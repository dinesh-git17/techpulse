"""Redis cache service with fail-open behavior.

This module provides CacheService for Redis-based caching operations.
All cache operations implement fail-open behavior: failures are logged
but do not propagate exceptions to callers, ensuring API availability
is never impacted by cache outages.
"""

from typing import Optional

import redis
import structlog

from techpulse.api.exceptions.domain import CacheConnectionError

logger = structlog.get_logger(__name__)


class CacheService:
    """Manage Redis cache connections and operations with fail-open behavior.

    This class handles the lifecycle of a Redis connection and provides
    get, set, and delete operations. All operations implement fail-open
    behavior: cache failures are logged but do not raise exceptions,
    allowing the application to continue operating without cache.

    The service is designed for use with Upstash Redis but is compatible
    with any Redis-protocol server.

    Attributes:
        redis_url: The Redis connection URL.
        default_ttl: Default time-to-live for cache entries in seconds.

    Example:
        >>> service = CacheService("redis://localhost:6379", default_ttl=3600)
        >>> service.connect()
        >>> service.set("key", b"value")
        >>> data = service.get("key")
        >>> service.close()
    """

    def __init__(self, redis_url: str, default_ttl: int = 86400) -> None:
        """Initialize the cache service with connection URL and default TTL.

        Args:
            redis_url: Redis connection URL (e.g., redis://host:port or rediss://...).
            default_ttl: Default TTL for cache entries in seconds.
        """
        self.redis_url = redis_url
        self.default_ttl = default_ttl
        self._client: Optional[redis.Redis] = None
        self._connected = False
        self._log = logger.bind(
            component="CacheService",
        )

    def connect(self) -> None:
        """Establish connection to Redis server.

        Creates a Redis client and verifies connectivity with a PING.
        If connection fails, logs the error but does not raise an exception
        to implement fail-open behavior.

        Raises:
            CacheConnectionError: If connection fails (logged, not propagated
                in production use - callers should check is_connected()).
        """
        if self._client is not None:
            self._log.warning("cache_connection_already_open")
            return

        try:
            self._client = redis.from_url(  # type: ignore[no-untyped-call]
                self.redis_url,
                decode_responses=False,
                socket_connect_timeout=5.0,
                socket_timeout=5.0,
            )
            self._client.ping()
            self._connected = True
            self._log.info("cache_connection_established")
        except redis.RedisError as error:
            self._connected = False
            self._client = None
            self._log.error(
                "cache_connection_failed",
                error=str(error),
                redis_url=self._mask_url(self.redis_url),
            )
            raise CacheConnectionError(
                reason=str(error),
                operation="connect",
            ) from error

    def close(self) -> None:
        """Close the Redis connection.

        Safely closes the connection if one is open. This method is
        idempotent and can be called multiple times without error.
        """
        if self._client is not None:
            try:
                self._client.close()
            except redis.RedisError as error:
                self._log.warning("cache_close_error", error=str(error))
            finally:
                self._client = None
                self._connected = False
                self._log.info("cache_connection_closed")

    def is_connected(self) -> bool:
        """Check if the cache service has an active connection.

        Returns:
            True if connected to Redis, False otherwise.
        """
        return self._connected and self._client is not None

    def health_check(self) -> bool:
        """Verify Redis connectivity with a PING command.

        Returns:
            True if Redis responds to PING, False otherwise.
        """
        if self._client is None:
            return False
        try:
            self._client.ping()
            return True
        except redis.RedisError:
            return False

    def get(self, key: str) -> Optional[bytes]:
        """Retrieve a value from the cache.

        Implements fail-open behavior: returns None on any error.

        Args:
            key: The cache key to retrieve.

        Returns:
            The cached value as bytes, or None if not found or on error.
        """
        if not self.is_connected():
            self._log.debug("cache_get_skipped", key=key, reason="not_connected")
            return None

        try:
            value: Optional[bytes] = self._client.get(key)  # type: ignore[union-attr,assignment]
            if value is not None:
                self._log.debug("cache_hit", key=key)
            else:
                self._log.debug("cache_miss", key=key)
            return value
        except redis.RedisError as error:
            self._log.error(
                "cache_get_error",
                key=key,
                error=str(error),
            )
            return None

    def set(
        self,
        key: str,
        value: bytes,
        ttl: Optional[int] = None,
    ) -> bool:
        """Store a value in the cache.

        Implements fail-open behavior: returns False on any error.

        Args:
            key: The cache key to store.
            value: The value to cache (must be bytes).
            ttl: Time-to-live in seconds. Uses default_ttl if not specified.

        Returns:
            True if the value was stored successfully, False otherwise.
        """
        if not self.is_connected():
            self._log.debug("cache_set_skipped", key=key, reason="not_connected")
            return False

        effective_ttl = ttl if ttl is not None else self.default_ttl

        try:
            self._client.set(key, value, ex=effective_ttl)  # type: ignore[union-attr]
            self._log.debug("cache_set", key=key, ttl_seconds=effective_ttl)
            return True
        except redis.RedisError as error:
            self._log.error(
                "cache_set_error",
                key=key,
                error=str(error),
            )
            return False

    def delete(self, key: str) -> bool:
        """Delete a value from the cache.

        Implements fail-open behavior: returns False on any error.

        Args:
            key: The cache key to delete.

        Returns:
            True if the key was deleted (or didn't exist), False on error.
        """
        if not self.is_connected():
            self._log.debug("cache_delete_skipped", key=key, reason="not_connected")
            return False

        try:
            self._client.delete(key)  # type: ignore[union-attr]
            self._log.debug("cache_delete", key=key)
            return True
        except redis.RedisError as error:
            self._log.error(
                "cache_delete_error",
                key=key,
                error=str(error),
            )
            return False

    def delete_pattern(self, pattern: str) -> int:
        """Delete all keys matching a pattern.

        Uses SCAN to find matching keys and deletes them in batches.
        Implements fail-open behavior: returns 0 on any error.

        Args:
            pattern: The glob-style pattern to match (e.g., "tp:v1:*").

        Returns:
            The number of keys deleted, or 0 on error.
        """
        if not self.is_connected():
            self._log.debug(
                "cache_delete_pattern_skipped",
                pattern=pattern,
                reason="not_connected",
            )
            return 0

        try:
            deleted_count = 0
            cursor: int = 0
            while True:
                scan_result: tuple[int, list[bytes]] = self._client.scan(  # type: ignore[union-attr,assignment]
                    cursor=cursor,
                    match=pattern,
                    count=100,
                )
                cursor, keys = scan_result
                if keys:
                    self._client.delete(*keys)  # type: ignore[union-attr]
                    deleted_count += len(keys)
                if cursor == 0:
                    break

            self._log.info(
                "cache_delete_pattern",
                pattern=pattern,
                deleted_count=deleted_count,
            )
            return deleted_count
        except redis.RedisError as error:
            self._log.error(
                "cache_delete_pattern_error",
                pattern=pattern,
                error=str(error),
            )
            return 0

    def _mask_url(self, url: str) -> str:
        """Mask sensitive parts of Redis URL for logging.

        Args:
            url: The Redis URL to mask.

        Returns:
            URL with password masked if present.
        """
        if "@" in url:
            protocol_end = url.find("://") + 3
            at_pos = url.find("@")
            return url[:protocol_end] + "***:***" + url[at_pos:]
        return url


