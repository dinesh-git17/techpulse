"""Cache serialization using orjson for fast JSON encoding/decoding.

This module provides CacheSerializer for converting Python objects to
bytes for cache storage and back. Uses orjson for 3-10x faster
serialization compared to stdlib json.
"""

from typing import TypeVar

import orjson
from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class CacheSerializationError(Exception):
    """Raised when cache serialization or deserialization fails.

    Attributes:
        reason: A descriptive explanation of the serialization failure.
        operation: The operation that failed (serialize or deserialize).
    """

    def __init__(self, reason: str, operation: str) -> None:
        """Initialize the serialization error with reason and operation.

        Args:
            reason: A human-readable description of why the operation failed.
            operation: The operation that failed (serialize or deserialize).
        """
        self.reason = reason
        self.operation = operation
        super().__init__(f"Cache {operation} failed: {reason}")


class CacheSerializer:
    """Serialize and deserialize data for cache storage using orjson.

    This class handles conversion between Python objects and bytes for
    Redis cache storage. Supports Pydantic models, dicts, lists, and
    primitive types.

    Uses orjson options for optimal performance:
    - OPT_SERIALIZE_NUMPY: Handle numpy types if present
    - OPT_UTC_Z: Use 'Z' suffix for UTC timestamps

    Example:
        >>> serializer = CacheSerializer()
        >>> data = {"name": "python", "count": 42}
        >>> cached = serializer.serialize(data)
        >>> restored = serializer.deserialize(cached)
        >>> assert data == restored
    """

    def serialize(self, data: dict[str, object] | list[object] | BaseModel) -> bytes:
        """Serialize data to bytes for cache storage.

        Handles Pydantic models by converting to dict first, then
        serializing with orjson.

        Args:
            data: The data to serialize. Can be a dict, list, or Pydantic model.

        Returns:
            JSON bytes suitable for cache storage.

        Raises:
            CacheSerializationError: If serialization fails.

        Example:
            >>> serializer = CacheSerializer()
            >>> serializer.serialize({"key": "value"})
            b'{"key":"value"}'
        """
        try:
            json_data: dict[str, object] | list[object]
            if isinstance(data, BaseModel):
                json_data = data.model_dump(mode="json")
            else:
                json_data = data

            return orjson.dumps(
                json_data,
                option=orjson.OPT_SERIALIZE_NUMPY | orjson.OPT_UTC_Z,
            )
        except (TypeError, orjson.JSONEncodeError) as error:
            raise CacheSerializationError(
                reason=str(error),
                operation="serialize",
            ) from error

    def deserialize(self, data: bytes) -> dict[str, object] | list[object]:
        """Deserialize bytes from cache back to Python objects.

        Args:
            data: The cached bytes to deserialize.

        Returns:
            The deserialized Python object (dict or list).

        Raises:
            CacheSerializationError: If deserialization fails.

        Example:
            >>> serializer = CacheSerializer()
            >>> serializer.deserialize(b'{"key":"value"}')
            {'key': 'value'}
        """
        try:
            result: dict[str, object] | list[object] = orjson.loads(data)
            return result
        except (orjson.JSONDecodeError, TypeError) as error:
            raise CacheSerializationError(
                reason=str(error),
                operation="deserialize",
            ) from error

    def deserialize_model(self, data: bytes, model_class: type[T]) -> T:
        """Deserialize bytes from cache into a Pydantic model.

        Provides type-safe deserialization directly into the expected
        Pydantic model type.

        Args:
            data: The cached bytes to deserialize.
            model_class: The Pydantic model class to deserialize into.

        Returns:
            An instance of the specified Pydantic model.

        Raises:
            CacheSerializationError: If deserialization or validation fails.

        Example:
            >>> from pydantic import BaseModel
            >>> class User(BaseModel):
            ...     name: str
            ...     age: int
            >>> serializer = CacheSerializer()
            >>> user = serializer.deserialize_model(b'{"name":"Alice","age":30}', User)
            >>> assert user.name == "Alice"
        """
        try:
            json_data = orjson.loads(data)
            return model_class.model_validate(json_data)
        except (orjson.JSONDecodeError, TypeError) as error:
            raise CacheSerializationError(
                reason=str(error),
                operation="deserialize",
            ) from error
        except ValueError as error:
            raise CacheSerializationError(
                reason=f"Model validation failed: {error}",
                operation="deserialize",
            ) from error

    def serialize_list(self, items: list[BaseModel]) -> bytes:
        """Serialize a list of Pydantic models to bytes.

        Convenience method for caching lists of domain objects.

        Args:
            items: List of Pydantic model instances to serialize.

        Returns:
            JSON bytes containing the serialized list.

        Raises:
            CacheSerializationError: If serialization fails.

        Example:
            >>> from pydantic import BaseModel
            >>> class Item(BaseModel):
            ...     id: int
            >>> serializer = CacheSerializer()
            >>> items = [Item(id=1), Item(id=2)]
            >>> data = serializer.serialize_list(items)
        """
        try:
            json_list = [item.model_dump(mode="json") for item in items]
            return orjson.dumps(
                json_list,
                option=orjson.OPT_SERIALIZE_NUMPY | orjson.OPT_UTC_Z,
            )
        except (TypeError, orjson.JSONEncodeError) as error:
            raise CacheSerializationError(
                reason=str(error),
                operation="serialize",
            ) from error

    def deserialize_list(self, data: bytes, model_class: type[T]) -> list[T]:
        """Deserialize bytes into a list of Pydantic models.

        Provides type-safe deserialization of cached lists directly
        into the expected Pydantic model type.

        Args:
            data: The cached bytes to deserialize.
            model_class: The Pydantic model class for list items.

        Returns:
            A list of Pydantic model instances.

        Raises:
            CacheSerializationError: If deserialization or validation fails.

        Example:
            >>> from pydantic import BaseModel
            >>> class Item(BaseModel):
            ...     id: int
            >>> serializer = CacheSerializer()
            >>> items = serializer.deserialize_list(b'[{"id":1},{"id":2}]', Item)
            >>> assert len(items) == 2
        """
        try:
            json_list = orjson.loads(data)
            if not isinstance(json_list, list):
                raise CacheSerializationError(
                    reason="Expected list, got " + type(json_list).__name__,
                    operation="deserialize",
                )
            return [model_class.model_validate(item) for item in json_list]
        except (orjson.JSONDecodeError, TypeError) as error:
            raise CacheSerializationError(
                reason=str(error),
                operation="deserialize",
            ) from error
        except ValueError as error:
            raise CacheSerializationError(
                reason=f"Model validation failed: {error}",
                operation="deserialize",
            ) from error
