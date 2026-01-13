"""Unit tests for CacheSerializer class."""

from datetime import datetime
from typing import Optional

import pytest
from pydantic import BaseModel

from techpulse.api.cache.serializer import CacheSerializationError, CacheSerializer


class SampleModel(BaseModel):
    """Sample Pydantic model for testing serialization."""

    id: int
    name: str
    active: bool = True


class NestedModel(BaseModel):
    """Nested Pydantic model for testing complex serialization."""

    id: int
    name: str
    tags: list[str]
    metadata: dict[str, str]


class DateModel(BaseModel):
    """Model with datetime for testing date serialization."""

    id: int
    created_at: datetime


class OptionalModel(BaseModel):
    """Model with optional fields for testing None handling."""

    id: int
    name: Optional[str] = None


class TestCacheSerializerSerialize:
    """Test suite for CacheSerializer.serialize method."""

    def test_serialize_returns_bytes(self) -> None:
        """Verify serialize returns bytes."""
        serializer = CacheSerializer()
        result = serializer.serialize({"key": "value"})
        assert isinstance(result, bytes)

    def test_serialize_dict(self) -> None:
        """Verify dict serialization works."""
        serializer = CacheSerializer()
        data = {"name": "python", "count": 42}
        result = serializer.serialize(data)
        assert b'"name"' in result
        assert b'"python"' in result
        assert b'"count"' in result
        assert b"42" in result

    def test_serialize_list(self) -> None:
        """Verify list serialization works."""
        serializer = CacheSerializer()
        data = [1, 2, 3]
        result = serializer.serialize(data)
        assert result == b"[1,2,3]"

    def test_serialize_nested_dict(self) -> None:
        """Verify nested dict serialization works."""
        serializer = CacheSerializer()
        data = {"outer": {"inner": "value"}}
        result = serializer.serialize(data)
        assert b'"outer"' in result
        assert b'"inner"' in result

    def test_serialize_pydantic_model(self) -> None:
        """Verify Pydantic model serialization works."""
        serializer = CacheSerializer()
        model = SampleModel(id=1, name="test")
        result = serializer.serialize(model)
        assert b'"id"' in result
        assert b"1" in result
        assert b'"name"' in result
        assert b'"test"' in result

    def test_serialize_pydantic_model_with_defaults(self) -> None:
        """Verify Pydantic model with defaults serializes correctly."""
        serializer = CacheSerializer()
        model = SampleModel(id=1, name="test")
        result = serializer.serialize(model)
        assert b'"active"' in result
        assert b"true" in result

    def test_serialize_nested_pydantic_model(self) -> None:
        """Verify nested Pydantic model serialization works."""
        serializer = CacheSerializer()
        model = NestedModel(
            id=1,
            name="test",
            tags=["a", "b"],
            metadata={"key": "value"},
        )
        result = serializer.serialize(model)
        assert b'"tags"' in result
        assert b'"metadata"' in result


class TestCacheSerializerDeserialize:
    """Test suite for CacheSerializer.deserialize method."""

    def test_deserialize_returns_dict(self) -> None:
        """Verify deserialize returns dict for object JSON."""
        serializer = CacheSerializer()
        result = serializer.deserialize(b'{"key":"value"}')
        assert isinstance(result, dict)
        assert result == {"key": "value"}

    def test_deserialize_returns_list(self) -> None:
        """Verify deserialize returns list for array JSON."""
        serializer = CacheSerializer()
        result = serializer.deserialize(b"[1,2,3]")
        assert isinstance(result, list)
        assert result == [1, 2, 3]

    def test_deserialize_nested_dict(self) -> None:
        """Verify nested dict deserialization works."""
        serializer = CacheSerializer()
        result = serializer.deserialize(b'{"outer":{"inner":"value"}}')
        assert result == {"outer": {"inner": "value"}}

    def test_deserialize_preserves_types(self) -> None:
        """Verify types are preserved during deserialization."""
        serializer = CacheSerializer()
        data = b'{"int":42,"float":3.14,"bool":true,"null":null}'
        result = serializer.deserialize(data)
        assert result["int"] == 42
        assert result["float"] == 3.14
        assert result["bool"] is True
        assert result["null"] is None


