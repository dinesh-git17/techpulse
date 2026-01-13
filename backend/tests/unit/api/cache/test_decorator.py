"""Unit tests for cache decorator with SETNX locking."""

from typing import Generator
from unittest.mock import MagicMock, patch

import pytest
import redis

from techpulse.api.cache.decorator import (
    DEFAULT_LOCK_MAX_WAIT_SECONDS,
    DEFAULT_LOCK_TIMEOUT_SECONDS,
    CacheLockAcquisitionError,
    cached,
)


@pytest.fixture
def mock_redis_client() -> MagicMock:
    """Create a mock Redis client for testing."""
    mock_client = MagicMock(spec=redis.Redis)
    mock_client.get.return_value = None
    mock_client.set.return_value = True
    mock_client.delete.return_value = 1
    return mock_client


@pytest.fixture
def mock_cache_service(mock_redis_client: MagicMock) -> MagicMock:
    """Create a mock CacheService for testing."""
    mock_service = MagicMock()
    mock_service.is_connected.return_value = True
    mock_service.get.return_value = None
    mock_service.set.return_value = True
    mock_service._client = mock_redis_client
    mock_service.default_ttl = 86400
    return mock_service


@pytest.fixture
def mock_get_cache_service(
    mock_cache_service: MagicMock,
) -> Generator[MagicMock, None, None]:
    """Patch get_cache_service to return mock service."""
    with patch(
        "techpulse.api.cache.decorator.get_cache_service",
        return_value=mock_cache_service,
    ) as mock:
        yield mock


class TestCachedDecoratorBasic:
    """Test suite for basic @cached decorator functionality."""

    @pytest.mark.anyio
    async def test_cache_hit_returns_cached_value(
        self,
        mock_cache_service: MagicMock,
        mock_get_cache_service: MagicMock,
    ) -> None:
        """Verify cache hit returns cached value without calling function."""
        mock_cache_service.get.return_value = b'{"result": "cached"}'

        call_count = 0

        @cached(endpoint="test", key_params=["param"])
        async def test_func(param: str) -> dict[str, str]:
            nonlocal call_count
            call_count += 1
            return {"result": "fresh"}

        result = await test_func(param="value")

        assert result == {"result": "cached"}
        assert call_count == 0

    @pytest.mark.anyio
    async def test_cache_miss_calls_function(
        self,
        mock_cache_service: MagicMock,
        mock_get_cache_service: MagicMock,
        mock_redis_client: MagicMock,
    ) -> None:
        """Verify cache miss executes function and caches result."""
        mock_cache_service.get.return_value = None
        mock_redis_client.get.return_value = None

        call_count = 0

        @cached(endpoint="test", key_params=["param"])
        async def test_func(param: str) -> dict[str, str]:
            nonlocal call_count
            call_count += 1
            return {"result": "fresh"}

        result = await test_func(param="value")

        assert result == {"result": "fresh"}
        assert call_count == 1
        mock_cache_service.set.assert_called_once()

    @pytest.mark.anyio
    async def test_cache_bypassed_when_not_connected(
        self,
        mock_cache_service: MagicMock,
        mock_get_cache_service: MagicMock,
    ) -> None:
        """Verify cache is bypassed when service not connected."""
        mock_cache_service.is_connected.return_value = False

        call_count = 0

        @cached(endpoint="test", key_params=["param"])
        async def test_func(param: str) -> dict[str, str]:
            nonlocal call_count
            call_count += 1
            return {"result": "fresh"}

        result = await test_func(param="value")

        assert result == {"result": "fresh"}
        assert call_count == 1
        mock_cache_service.get.assert_not_called()

    @pytest.mark.anyio
    async def test_cache_bypassed_when_service_none(
        self,
        mock_get_cache_service: MagicMock,
    ) -> None:
        """Verify cache is bypassed when service is None."""
        mock_get_cache_service.return_value = None

        call_count = 0

        @cached(endpoint="test", key_params=["param"])
        async def test_func(param: str) -> dict[str, str]:
            nonlocal call_count
            call_count += 1
            return {"result": "fresh"}

        result = await test_func(param="value")

        assert result == {"result": "fresh"}
        assert call_count == 1


