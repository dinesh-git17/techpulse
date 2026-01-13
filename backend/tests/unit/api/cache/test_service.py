"""Unit tests for CacheService class."""

from typing import Generator
from unittest.mock import MagicMock, patch

import pytest
import redis

from techpulse.api.cache.service import (
    CacheService,
    close_cache_service,
    get_cache_service,
    init_cache_service,
)
from techpulse.api.exceptions.domain import CacheConnectionError


@pytest.fixture
def mock_redis_client() -> Generator[MagicMock, None, None]:
    """Create a mock Redis client for testing."""
    mock_client = MagicMock(spec=redis.Redis)
    mock_client.ping.return_value = True
    mock_client.get.return_value = None
    mock_client.set.return_value = True
    mock_client.delete.return_value = 1
    mock_client.scan.return_value = (0, [])
    yield mock_client


@pytest.fixture
def cache_service() -> CacheService:
    """Create a CacheService instance for testing."""
    return CacheService("redis://localhost:6379", default_ttl=3600)


class TestCacheServiceInit:
    """Test suite for CacheService initialization."""

    def test_init_stores_redis_url(self) -> None:
        """Verify redis_url is stored during initialization."""
        service = CacheService("redis://localhost:6379")
        assert service.redis_url == "redis://localhost:6379"

    def test_init_stores_default_ttl(self) -> None:
        """Verify default_ttl is stored during initialization."""
        service = CacheService("redis://localhost:6379", default_ttl=7200)
        assert service.default_ttl == 7200

    def test_init_uses_default_ttl(self) -> None:
        """Verify default TTL of 86400 is used when not specified."""
        service = CacheService("redis://localhost:6379")
        assert service.default_ttl == 86400

    def test_init_not_connected(self) -> None:
        """Verify service is not connected after initialization."""
        service = CacheService("redis://localhost:6379")
        assert not service.is_connected()


class TestCacheServiceConnect:
    """Test suite for CacheService.connect method."""

    def test_connect_success(
        self, cache_service: CacheService, mock_redis_client: MagicMock
    ) -> None:
        """Verify successful connection to Redis."""
        with patch("techpulse.api.cache.service.redis.from_url") as mock_from_url:
            mock_from_url.return_value = mock_redis_client
            cache_service.connect()

            assert cache_service.is_connected()
            mock_redis_client.ping.assert_called_once()

    def test_connect_failure_raises_exception(
        self, cache_service: CacheService
    ) -> None:
        """Verify connection failure raises CacheConnectionError."""
        with patch("techpulse.api.cache.service.redis.from_url") as mock_from_url:
            mock_from_url.side_effect = redis.ConnectionError("Connection refused")

            with pytest.raises(CacheConnectionError) as exc_info:
                cache_service.connect()

            assert "Connection refused" in exc_info.value.reason
            assert exc_info.value.operation == "connect"
            assert not cache_service.is_connected()

    def test_connect_already_connected_logs_warning(
        self, cache_service: CacheService, mock_redis_client: MagicMock
    ) -> None:
        """Verify warning is logged when already connected."""
        with patch("techpulse.api.cache.service.redis.from_url") as mock_from_url:
            mock_from_url.return_value = mock_redis_client
            cache_service.connect()
            cache_service.connect()
            assert mock_from_url.call_count == 1

    def test_connect_ping_failure_raises_exception(
        self, cache_service: CacheService, mock_redis_client: MagicMock
    ) -> None:
        """Verify ping failure raises CacheConnectionError."""
        mock_redis_client.ping.side_effect = redis.ConnectionError("PING failed")

        with patch("techpulse.api.cache.service.redis.from_url") as mock_from_url:
            mock_from_url.return_value = mock_redis_client

            with pytest.raises(CacheConnectionError):
                cache_service.connect()

            assert not cache_service.is_connected()


