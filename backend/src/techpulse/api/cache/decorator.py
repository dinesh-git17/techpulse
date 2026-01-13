"""Cache-aside decorator with SETNX locking for stampede prevention.

This module provides the @cached decorator for wrapping async methods with
cache-aside logic. The decorator implements stampede prevention using Redis
SETNX-based distributed locking to ensure only one request populates the
cache on a cold miss.
"""

import asyncio
import functools
import inspect
import time
from collections.abc import Awaitable, Callable
from typing import TypeVar, cast

import redis
import structlog
from pydantic import BaseModel

from techpulse.api.cache.keys import CacheKeyBuilder
from techpulse.api.cache.serializer import CacheSerializationError, CacheSerializer
from techpulse.api.cache.service import CacheService, get_cache_service

logger = structlog.get_logger(__name__)

T = TypeVar("T")

DEFAULT_LOCK_TIMEOUT_SECONDS = 30
DEFAULT_LOCK_RETRY_DELAY_SECONDS = 0.05
DEFAULT_LOCK_MAX_WAIT_SECONDS = 10.0


class CacheLockAcquisitionError(Exception):
    """Raised when cache lock cannot be acquired within timeout.

    This exception is typically caught internally and results in a direct
    database query (fail-open behavior).

    Attributes:
        key: The cache key for which lock acquisition failed.
        wait_time: Total time spent waiting for the lock.
    """

    def __init__(self, key: str, wait_time: float) -> None:
        """Initialize the lock acquisition error.

        Args:
            key: The cache key that could not be locked.
            wait_time: Time in seconds spent waiting for the lock.
        """
        self.key = key
        self.wait_time = wait_time
        super().__init__(
            f"Failed to acquire cache lock for '{key}' after {wait_time:.2f}s"
        )


def cached(
    endpoint: str,
    key_params: list[str],
    ttl: int | None = None,
    lock_timeout: int = DEFAULT_LOCK_TIMEOUT_SECONDS,
) -> Callable[[Callable[..., T]], Callable[..., Awaitable[T]]]:
    """Decorator for cache-aside pattern with stampede prevention.

    Wraps an async method with cache lookup and SETNX-based locking.
    On cache hit, returns cached data immediately. On cache miss,
    acquires a distributed lock before executing the wrapped function
    to prevent multiple concurrent requests from hitting the database.

    The decorator implements fail-open behavior: if Redis is unavailable
    or any cache operation fails, the wrapped function executes directly.

    Args:
        endpoint: The endpoint name for cache key generation (e.g., "trends").
        key_params: List of parameter names to include in the cache key.
            These must match the parameter names of the decorated function.
        ttl: Optional TTL override in seconds. Uses service default if None.
        lock_timeout: Lock expiry time in seconds for stampede prevention.

    Returns:
        A decorator function that wraps async methods with caching logic.

    Example:
        >>> @cached(endpoint="trends", key_params=["tech_keys", "start_date"])
        ... async def get_trends(tech_keys: list[str], start_date: date) -> list:
        ...     return await fetch_from_database(tech_keys, start_date)
    """

    def decorator(func: Callable[..., T]) -> Callable[..., Awaitable[T]]:
        @functools.wraps(func)
        async def wrapper(*args: object, **kwargs: object) -> T:
            cache_context = _CacheContext(
                endpoint=endpoint,
                key_params=key_params,
                ttl=ttl,
                lock_timeout=lock_timeout,
                func=func,
            )
            return await cache_context.execute(*args, **kwargs)

        return wrapper

    return decorator