class TestCacheKeyGeneration:
    """Test suite for cache key generation from function arguments."""

    @pytest.mark.anyio
    async def test_key_generated_from_positional_args(
        self,
        mock_cache_service: MagicMock,
        mock_get_cache_service: MagicMock,
    ) -> None:
        """Verify cache key is generated from positional arguments."""
        mock_cache_service.get.return_value = b'{"data": "cached"}'

        @cached(endpoint="trends", key_params=["tech_ids", "start_date"])
        async def get_trends(
            tech_ids: list[str], start_date: str, end_date: str
        ) -> dict[str, str]:
            return {"data": "fresh"}

        await get_trends(["python", "react"], "2024-01-01", "2024-12-31")

        mock_cache_service.get.assert_called_once()
        call_key = mock_cache_service.get.call_args[0][0]
        assert "trends" in call_key

    @pytest.mark.anyio
    async def test_key_generated_from_keyword_args(
        self,
        mock_cache_service: MagicMock,
        mock_get_cache_service: MagicMock,
    ) -> None:
        """Verify cache key is generated from keyword arguments."""
        mock_cache_service.get.return_value = b'{"data": "cached"}'

        @cached(endpoint="trends", key_params=["tech_ids"])
        async def get_trends(tech_ids: list[str]) -> dict[str, str]:
            return {"data": "fresh"}

        await get_trends(tech_ids=["python"])

        mock_cache_service.get.assert_called_once()

    @pytest.mark.anyio
    async def test_date_objects_converted_to_isoformat(
        self,
        mock_cache_service: MagicMock,
        mock_get_cache_service: MagicMock,
    ) -> None:
        """Verify date objects are converted to ISO format for key generation."""
        from datetime import date

        mock_cache_service.get.return_value = b'{"data": "cached"}'

        @cached(endpoint="trends", key_params=["start_date"])
        async def get_trends(start_date: date) -> dict[str, str]:
            return {"data": "fresh"}

        await get_trends(start_date=date(2024, 1, 15))

        mock_cache_service.get.assert_called_once()


class TestLockAcquisition:
    """Test suite for SETNX lock acquisition behavior."""

    @pytest.mark.anyio
    async def test_lock_acquired_on_cache_miss(
        self,
        mock_cache_service: MagicMock,
        mock_get_cache_service: MagicMock,
        mock_redis_client: MagicMock,
    ) -> None:
        """Verify lock is acquired on cache miss."""
        mock_cache_service.get.return_value = None
        mock_redis_client.get.return_value = None
        mock_redis_client.set.return_value = True

        @cached(endpoint="test", key_params=["param"])
        async def test_func(param: str) -> dict[str, str]:
            return {"result": "fresh"}

        await test_func(param="value")

        set_calls = [
            call
            for call in mock_redis_client.set.call_args_list
            if call.kwargs.get("nx")
        ]
        assert len(set_calls) >= 1

    @pytest.mark.anyio
    async def test_lock_released_after_execution(
        self,
        mock_cache_service: MagicMock,
        mock_get_cache_service: MagicMock,
        mock_redis_client: MagicMock,
    ) -> None:
        """Verify lock is released after function execution."""
        mock_cache_service.get.return_value = None
        mock_redis_client.get.return_value = None
        mock_redis_client.set.return_value = True

        @cached(endpoint="test", key_params=["param"])
        async def test_func(param: str) -> dict[str, str]:
            return {"result": "fresh"}

        await test_func(param="value")

        mock_redis_client.delete.assert_called()
        delete_call = mock_redis_client.delete.call_args[0][0]
        assert ":lock" in delete_call

    @pytest.mark.anyio
    async def test_lock_released_on_function_exception(
        self,
        mock_cache_service: MagicMock,
        mock_get_cache_service: MagicMock,
        mock_redis_client: MagicMock,
    ) -> None:
        """Verify lock is released even when function raises exception."""
        mock_cache_service.get.return_value = None
        mock_redis_client.get.return_value = None
        mock_redis_client.set.return_value = True

        @cached(endpoint="test", key_params=["param"])
        async def test_func(param: str) -> dict[str, str]:
            raise ValueError("Test exception")

        with pytest.raises(ValueError, match="Test exception"):
            await test_func(param="value")

        mock_redis_client.delete.assert_called()

    @pytest.mark.anyio
    async def test_lock_has_expiry_timeout(
        self,
        mock_cache_service: MagicMock,
        mock_get_cache_service: MagicMock,
        mock_redis_client: MagicMock,
    ) -> None:
        """Verify lock is created with expiry timeout."""
        mock_cache_service.get.return_value = None
        mock_redis_client.get.return_value = None
        mock_redis_client.set.return_value = True

        @cached(endpoint="test", key_params=["param"], lock_timeout=60)
        async def test_func(param: str) -> dict[str, str]:
            return {"result": "fresh"}

        await test_func(param="value")

        set_calls = [
            call
            for call in mock_redis_client.set.call_args_list
            if call.kwargs.get("nx")
        ]
        assert len(set_calls) >= 1
        assert set_calls[0].kwargs.get("ex") == 60