class TestCacheServiceClose:
    """Test suite for CacheService.close method."""

    def test_close_connected_client(
        self, cache_service: CacheService, mock_redis_client: MagicMock
    ) -> None:
        """Verify close disconnects the client."""
        with patch("techpulse.api.cache.service.redis.from_url") as mock_from_url:
            mock_from_url.return_value = mock_redis_client
            cache_service.connect()
            cache_service.close()

            assert not cache_service.is_connected()
            mock_redis_client.close.assert_called_once()

    def test_close_not_connected_is_safe(self, cache_service: CacheService) -> None:
        """Verify close is safe when not connected."""
        cache_service.close()
        assert not cache_service.is_connected()

    def test_close_error_is_handled(
        self, cache_service: CacheService, mock_redis_client: MagicMock
    ) -> None:
        """Verify close error does not raise exception."""
        mock_redis_client.close.side_effect = redis.ConnectionError("Close failed")

        with patch("techpulse.api.cache.service.redis.from_url") as mock_from_url:
            mock_from_url.return_value = mock_redis_client
            cache_service.connect()
            cache_service.close()

            assert not cache_service.is_connected()


class TestCacheServiceGet:
    """Test suite for CacheService.get method."""

    def test_get_returns_value(
        self, cache_service: CacheService, mock_redis_client: MagicMock
    ) -> None:
        """Verify get returns cached value."""
        mock_redis_client.get.return_value = b"cached_value"

        with patch("techpulse.api.cache.service.redis.from_url") as mock_from_url:
            mock_from_url.return_value = mock_redis_client
            cache_service.connect()
            result = cache_service.get("test_key")

            assert result == b"cached_value"
            mock_redis_client.get.assert_called_once_with("test_key")

    def test_get_returns_none_on_miss(
        self, cache_service: CacheService, mock_redis_client: MagicMock
    ) -> None:
        """Verify get returns None for cache miss."""
        mock_redis_client.get.return_value = None

        with patch("techpulse.api.cache.service.redis.from_url") as mock_from_url:
            mock_from_url.return_value = mock_redis_client
            cache_service.connect()
            result = cache_service.get("nonexistent_key")

            assert result is None

    def test_get_returns_none_when_not_connected(
        self, cache_service: CacheService
    ) -> None:
        """Verify get returns None when not connected (fail-open)."""
        result = cache_service.get("test_key")
        assert result is None

    def test_get_returns_none_on_error(
        self, cache_service: CacheService, mock_redis_client: MagicMock
    ) -> None:
        """Verify get returns None on Redis error (fail-open)."""
        mock_redis_client.get.side_effect = redis.ConnectionError("Get failed")

        with patch("techpulse.api.cache.service.redis.from_url") as mock_from_url:
            mock_from_url.return_value = mock_redis_client
            cache_service.connect()
            result = cache_service.get("test_key")

            assert result is None


class TestCacheServiceSet:
    """Test suite for CacheService.set method."""

    def test_set_stores_value(
        self, cache_service: CacheService, mock_redis_client: MagicMock
    ) -> None:
        """Verify set stores value with TTL."""
        with patch("techpulse.api.cache.service.redis.from_url") as mock_from_url:
            mock_from_url.return_value = mock_redis_client
            cache_service.connect()
            result = cache_service.set("test_key", b"test_value")

            assert result is True
            mock_redis_client.set.assert_called_once_with(
                "test_key", b"test_value", ex=3600
            )

    def test_set_uses_custom_ttl(
        self, cache_service: CacheService, mock_redis_client: MagicMock
    ) -> None:
        """Verify set uses custom TTL when provided."""
        with patch("techpulse.api.cache.service.redis.from_url") as mock_from_url:
            mock_from_url.return_value = mock_redis_client
            cache_service.connect()
            cache_service.set("test_key", b"test_value", ttl=7200)

            mock_redis_client.set.assert_called_once_with(
                "test_key", b"test_value", ex=7200
            )

    def test_set_returns_false_when_not_connected(
        self, cache_service: CacheService
    ) -> None:
        """Verify set returns False when not connected (fail-open)."""
        result = cache_service.set("test_key", b"test_value")
        assert result is False

    def test_set_returns_false_on_error(
        self, cache_service: CacheService, mock_redis_client: MagicMock
    ) -> None:
        """Verify set returns False on Redis error (fail-open)."""
        mock_redis_client.set.side_effect = redis.ConnectionError("Set failed")

        with patch("techpulse.api.cache.service.redis.from_url") as mock_from_url:
            mock_from_url.return_value = mock_redis_client
            cache_service.connect()
            result = cache_service.set("test_key", b"test_value")

            assert result is False