class TestCacheSerializerRoundTrip:
    """Test suite for round-trip serialization."""

    def test_roundtrip_dict(self) -> None:
        """Verify dict round-trip preserves data."""
        serializer = CacheSerializer()
        original = {"name": "python", "count": 42, "active": True}
        serialized = serializer.serialize(original)
        restored = serializer.deserialize(serialized)
        assert restored == original

    def test_roundtrip_list(self) -> None:
        """Verify list round-trip preserves data."""
        serializer = CacheSerializer()
        original = [1, "two", 3.0, True, None]
        serialized = serializer.serialize(original)
        restored = serializer.deserialize(serialized)
        assert restored == original

    def test_roundtrip_pydantic_model(self) -> None:
        """Verify Pydantic model round-trip works (critical acceptance criteria)."""
        serializer = CacheSerializer()
        original = SampleModel(id=1, name="test", active=False)
        serialized = serializer.serialize(original)
        restored = serializer.deserialize_model(serialized, SampleModel)
        assert restored.id == original.id
        assert restored.name == original.name
        assert restored.active == original.active

    def test_roundtrip_nested_pydantic_model(self) -> None:
        """Verify nested Pydantic model round-trip works."""
        serializer = CacheSerializer()
        original = NestedModel(
            id=1,
            name="test",
            tags=["a", "b", "c"],
            metadata={"key1": "value1", "key2": "value2"},
        )
        serialized = serializer.serialize(original)
        restored = serializer.deserialize_model(serialized, NestedModel)
        assert restored.id == original.id
        assert restored.name == original.name
        assert restored.tags == original.tags
        assert restored.metadata == original.metadata


class TestCacheSerializerDeserializeModel:
    """Test suite for CacheSerializer.deserialize_model method."""

    def test_deserialize_model_returns_instance(self) -> None:
        """Verify deserialize_model returns model instance."""
        serializer = CacheSerializer()
        data = b'{"id":1,"name":"test"}'
        result = serializer.deserialize_model(data, SampleModel)
        assert isinstance(result, SampleModel)

    def test_deserialize_model_populates_fields(self) -> None:
        """Verify deserialize_model populates all fields."""
        serializer = CacheSerializer()
        data = b'{"id":42,"name":"python","active":false}'
        result = serializer.deserialize_model(data, SampleModel)
        assert result.id == 42
        assert result.name == "python"
        assert result.active is False

    def test_deserialize_model_uses_defaults(self) -> None:
        """Verify deserialize_model uses field defaults."""
        serializer = CacheSerializer()
        data = b'{"id":1,"name":"test"}'
        result = serializer.deserialize_model(data, SampleModel)
        assert result.active is True  # default value

    def test_deserialize_model_optional_fields(self) -> None:
        """Verify deserialize_model handles optional fields."""
        serializer = CacheSerializer()
        data = b'{"id":1}'
        result = serializer.deserialize_model(data, OptionalModel)
        assert result.id == 1
        assert result.name is None


class TestCacheSerializerSerializeList:
    """Test suite for CacheSerializer.serialize_list method."""

    def test_serialize_list_returns_bytes(self) -> None:
        """Verify serialize_list returns bytes."""
        serializer = CacheSerializer()
        items = [SampleModel(id=1, name="a"), SampleModel(id=2, name="b")]
        result = serializer.serialize_list(items)
        assert isinstance(result, bytes)

    def test_serialize_list_format(self) -> None:
        """Verify serialize_list produces valid JSON array."""
        serializer = CacheSerializer()
        items = [SampleModel(id=1, name="a")]
        result = serializer.serialize_list(items)
        assert result.startswith(b"[")
        assert result.endswith(b"]")

    def test_serialize_list_empty(self) -> None:
        """Verify serialize_list handles empty list."""
        serializer = CacheSerializer()
        result = serializer.serialize_list([])
        assert result == b"[]"

    def test_serialize_list_multiple_items(self) -> None:
        """Verify serialize_list handles multiple items."""
        serializer = CacheSerializer()
        items = [
            SampleModel(id=1, name="a"),
            SampleModel(id=2, name="b"),
            SampleModel(id=3, name="c"),
        ]
        result = serializer.serialize_list(items)
        assert b'"id":1' in result
        assert b'"id":2' in result
        assert b'"id":3' in result