class TestLockRetryBehavior:
    """Test suite for lock retry with exponential backoff."""

    @pytest.mark.anyio
    async def test_lock_retry_on_contention(
        self,
        mock_cache_service: MagicMock,
        mock_get_cache_service: MagicMock,
        mock_redis_client: MagicMock,
    ) -> None:
        """Verify lock acquisition retries on contention."""
        mock_cache_service.get.return_value = None
        mock_redis_client.set.side_effect = [False, False, True]
        mock_redis_client.get.return_value = None

        @cached(endpoint="test", key_params=["param"])
        async def test_func(param: str) -> dict[str, str]:
            return {"result": "fresh"}

        result = await test_func(param="value")

        assert result == {"result": "fresh"}
        assert mock_redis_client.set.call_count >= 3

    @pytest.mark.anyio
    async def test_lock_bypass_when_cache_populated_during_wait(
        self,
        mock_cache_service: MagicMock,
        mock_get_cache_service: MagicMock,
        mock_redis_client: MagicMock,
    ) -> None:
        """Verify lock wait exits when cache is populated by another request."""
        cache_service_get_calls = 0

        def cache_service_get_side_effect(key: str) -> bytes | None:
            nonlocal cache_service_get_calls
            cache_service_get_calls += 1
            if cache_service_get_calls <= 1:
                return None
            return b'{"result": "from_other_request"}'

        mock_cache_service.get.side_effect = cache_service_get_side_effect

        call_sequence = [False, False]
        redis_cache_values = [None, b'{"result": "from_other_request"}']

        def set_side_effect(*args: object, **kwargs: object) -> bool:
            if kwargs.get("nx"):
                return call_sequence.pop(0) if call_sequence else False
            return True

        def redis_get_side_effect(key: str) -> bytes | None:
            if ":lock" not in key:
                return redis_cache_values.pop(0) if redis_cache_values else None
            return None

        mock_redis_client.set.side_effect = set_side_effect
        mock_redis_client.get.side_effect = redis_get_side_effect

        call_count = 0

        @cached(endpoint="test", key_params=["param"])
        async def test_func(param: str) -> dict[str, str]:
            nonlocal call_count
            call_count += 1
            return {"result": "fresh"}

        result = await test_func(param="value")

        assert result == {"result": "from_other_request"}
        assert call_count == 0


class TestLockTimeout:
    """Test suite for lock acquisition timeout behavior."""

    @pytest.mark.anyio
    async def test_lock_timeout_falls_back_to_direct_execution(
        self,
        mock_cache_service: MagicMock,
        mock_get_cache_service: MagicMock,
        mock_redis_client: MagicMock,
    ) -> None:
        """Verify lock timeout results in direct function execution."""
        mock_cache_service.get.return_value = None
        mock_redis_client.set.return_value = False
        mock_redis_client.get.return_value = None

        with patch("techpulse.api.cache.decorator.DEFAULT_LOCK_MAX_WAIT_SECONDS", 0.1):
            call_count = 0

            @cached(endpoint="test", key_params=["param"])
            async def test_func(param: str) -> dict[str, str]:
                nonlocal call_count
                call_count += 1
                return {"result": "direct"}

            result = await test_func(param="value")

            assert result == {"result": "direct"}
            assert call_count == 1


