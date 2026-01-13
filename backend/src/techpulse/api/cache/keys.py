"""Cache key builder for deterministic cache key generation.

This module provides CacheKeyBuilder for generating consistent, normalized
cache keys from request parameters. Keys are deterministic regardless of
parameter order, ensuring cache hits for semantically equivalent requests.
"""

import hashlib
from typing import Union

import orjson


class CacheKeyBuilder:
    """Build deterministic cache keys from request parameters.

    This class generates consistent cache keys by normalizing parameters
    before hashing. List parameters are sorted alphabetically to ensure
    that ['a', 'b'] and ['b', 'a'] produce the same key.

    The key format is: {prefix}:{version}:{endpoint}:{param_hash}

    Attributes:
        prefix: The cache key prefix (default: "tp").
        version: The cache version for key rotation (default: "v1").

    Example:
        >>> builder = CacheKeyBuilder()
        >>> key = builder.build("trends", tech_ids=["react", "python"])
        >>> # Same key regardless of list order
        >>> same_key = builder.build("trends", tech_ids=["python", "react"])
        >>> assert key == same_key
    """

    def __init__(self, prefix: str = "tp", version: str = "v1") -> None:
        """Initialize the key builder with prefix and version.

        Args:
            prefix: The cache key prefix for namespacing.
            version: The cache version for key rotation on schema changes.
        """
        self.prefix = prefix
        self.version = version

    def build(self, endpoint: str, **kwargs: Union[str, int, list[str], None]) -> str:
        """Build a deterministic cache key from endpoint and parameters.

        Normalizes all parameters by sorting lists and creating a consistent
        hash. None values are excluded from the key generation.

        Args:
            endpoint: The API endpoint name (e.g., "trends", "technologies").
            **kwargs: Request parameters to include in the key.

        Returns:
            A deterministic cache key in format: prefix:version:endpoint:hash

        Example:
            >>> builder = CacheKeyBuilder()
            >>> builder.build("trends", start="2024-01", end="2024-12")
            'tp:v1:trends:a1b2c3d4...'
        """
        normalized = self._normalize_params(kwargs)
        param_hash = self._hash_params(normalized)
        return f"{self.prefix}:{self.version}:{endpoint}:{param_hash}"

    def _normalize_params(
        self, params: dict[str, Union[str, int, list[str], None]]
    ) -> dict[str, Union[str, int, list[str]]]:
        """Normalize parameters for consistent hashing.

        Sorts list values alphabetically and removes None values.
        Dict keys are also sorted during serialization.

        Args:
            params: The raw request parameters.

        Returns:
            Normalized parameters with sorted lists and no None values.
        """
        normalized: dict[str, Union[str, int, list[str]]] = {}

        for key, value in sorted(params.items()):
            if value is None:
                continue
            if isinstance(value, list):
                normalized[key] = sorted(value)
            else:
                normalized[key] = value

        return normalized

    def _hash_params(self, params: dict[str, Union[str, int, list[str]]]) -> str:
        """Generate a SHA-256 hash of normalized parameters.

        Uses orjson for fast, deterministic JSON serialization with
        sorted keys.

        Args:
            params: Normalized parameters to hash.

        Returns:
            First 16 characters of the SHA-256 hex digest.
        """
        if not params:
            return "empty"

        serialized = orjson.dumps(params, option=orjson.OPT_SORT_KEYS)
        hash_digest = hashlib.sha256(serialized).hexdigest()
        return hash_digest[:16]

    def pattern(self, endpoint: str) -> str:
        """Generate a glob pattern for matching all keys of an endpoint.

        Useful for bulk cache invalidation of all keys for a specific
        endpoint.

        Args:
            endpoint: The API endpoint name.

        Returns:
            A glob pattern matching all keys for the endpoint.

        Example:
            >>> builder = CacheKeyBuilder()
            >>> builder.pattern("trends")
            'tp:v1:trends:*'
        """
        return f"{self.prefix}:{self.version}:{endpoint}:*"

    def all_pattern(self) -> str:
        """Generate a glob pattern for matching all cache keys.

        Useful for complete cache invalidation.

        Returns:
            A glob pattern matching all keys with the current prefix/version.

        Example:
            >>> builder = CacheKeyBuilder()
            >>> builder.all_pattern()
            'tp:v1:*'
        """
        return f"{self.prefix}:{self.version}:*"
