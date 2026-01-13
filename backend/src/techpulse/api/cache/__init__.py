"""Cache module for Redis-based caching with fail-open behavior.

This module provides a service-layer cache implementation using Redis
(Upstash) with automatic fail-open behavior. Cache failures are logged
but do not impact API availability.

Components:
    - CacheService: Redis client with fail-open get/set/delete operations
    - CacheKeyBuilder: Deterministic cache key generation with normalization
    - CacheSerializer: Fast JSON serialization using orjson
"""

from techpulse.api.cache.keys import CacheKeyBuilder
from techpulse.api.cache.serializer import CacheSerializationError, CacheSerializer
from techpulse.api.cache.service import (
    CacheService,
    close_cache_service,
    get_cache_service,
    init_cache_service,
)

__all__ = [
    "CacheKeyBuilder",
    "CacheSerializationError",
    "CacheSerializer",
    "CacheService",
    "close_cache_service",
    "get_cache_service",
    "init_cache_service",
]
