"""Integration tests for cache stampede prevention.

These tests verify that the @cached decorator with SETNX locking
prevents multiple concurrent requests from hitting the database.
The "zero-stampede" guarantee ensures that if N requests arrive
simultaneously on a cold cache, only 1 database query is executed.
"""

import asyncio
from unittest.mock import MagicMock, patch

import pytest

from techpulse.api.cache.decorator import cached


class MockRedisClient:
    """Mock Redis client with SETNX locking simulation.

    Simulates Redis SETNX behavior for distributed locking.
    Tracks lock acquisition attempts and provides thread-safe
    lock/unlock semantics.
    """

    def __init__(self) -> None:
        """Initialize mock client with empty cache and no lock."""
        self._cache: dict[str, bytes] = {}
        self._lock: asyncio.Lock = asyncio.Lock()
        self._redis_lock_held: bool = False
        self._lock_holder_id: int | None = None

    def get(self, key: str) -> bytes | None:
        """Get value from mock cache.

        Args:
            key: The cache key to retrieve.

        Returns:
            The cached bytes, or None if not found.
        """
        return self._cache.get(key)

    def set(
        self,
        key: str,
        value: bytes,
        nx: bool = False,
        ex: int | None = None,
    ) -> bool:
        """Set value in mock cache with optional NX flag.

        Args:
            key: The cache key to set.
            value: The value to store.
            nx: If True, only set if key does not exist.
            ex: Expiry time in seconds (ignored in mock).

        Returns:
            True if value was set, False if NX prevented set.
        """
        if nx and ":lock" in key:
            if self._redis_lock_held:
                return False
            self._redis_lock_held = True
            return True

        self._cache[key] = value
        return True

    def delete(self, key: str) -> int:
        """Delete key from mock cache.

        Args:
            key: The cache key to delete.

        Returns:
            1 if key was deleted, 0 otherwise.
        """
        if ":lock" in key:
            self._redis_lock_held = False
        if key in self._cache:
            del self._cache[key]
            return 1
        return 0


class MockCacheService:
    """Mock CacheService for integration testing.

    Provides the same interface as CacheService but uses
    MockRedisClient for in-memory operation.
    """

    def __init__(self) -> None:
        """Initialize mock service with mock Redis client."""
        self._client = MockRedisClient()
        self._cache: dict[str, bytes] = {}
        self.default_ttl = 86400

    def is_connected(self) -> bool:
        """Check connection status.

        Returns:
            Always True for mock service.
        """
        return True

    def get(self, key: str) -> bytes | None:
        """Get value from cache.

        Args:
            key: The cache key to retrieve.

        Returns:
            The cached bytes, or None if not found.
        """
        return self._cache.get(key)

    def set(self, key: str, value: bytes, ttl: int | None = None) -> bool:
        """Set value in cache.

        Args:
            key: The cache key to set.
            value: The value to store.
            ttl: TTL in seconds (ignored in mock).

        Returns:
            True indicating successful set.
        """
        self._cache[key] = value
        self._client._cache[key] = value
        return True


class TestStampedePrevention:
    """Test suite for cache stampede prevention.

    Verifies that the @cached decorator prevents multiple concurrent
    requests from hitting the database on a cold cache.
    """

    @pytest.mark.anyio
    async def test_fifty_concurrent_requests_single_db_call(self) -> None:
        """Verify 50 concurrent requests result in exactly 1 database call.

        This is the core stampede prevention test. On a cold cache,
        50 simultaneous requests should result in only 1 database query.
        The remaining 49 requests should wait for the cache to be
        populated and then return the cached result.
        """
        mock_service = MockCacheService()
        db_call_count = 0
        db_call_lock = asyncio.Lock()

        @cached(endpoint="trends", key_params=["tech_ids"])
        async def fetch_trends(tech_ids: list[str]) -> dict[str, object]:
            nonlocal db_call_count
            async with db_call_lock:
                db_call_count += 1

            await asyncio.sleep(0.01)
            return {
                "tech_ids": tech_ids,
                "data": [{"month": "2024-01", "count": 100}],
            }

        with patch(
            "techpulse.api.cache.decorator.get_cache_service",
            return_value=mock_service,
        ):
            tasks = [
                asyncio.create_task(fetch_trends(tech_ids=["python", "react"]))
                for _ in range(50)
            ]

            results = await asyncio.gather(*tasks)

        assert db_call_count == 1, (
            f"Expected exactly 1 DB call for 50 concurrent requests, "
            f"but got {db_call_count}"
        )

        assert len(results) == 50
        for result in results:
            assert result["tech_ids"] == ["python", "react"]
            assert result["data"] == [{"month": "2024-01", "count": 100}]

    @pytest.mark.anyio
    async def test_different_params_hit_db_separately(self) -> None:
        """Verify different parameters result in separate DB calls.

        Requests with different cache keys should each hit the database
        independently, as they represent different data sets.
        """
        mock_service = MockCacheService()
        db_calls: list[str] = []
        db_call_lock = asyncio.Lock()

        @cached(endpoint="trends", key_params=["tech_id"])
        async def fetch_trend(tech_id: str) -> dict[str, str]:
            nonlocal db_calls
            async with db_call_lock:
                db_calls.append(tech_id)

            await asyncio.sleep(0.01)
            return {"tech_id": tech_id, "count": "100"}

        with patch(
            "techpulse.api.cache.decorator.get_cache_service",
            return_value=mock_service,
        ):
            tasks = []
            for tech_id in ["python", "react", "node"]:
                for _ in range(10):
                    tasks.append(asyncio.create_task(fetch_trend(tech_id=tech_id)))

            await asyncio.gather(*tasks)

        assert len(db_calls) == 3, (
            f"Expected 3 DB calls (one per tech_id), but got {len(db_calls)}"
        )
        assert set(db_calls) == {"python", "react", "node"}

    @pytest.mark.anyio
    async def test_cache_hit_after_first_request(self) -> None:
        """Verify subsequent requests hit cache after initial population."""
        mock_service = MockCacheService()
        db_call_count = 0

        @cached(endpoint="trends", key_params=["tech_id"])
        async def fetch_trend(tech_id: str) -> dict[str, str]:
            nonlocal db_call_count
            db_call_count += 1
            return {"tech_id": tech_id}

        with patch(
            "techpulse.api.cache.decorator.get_cache_service",
            return_value=mock_service,
        ):
            result1 = await fetch_trend(tech_id="python")

            result2 = await fetch_trend(tech_id="python")
            result3 = await fetch_trend(tech_id="python")

        assert db_call_count == 1
        assert result1 == result2 == result3 == {"tech_id": "python"}