class TestFailOpenBehavior:
    """Test suite for fail-open behavior on Redis errors."""

    @pytest.mark.anyio
    async def test_redis_error_on_lock_acquire_falls_back(
        self,
        mock_cache_service: MagicMock,
        mock_get_cache_service: MagicMock,
        mock_redis_client: MagicMock,
    ) -> None:
        """Verify Redis error during lock acquisition falls back to direct execution."""
        mock_cache_service.get.return_value = None
        mock_redis_client.set.side_effect = redis.ConnectionError("Connection lost")
        mock_redis_client.get.return_value = None

        call_count = 0

        @cached(endpoint="test", key_params=["param"])
        async def test_func(param: str) -> dict[str, str]:
            nonlocal call_count
            call_count += 1
            return {"result": "fallback"}

        result = await test_func(param="value")

        assert result == {"result": "fallback"}
        assert call_count == 1

    @pytest.mark.anyio
    async def test_redis_error_on_cache_write_continues(
        self,
        mock_cache_service: MagicMock,
        mock_get_cache_service: MagicMock,
        mock_redis_client: MagicMock,
    ) -> None:
        """Verify Redis error during cache write does not affect result."""
        mock_cache_service.get.return_value = None
        mock_cache_service.set.return_value = False
        mock_redis_client.get.return_value = None
        mock_redis_client.set.return_value = True

        @cached(endpoint="test", key_params=["param"])
        async def test_func(param: str) -> dict[str, str]:
            return {"result": "computed"}

        result = await test_func(param="value")

        assert result == {"result": "computed"}


class TestSyncFunctionSupport:
    """Test suite for synchronous function support."""

    @pytest.mark.anyio
    async def test_sync_function_wrapped_correctly(
        self,
        mock_cache_service: MagicMock,
        mock_get_cache_service: MagicMock,
        mock_redis_client: MagicMock,
    ) -> None:
        """Verify synchronous functions work with the decorator."""
        mock_cache_service.get.return_value = None
        mock_redis_client.get.return_value = None
        mock_redis_client.set.return_value = True

        @cached(endpoint="test", key_params=["param"])
        def test_func(param: str) -> dict[str, str]:
            return {"result": "sync"}

        result = await test_func(param="value")

        assert result == {"result": "sync"}


class TestCustomTTL:
    """Test suite for custom TTL configuration."""

    @pytest.mark.anyio
    async def test_custom_ttl_passed_to_cache_set(
        self,
        mock_cache_service: MagicMock,
        mock_get_cache_service: MagicMock,
        mock_redis_client: MagicMock,
    ) -> None:
        """Verify custom TTL is passed to cache set operation."""
        mock_cache_service.get.return_value = None
        mock_redis_client.get.return_value = None
        mock_redis_client.set.return_value = True

        @cached(endpoint="test", key_params=["param"], ttl=7200)
        async def test_func(param: str) -> dict[str, str]:
            return {"result": "fresh"}

        await test_func(param="value")

        mock_cache_service.set.assert_called_once()
        call_args = mock_cache_service.set.call_args
        assert call_args[0][2] == 7200


class TestCacheLockAcquisitionError:
    """Test suite for CacheLockAcquisitionError exception."""

    def test_error_attributes(self) -> None:
        """Verify error contains key and wait_time attributes."""
        error = CacheLockAcquisitionError("test:key:lock", 5.5)

        assert error.key == "test:key:lock"
        assert error.wait_time == 5.5
        assert "test:key:lock" in str(error)
        assert "5.50" in str(error)


class TestDefaultConstants:
    """Test suite for default constant values."""

    def test_default_lock_timeout(self) -> None:
        """Verify default lock timeout is 30 seconds."""
        assert DEFAULT_LOCK_TIMEOUT_SECONDS == 30

    def test_default_max_wait(self) -> None:
        """Verify default max wait is 10 seconds."""
        assert DEFAULT_LOCK_MAX_WAIT_SECONDS == 10.0