class TestCacheServiceDelete:
    """Test suite for CacheService.delete method."""

    def test_delete_removes_key(
        self, cache_service: CacheService, mock_redis_client: MagicMock
    ) -> None:
        """Verify delete removes key from cache."""
        with patch("techpulse.api.cache.service.redis.from_url") as mock_from_url:
            mock_from_url.return_value = mock_redis_client
            cache_service.connect()
            result = cache_service.delete("test_key")

            assert result is True
            mock_redis_client.delete.assert_called_once_with("test_key")

    def test_delete_returns_false_when_not_connected(
        self, cache_service: CacheService
    ) -> None:
        """Verify delete returns False when not connected (fail-open)."""
        result = cache_service.delete("test_key")
        assert result is False

    def test_delete_returns_false_on_error(
        self, cache_service: CacheService, mock_redis_client: MagicMock
    ) -> None:
        """Verify delete returns False on Redis error (fail-open)."""
        mock_redis_client.delete.side_effect = redis.ConnectionError("Delete failed")

        with patch("techpulse.api.cache.service.redis.from_url") as mock_from_url:
            mock_from_url.return_value = mock_redis_client
            cache_service.connect()
            result = cache_service.delete("test_key")

            assert result is False


class TestCacheServiceDeletePattern:
    """Test suite for CacheService.delete_pattern method."""

    def test_delete_pattern_removes_matching_keys(
        self, cache_service: CacheService, mock_redis_client: MagicMock
    ) -> None:
        """Verify delete_pattern removes all matching keys."""
        mock_redis_client.scan.return_value = (0, [b"tp:v1:key1", b"tp:v1:key2"])

        with patch("techpulse.api.cache.service.redis.from_url") as mock_from_url:
            mock_from_url.return_value = mock_redis_client
            cache_service.connect()
            result = cache_service.delete_pattern("tp:v1:*")

            assert result == 2
            mock_redis_client.delete.assert_called_once_with(
                b"tp:v1:key1", b"tp:v1:key2"
            )

    def test_delete_pattern_handles_pagination(
        self, cache_service: CacheService, mock_redis_client: MagicMock
    ) -> None:
        """Verify delete_pattern handles cursor-based pagination."""
        mock_redis_client.scan.side_effect = [
            (1, [b"key1"]),
            (0, [b"key2"]),
        ]

        with patch("techpulse.api.cache.service.redis.from_url") as mock_from_url:
            mock_from_url.return_value = mock_redis_client
            cache_service.connect()
            result = cache_service.delete_pattern("key*")

            assert result == 2
            assert mock_redis_client.scan.call_count == 2

    def test_delete_pattern_returns_zero_when_not_connected(
        self, cache_service: CacheService
    ) -> None:
        """Verify delete_pattern returns 0 when not connected (fail-open)."""
        result = cache_service.delete_pattern("tp:v1:*")
        assert result == 0

    def test_delete_pattern_returns_zero_on_error(
        self, cache_service: CacheService, mock_redis_client: MagicMock
    ) -> None:
        """Verify delete_pattern returns 0 on Redis error (fail-open)."""
        mock_redis_client.scan.side_effect = redis.ConnectionError("Scan failed")

        with patch("techpulse.api.cache.service.redis.from_url") as mock_from_url:
            mock_from_url.return_value = mock_redis_client
            cache_service.connect()
            result = cache_service.delete_pattern("tp:v1:*")

            assert result == 0