class TestCacheSerializerDeserializeList:
    """Test suite for CacheSerializer.deserialize_list method."""

    def test_deserialize_list_returns_list(self) -> None:
        """Verify deserialize_list returns a list."""
        serializer = CacheSerializer()
        data = b'[{"id":1,"name":"a"},{"id":2,"name":"b"}]'
        result = serializer.deserialize_list(data, SampleModel)
        assert isinstance(result, list)
        assert len(result) == 2

    def test_deserialize_list_returns_model_instances(self) -> None:
        """Verify deserialize_list returns model instances."""
        serializer = CacheSerializer()
        data = b'[{"id":1,"name":"a"}]'
        result = serializer.deserialize_list(data, SampleModel)
        assert isinstance(result[0], SampleModel)

    def test_deserialize_list_populates_fields(self) -> None:
        """Verify deserialize_list populates all fields."""
        serializer = CacheSerializer()
        data = b'[{"id":1,"name":"first"},{"id":2,"name":"second"}]'
        result = serializer.deserialize_list(data, SampleModel)
        assert result[0].id == 1
        assert result[0].name == "first"
        assert result[1].id == 2
        assert result[1].name == "second"

    def test_deserialize_list_empty(self) -> None:
        """Verify deserialize_list handles empty array."""
        serializer = CacheSerializer()
        data = b"[]"
        result = serializer.deserialize_list(data, SampleModel)
        assert result == []


class TestCacheSerializerListRoundTrip:
    """Test suite for list round-trip serialization."""

    def test_list_roundtrip(self) -> None:
        """Verify list round-trip preserves data."""
        serializer = CacheSerializer()
        original = [
            SampleModel(id=1, name="first", active=True),
            SampleModel(id=2, name="second", active=False),
        ]
        serialized = serializer.serialize_list(original)
        restored = serializer.deserialize_list(serialized, SampleModel)

        assert len(restored) == len(original)
        for orig, rest in zip(original, restored, strict=True):
            assert rest.id == orig.id
            assert rest.name == orig.name
            assert rest.active == orig.active


class TestCacheSerializerErrors:
    """Test suite for error handling."""

    def test_serialize_invalid_type_raises_error(self) -> None:
        """Verify serialization of invalid type raises CacheSerializationError."""
        serializer = CacheSerializer()
        # Create an object that can't be serialized
        with pytest.raises(CacheSerializationError) as exc_info:
            serializer.serialize({"func": lambda x: x})  # type: ignore[dict-item]
        assert exc_info.value.operation == "serialize"

    def test_deserialize_invalid_json_raises_error(self) -> None:
        """Verify invalid JSON raises CacheSerializationError."""
        serializer = CacheSerializer()
        with pytest.raises(CacheSerializationError) as exc_info:
            serializer.deserialize(b"not valid json")
        assert exc_info.value.operation == "deserialize"

    def test_deserialize_model_invalid_json_raises_error(self) -> None:
        """Verify invalid JSON raises CacheSerializationError for model."""
        serializer = CacheSerializer()
        with pytest.raises(CacheSerializationError) as exc_info:
            serializer.deserialize_model(b"not valid json", SampleModel)
        assert exc_info.value.operation == "deserialize"

    def test_deserialize_model_validation_failure_raises_error(self) -> None:
        """Verify model validation failure raises CacheSerializationError."""
        serializer = CacheSerializer()
        # Missing required 'name' field
        with pytest.raises(CacheSerializationError) as exc_info:
            serializer.deserialize_model(b'{"id":1}', SampleModel)
        assert "validation failed" in exc_info.value.reason.lower()

    def test_deserialize_list_non_array_raises_error(self) -> None:
        """Verify non-array JSON raises CacheSerializationError."""
        serializer = CacheSerializer()
        with pytest.raises(CacheSerializationError) as exc_info:
            serializer.deserialize_list(b'{"id":1}', SampleModel)
        assert "Expected list" in exc_info.value.reason


class TestCacheSerializationErrorException:
    """Test suite for CacheSerializationError exception."""

    def test_error_stores_reason(self) -> None:
        """Verify reason attribute is stored."""
        error = CacheSerializationError(reason="test reason", operation="serialize")
        assert error.reason == "test reason"

    def test_error_stores_operation(self) -> None:
        """Verify operation attribute is stored."""
        error = CacheSerializationError(reason="test", operation="deserialize")
        assert error.operation == "deserialize"

    def test_error_formats_message(self) -> None:
        """Verify error message is formatted correctly."""
        error = CacheSerializationError(reason="invalid data", operation="serialize")
        assert "serialize" in str(error)
        assert "invalid data" in str(error)