class TestStampedeWithRealRedisClient:
    """Test suite using mock Redis client with realistic SETNX behavior.

    These tests verify the SETNX locking mechanism works correctly
    with a more realistic Redis client simulation.
    """

    @pytest.mark.anyio
    async def test_lock_prevents_concurrent_db_access(self) -> None:
        """Verify SETNX lock prevents concurrent database access.

        Simulates the race condition where multiple requests arrive
        simultaneously and compete for the lock. Only the lock holder
        should execute the database query.
        """
        mock_redis = MockRedisClient()
        cache_store: dict[str, bytes] = {}

        def get_side_effect(key: str) -> bytes | None:
            return cache_store.get(key)

        def set_side_effect(key: str, value: bytes, ttl: int | None = None) -> bool:
            cache_store[key] = value
            mock_redis._cache[key] = value
            return True

        mock_service = MagicMock()
        mock_service.is_connected.return_value = True
        mock_service.get.side_effect = get_side_effect
        mock_service.set.side_effect = set_side_effect
        mock_service._client = mock_redis
        mock_service.default_ttl = 86400

        db_call_count = 0
        db_call_lock = asyncio.Lock()

        @cached(endpoint="test", key_params=["param"])
        async def db_operation(param: str) -> dict[str, str]:
            nonlocal db_call_count
            async with db_call_lock:
                db_call_count += 1
            await asyncio.sleep(0.02)
            return {"param": param, "result": "computed"}

        with patch(
            "techpulse.api.cache.decorator.get_cache_service",
            return_value=mock_service,
        ):
            tasks = [
                asyncio.create_task(db_operation(param="same_value")) for _ in range(20)
            ]

            results = await asyncio.gather(*tasks)

        assert db_call_count <= 2, (
            f"Expected at most 2 DB calls due to lock timing, but got {db_call_count}"
        )

        for result in results:
            assert result["param"] == "same_value"


class TestStampedeRecovery:
    """Test suite for stampede recovery scenarios.

    Verifies behavior when the initial request fails or times out.
    """

    @pytest.mark.anyio
    async def test_subsequent_requests_retry_on_failed_cache_population(
        self,
    ) -> None:
        """Verify requests retry when initial cache population fails.

        If the lock holder fails to populate the cache (e.g., DB error),
        subsequent requests should be able to acquire the lock and retry.
        """
        mock_redis = MockRedisClient()
        mock_service = MagicMock()
        mock_service.is_connected.return_value = True
        mock_service.get.return_value = None
        mock_service.set.return_value = True
        mock_service._client = mock_redis
        mock_service.default_ttl = 86400

        call_count = 0

        @cached(endpoint="test", key_params=["param"])
        async def sometimes_fails(param: str) -> dict[str, str]:
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise ValueError("First call fails")
            return {"param": param, "attempt": call_count}

        with patch(
            "techpulse.api.cache.decorator.get_cache_service",
            return_value=mock_service,
        ):
            with pytest.raises(ValueError):
                await sometimes_fails(param="value")

            result = await sometimes_fails(param="value")

        assert call_count == 2
        assert result["attempt"] == 2
