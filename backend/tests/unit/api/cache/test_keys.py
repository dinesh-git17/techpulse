"""Unit tests for CacheKeyBuilder class."""

from techpulse.api.cache.keys import CacheKeyBuilder


class TestCacheKeyBuilderInit:
    """Test suite for CacheKeyBuilder initialization."""

    def test_init_default_prefix(self) -> None:
        """Verify default prefix is 'tp'."""
        builder = CacheKeyBuilder()
        assert builder.prefix == "tp"

    def test_init_default_version(self) -> None:
        """Verify default version is 'v1'."""
        builder = CacheKeyBuilder()
        assert builder.version == "v1"

    def test_init_custom_prefix(self) -> None:
        """Verify custom prefix is stored."""
        builder = CacheKeyBuilder(prefix="custom")
        assert builder.prefix == "custom"

    def test_init_custom_version(self) -> None:
        """Verify custom version is stored."""
        builder = CacheKeyBuilder(version="v2")
        assert builder.version == "v2"


class TestCacheKeyBuilderBuild:
    """Test suite for CacheKeyBuilder.build method."""

    def test_build_returns_string(self) -> None:
        """Verify build returns a string key."""
        builder = CacheKeyBuilder()
        key = builder.build("trends")
        assert isinstance(key, str)

    def test_build_key_format(self) -> None:
        """Verify key follows prefix:version:endpoint:hash format."""
        builder = CacheKeyBuilder()
        key = builder.build("trends", start="2024-01")
        parts = key.split(":")
        assert len(parts) == 4
        assert parts[0] == "tp"
        assert parts[1] == "v1"
        assert parts[2] == "trends"
        assert len(parts[3]) == 16  # Hash is 16 chars

    def test_build_empty_params_returns_empty_hash(self) -> None:
        """Verify empty params produces 'empty' hash."""
        builder = CacheKeyBuilder()
        key = builder.build("trends")
        assert key == "tp:v1:trends:empty"

    def test_build_same_params_same_key(self) -> None:
        """Verify identical params produce identical keys."""
        builder = CacheKeyBuilder()
        key1 = builder.build("trends", start="2024-01", end="2024-12")
        key2 = builder.build("trends", start="2024-01", end="2024-12")
        assert key1 == key2

    def test_build_different_params_different_key(self) -> None:
        """Verify different params produce different keys."""
        builder = CacheKeyBuilder()
        key1 = builder.build("trends", start="2024-01")
        key2 = builder.build("trends", start="2024-02")
        assert key1 != key2

    def test_build_param_order_independent(self) -> None:
        """Verify param order does not affect key."""
        builder = CacheKeyBuilder()
        key1 = builder.build("trends", start="2024-01", end="2024-12")
        key2 = builder.build("trends", end="2024-12", start="2024-01")
        assert key1 == key2


class TestCacheKeyBuilderListNormalization:
    """Test suite for list parameter normalization."""

    def test_build_list_order_independent(self) -> None:
        """Verify list order does not affect key (critical acceptance criteria)."""
        builder = CacheKeyBuilder()
        key1 = builder.build("trends", techs=["b", "a"])
        key2 = builder.build("trends", techs=["a", "b"])
        assert key1 == key2

    def test_build_list_sorted_alphabetically(self) -> None:
        """Verify lists are sorted alphabetically."""
        builder = CacheKeyBuilder()
        key1 = builder.build("trends", techs=["python", "react", "go"])
        key2 = builder.build("trends", techs=["react", "go", "python"])
        key3 = builder.build("trends", techs=["go", "python", "react"])
        assert key1 == key2 == key3

    def test_build_multiple_lists_normalized(self) -> None:
        """Verify multiple list params are all normalized."""
        builder = CacheKeyBuilder()
        key1 = builder.build(
            "trends",
            techs=["b", "a"],
            categories=["y", "x"],
        )
        key2 = builder.build(
            "trends",
            techs=["a", "b"],
            categories=["x", "y"],
        )
        assert key1 == key2

    def test_build_empty_list_included(self) -> None:
        """Verify empty lists are included in key."""
        builder = CacheKeyBuilder()
        key1 = builder.build("trends", techs=[])
        key2 = builder.build("trends")
        assert key1 != key2