class TestCacheServiceHealthCheck:
    """Test suite for CacheService.health_check method."""

    def test_health_check_returns_true_when_healthy(
        self, cache_service: CacheService, mock_redis_client: MagicMock
    ) -> None:
        """Verify health_check returns True when Redis responds."""
        with patch("techpulse.api.cache.service.redis.from_url") as mock_from_url:
            mock_from_url.return_value = mock_redis_client
            cache_service.connect()
            result = cache_service.health_check()

            assert result is True

    def test_health_check_returns_false_when_not_connected(
        self, cache_service: CacheService
    ) -> None:
        """Verify health_check returns False when not connected."""
        result = cache_service.health_check()
        assert result is False

    def test_health_check_returns_false_on_ping_failure(
        self, cache_service: CacheService, mock_redis_client: MagicMock
    ) -> None:
        """Verify health_check returns False when ping fails."""
        with patch("techpulse.api.cache.service.redis.from_url") as mock_from_url:
            mock_from_url.return_value = mock_redis_client
            cache_service.connect()

            mock_redis_client.ping.side_effect = redis.ConnectionError("Ping failed")
            result = cache_service.health_check()

            assert result is False


class TestCacheServiceMaskUrl:
    """Test suite for CacheService._mask_url method."""

    def test_mask_url_with_credentials(self, cache_service: CacheService) -> None:
        """Verify URL with credentials is masked."""
        url = "redis://user:password@localhost:6379"  # pragma: allowlist secret
        result = cache_service._mask_url(url)
        assert result == "redis://***:***@localhost:6379"

    def test_mask_url_without_credentials(self, cache_service: CacheService) -> None:
        """Verify URL without credentials is not modified."""
        url = "redis://localhost:6379"
        result = cache_service._mask_url(url)
        assert result == "redis://localhost:6379"


class TestGlobalCacheServiceFunctions:
    """Test suite for global cache service functions."""

    def test_init_cache_service_with_valid_url(
        self, mock_redis_client: MagicMock
    ) -> None:
        """Verify init_cache_service creates and connects service."""
        with patch("techpulse.api.cache.service.redis.from_url") as mock_from_url:
            mock_from_url.return_value = mock_redis_client
            service = init_cache_service("redis://localhost:6379", default_ttl=3600)

            assert service is not None
            assert service.is_connected()

            close_cache_service()

    def test_init_cache_service_with_none_url(self) -> None:
        """Verify init_cache_service returns None when URL is None."""
        service = init_cache_service(None)
        assert service is None
        assert get_cache_service() is None

    def test_init_cache_service_connection_failure(self) -> None:
        """Verify init_cache_service returns None on connection failure."""
        with patch("techpulse.api.cache.service.redis.from_url") as mock_from_url:
            mock_from_url.side_effect = redis.ConnectionError("Connection refused")
            service = init_cache_service("redis://localhost:6379")

            assert service is None
            assert get_cache_service() is None

    def test_get_cache_service_returns_initialized_service(
        self, mock_redis_client: MagicMock
    ) -> None:
        """Verify get_cache_service returns the initialized service."""
        with patch("techpulse.api.cache.service.redis.from_url") as mock_from_url:
            mock_from_url.return_value = mock_redis_client
            init_cache_service("redis://localhost:6379")
            service = get_cache_service()

            assert service is not None
            assert service.is_connected()

            close_cache_service()

    def test_close_cache_service_clears_global(
        self, mock_redis_client: MagicMock
    ) -> None:
        """Verify close_cache_service clears the global service."""
        with patch("techpulse.api.cache.service.redis.from_url") as mock_from_url:
            mock_from_url.return_value = mock_redis_client
            init_cache_service("redis://localhost:6379")
            close_cache_service()

            assert get_cache_service() is None

    def test_close_cache_service_when_not_initialized(self) -> None:
        """Verify close_cache_service is safe when not initialized."""
        close_cache_service()
        assert get_cache_service() is None