class _CacheContext:
    """Internal context manager for cache operations.

    Encapsulates all cache-related state and operations for a single
    decorated function call. Handles key generation, cache lookup,
    lock acquisition, and result caching.
    """

    def __init__(
        self,
        endpoint: str,
        key_params: list[str],
        ttl: int | None,
        lock_timeout: int,
        func: Callable[..., T],
    ) -> None:
        """Initialize the cache context.

        Args:
            endpoint: The endpoint name for cache key generation.
            key_params: Parameter names to include in the cache key.
            ttl: TTL override in seconds, or None for service default.
            lock_timeout: Lock expiry time in seconds.
            func: The wrapped function to execute on cache miss.
        """
        self.endpoint = endpoint
        self.key_params = key_params
        self.ttl = ttl
        self.lock_timeout = lock_timeout
        self.func = func
        self.key_builder = CacheKeyBuilder()
        self.serializer = CacheSerializer()
        self._log = logger.bind(
            component="CacheDecorator",
            endpoint=endpoint,
        )

    async def execute(self, *args: object, **kwargs: object) -> T:
        """Execute the cached operation with stampede prevention.

        Attempts to retrieve from cache first. On miss, acquires a
        distributed lock before executing the wrapped function and
        caching the result.

        Args:
            *args: Positional arguments passed to the wrapped function.
            **kwargs: Keyword arguments passed to the wrapped function.

        Returns:
            The result from cache or from executing the wrapped function.
        """
        cache_service = get_cache_service()

        if cache_service is None or not cache_service.is_connected():
            self._log.debug("cache_bypassed", reason="not_connected")
            return await self._execute_function(*args, **kwargs)

        cache_key = self._build_cache_key(*args, **kwargs)
        log_context = self._log.bind(cache_key=cache_key)

        cached_value = await self._get_cached_value(cache_service, cache_key)
        if cached_value is not None:
            log_context.info("cache_hit", cache_hit=True)
            return cast(T, cached_value)

        log_context.info("cache_miss", cache_hit=False)

        return await self._execute_with_lock(
            cache_service, cache_key, log_context, *args, **kwargs
        )

    def _build_cache_key(self, *args: object, **kwargs: object) -> str:
        """Build a cache key from function arguments.

        Extracts the specified key parameters from the function's
        arguments and generates a deterministic cache key.

        Args:
            *args: Positional arguments passed to the wrapped function.
            **kwargs: Keyword arguments passed to the wrapped function.

        Returns:
            A deterministic cache key string.
        """
        sig = inspect.signature(self.func)
        bound_args = sig.bind(*args, **kwargs)
        bound_args.apply_defaults()

        key_values: dict[str, str | int | list[str] | None] = {}
        for param_name in self.key_params:
            if param_name in bound_args.arguments:
                value = bound_args.arguments[param_name]
                if hasattr(value, "isoformat"):
                    key_values[param_name] = value.isoformat()
                elif isinstance(value, list):
                    key_values[param_name] = cast(list[str], value)
                elif value is None:
                    key_values[param_name] = None
                else:
                    key_values[param_name] = str(value)

        return self.key_builder.build(self.endpoint, **key_values)

    async def _get_cached_value(
        self,
        cache_service: CacheService,
        cache_key: str,
    ) -> dict[str, object] | list[object] | None:
        """Retrieve and deserialize a cached value.

        Args:
            cache_service: The active cache service.
            cache_key: The cache key to retrieve.

        Returns:
            The deserialized cached value, or None if not found or on error.
        """
        try:
            cached_bytes = await asyncio.to_thread(cache_service.get, cache_key)
            if cached_bytes is None:
                return None
            return self.serializer.deserialize(cached_bytes)
        except CacheSerializationError as error:
            self._log.warning(
                "cache_deserialize_error",
                cache_key=cache_key,
                error=str(error),
            )
            return None

    async def _execute_with_lock(
        self,
        cache_service: CacheService,
        cache_key: str,
        log_context: structlog.typing.FilteringBoundLogger,
        *args: object,
        **kwargs: object,
    ) -> T:
        """Execute function with distributed lock for stampede prevention.

        Acquires a SETNX lock before executing the function. If the lock
        is already held, waits with exponential backoff and checks the
        cache again (another request may have populated it).

        Args:
            cache_service: The active cache service.
            cache_key: The cache key for both data and lock.
            log_context: Logger with bound context.
            *args: Positional arguments for the wrapped function.
            **kwargs: Keyword arguments for the wrapped function.

        Returns:
            The result from the wrapped function.
        """
        lock_key = f"{cache_key}:lock"

        try:
            acquired = await self._acquire_lock(cache_service, lock_key, log_context)

            if acquired:
                log_context.debug("lock_acquired", lock_key=lock_key)
                try:
                    cached_value = await self._get_cached_value(
                        cache_service, cache_key
                    )
                    if cached_value is not None:
                        log_context.info(
                            "cache_hit_after_lock", cache_hit=True, after_lock=True
                        )
                        return cast(T, cached_value)

                    computed_result: T = await self._execute_function(*args, **kwargs)
                    await self._cache_result(
                        cache_service, cache_key, computed_result, log_context
                    )
                    return computed_result
                finally:
                    await self._release_lock(cache_service, lock_key, log_context)
            else:
                cached_value = await self._get_cached_value(cache_service, cache_key)
                if cached_value is not None:
                    log_context.info(
                        "lock_bypass", reason="cache_populated_during_wait"
                    )
                    return cast(T, cached_value)
                log_context.info("lock_bypass", reason="direct_execution")
                return await self._execute_function(*args, **kwargs)

        except CacheLockAcquisitionError:
            log_context.warning("lock_timeout", lock_key=lock_key)
            return await self._execute_function(*args, **kwargs)

    async def _acquire_lock(
        self,
        cache_service: CacheService,
        lock_key: str,
        log_context: structlog.typing.FilteringBoundLogger,
    ) -> bool:
        """Attempt to acquire a distributed lock with retry.

        Uses Redis SETNX with expiry for lock acquisition. If the lock
        is held by another process, waits with exponential backoff and
        periodically checks if the original cache key has been populated.

        Args:
            cache_service: The active cache service.
            lock_key: The lock key to acquire.
            log_context: Logger with bound context.

        Returns:
            True if lock was acquired, False if should bypass locking.

        Raises:
            CacheLockAcquisitionError: If lock cannot be acquired within timeout.
        """
        client: redis.Redis | None = getattr(cache_service, "_client", None)
        if client is None:
            return False

        start_time = time.monotonic()
        retry_delay = DEFAULT_LOCK_RETRY_DELAY_SECONDS
        wait_count = 0

        while True:
            elapsed = time.monotonic() - start_time
            if elapsed >= DEFAULT_LOCK_MAX_WAIT_SECONDS:
                raise CacheLockAcquisitionError(lock_key, elapsed)

            try:
                acquired = await asyncio.to_thread(
                    client.set,
                    lock_key,
                    b"1",
                    nx=True,
                    ex=self.lock_timeout,
                )
                if acquired:
                    return True

                wait_count += 1
                log_context.debug(
                    "lock_wait",
                    lock_key=lock_key,
                    wait_count=wait_count,
                    retry_delay=retry_delay,
                )

                await asyncio.sleep(retry_delay)

                data_key = lock_key.replace(":lock", "")
                cached_bytes = await asyncio.to_thread(client.get, data_key)
                if cached_bytes is not None:
                    return False

                retry_delay = min(retry_delay * 2, 0.5)

            except redis.RedisError as error:
                log_context.warning(
                    "lock_acquire_error",
                    lock_key=lock_key,
                    error=str(error),
                )
                return False

    async def _release_lock(
        self,
        cache_service: CacheService,
        lock_key: str,
        log_context: structlog.typing.FilteringBoundLogger,
    ) -> None:
        """Release a distributed lock.

        Args:
            cache_service: The active cache service.
            lock_key: The lock key to release.
            log_context: Logger with bound context.
        """
        client: redis.Redis | None = getattr(cache_service, "_client", None)
        if client is None:
            return

        try:
            await asyncio.to_thread(client.delete, lock_key)
            log_context.debug("lock_released", lock_key=lock_key)
        except redis.RedisError as error:
            log_context.warning(
                "lock_release_error",
                lock_key=lock_key,
                error=str(error),
            )

    async def _cache_result(
        self,
        cache_service: CacheService,
        cache_key: str,
        result: T,
        log_context: structlog.typing.FilteringBoundLogger,
    ) -> None:
        """Serialize and cache the function result.

        Args:
            cache_service: The active cache service.
            cache_key: The cache key to store under.
            result: The function result to cache.
            log_context: Logger with bound context.
        """
        try:
            if isinstance(result, BaseModel):
                serialized = self.serializer.serialize(result)
            elif isinstance(result, (dict, list)):
                serialized = self.serializer.serialize(
                    cast(dict[str, object] | list[object], result)
                )
            else:
                log_context.warning(
                    "cache_serialize_skip",
                    cache_key=cache_key,
                    reason="unsupported_type",
                    result_type=type(result).__name__,
                )
                return

            success = await asyncio.to_thread(
                cache_service.set,
                cache_key,
                serialized,
                self.ttl,
            )
            if success:
                log_context.info("cache_write", cache_key=cache_key)
            else:
                log_context.warning("cache_write_failed", cache_key=cache_key)
        except CacheSerializationError as error:
            log_context.warning(
                "cache_serialize_error",
                cache_key=cache_key,
                error=str(error),
            )

    async def _execute_function(self, *args: object, **kwargs: object) -> T:
        """Execute the wrapped function.

        Handles both async and sync functions by checking if the result
        is a coroutine.

        Args:
            *args: Positional arguments for the function.
            **kwargs: Keyword arguments for the function.

        Returns:
            The function result.
        """
        result = self.func(*args, **kwargs)
        if asyncio.iscoroutine(result):
            return cast(T, await result)
        return cast(T, result)