class TestCacheKeyBuilderNoneHandling:
    """Test suite for None value handling."""

    def test_build_none_value_excluded(self) -> None:
        """Verify None values are excluded from key generation."""
        builder = CacheKeyBuilder()
        key1 = builder.build("trends", start="2024-01", end=None)
        key2 = builder.build("trends", start="2024-01")
        assert key1 == key2

    def test_build_all_none_returns_empty(self) -> None:
        """Verify all None params produces 'empty' hash."""
        builder = CacheKeyBuilder()
        key = builder.build("trends", start=None, end=None)
        assert key == "tp:v1:trends:empty"


class TestCacheKeyBuilderEndpoints:
    """Test suite for different endpoint handling."""

    def test_build_different_endpoints_different_keys(self) -> None:
        """Verify different endpoints produce different keys."""
        builder = CacheKeyBuilder()
        key1 = builder.build("trends", page=1)
        key2 = builder.build("technologies", page=1)
        assert key1 != key2

    def test_build_various_endpoints(self) -> None:
        """Verify various endpoint names work correctly."""
        builder = CacheKeyBuilder()
        endpoints = ["trends", "technologies", "jobs", "skills"]
        keys = [builder.build(ep, id="test") for ep in endpoints]
        assert len(set(keys)) == len(endpoints)  # All unique


class TestCacheKeyBuilderPattern:
    """Test suite for CacheKeyBuilder.pattern method."""

    def test_pattern_returns_glob_pattern(self) -> None:
        """Verify pattern returns a glob pattern string."""
        builder = CacheKeyBuilder()
        pattern = builder.pattern("trends")
        assert pattern == "tp:v1:trends:*"

    def test_pattern_custom_prefix_version(self) -> None:
        """Verify pattern uses custom prefix and version."""
        builder = CacheKeyBuilder(prefix="cache", version="v2")
        pattern = builder.pattern("trends")
        assert pattern == "cache:v2:trends:*"


class TestCacheKeyBuilderAllPattern:
    """Test suite for CacheKeyBuilder.all_pattern method."""

    def test_all_pattern_returns_glob_pattern(self) -> None:
        """Verify all_pattern returns a glob pattern string."""
        builder = CacheKeyBuilder()
        pattern = builder.all_pattern()
        assert pattern == "tp:v1:*"

    def test_all_pattern_custom_prefix_version(self) -> None:
        """Verify all_pattern uses custom prefix and version."""
        builder = CacheKeyBuilder(prefix="cache", version="v2")
        pattern = builder.all_pattern()
        assert pattern == "cache:v2:*"


class TestCacheKeyBuilderIntTypes:
    """Test suite for integer parameter handling."""

    def test_build_int_param(self) -> None:
        """Verify integer params work correctly."""
        builder = CacheKeyBuilder()
        key = builder.build("trends", page=1, page_size=20)
        assert "tp:v1:trends:" in key
        assert key != "tp:v1:trends:empty"

    def test_build_same_int_same_key(self) -> None:
        """Verify same integer produces same key."""
        builder = CacheKeyBuilder()
        key1 = builder.build("trends", page=1)
        key2 = builder.build("trends", page=1)
        assert key1 == key2

    def test_build_different_int_different_key(self) -> None:
        """Verify different integers produce different keys."""
        builder = CacheKeyBuilder()
        key1 = builder.build("trends", page=1)
        key2 = builder.build("trends", page=2)
        assert key1 != key2


class TestCacheKeyBuilderMixedParams:
    """Test suite for mixed parameter types."""

    def test_build_mixed_types(self) -> None:
        """Verify mixed param types work together."""
        builder = CacheKeyBuilder()
        key = builder.build(
            "trends",
            techs=["python", "go"],
            start="2024-01",
            page=1,
        )
        assert "tp:v1:trends:" in key

    def test_build_mixed_types_deterministic(self) -> None:
        """Verify mixed params produce deterministic keys."""
        builder = CacheKeyBuilder()
        key1 = builder.build(
            "trends",
            techs=["go", "python"],
            start="2024-01",
            page=1,
        )
        key2 = builder.build(
            "trends",
            page=1,
            start="2024-01",
            techs=["python", "go"],
        )
        assert key1 == key2