_cache_service: Optional[CacheService] = None


def init_cache_service(
    redis_url: Optional[str],
    default_ttl: int = 86400,
) -> Optional[CacheService]:
    """Initialize the global cache service.

    Creates and connects a CacheService instance. If redis_url is None,
    caching is disabled and None is returned. Connection failures are
    logged but do not prevent application startup (fail-open behavior).

    Args:
        redis_url: Redis connection URL, or None to disable caching.
        default_ttl: Default TTL for cache entries in seconds.

    Returns:
        The initialized CacheService, or None if caching is disabled
        or connection failed.
    """
    global _cache_service

    if redis_url is None:
        logger.info("cache_disabled", reason="redis_url_not_configured")
        _cache_service = None
        return None

    service = CacheService(redis_url, default_ttl)
    try:
        service.connect()
        _cache_service = service
        return service
    except CacheConnectionError:
        _cache_service = None
        return None


def close_cache_service() -> None:
    """Close and clear the global cache service.

    Safely closes the Redis connection and clears the global reference.
    This should be called during application shutdown.
    """
    global _cache_service
    if _cache_service is not None:
        _cache_service.close()
        _cache_service = None


def get_cache_service() -> Optional[CacheService]:
    """Retrieve the global cache service instance.

    Returns:
        The active CacheService, or None if caching is not configured
        or initialization failed.
    """
    return _cache_service
