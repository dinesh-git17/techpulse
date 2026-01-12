"""Unit tests for storage exception hierarchy."""

from techpulse.storage.exceptions import (
    InvalidPayloadError,
    StorageConnectionError,
    StorageError,
    TransactionError,
)


class TestExceptionHierarchy:
    """Test suite for exception class hierarchy."""

    def test_storage_connection_error_inherits_from_base(self) -> None:
        """Verify StorageConnectionError inherits from StorageError."""
        error = StorageConnectionError("/path/to/db.duckdb", "Lock timeout")
        assert isinstance(error, StorageError)
        assert isinstance(error, Exception)

    def test_invalid_payload_error_inherits_from_base(self) -> None:
        """Verify InvalidPayloadError inherits from StorageError."""
        error = InvalidPayloadError(0, "Malformed JSON")
        assert isinstance(error, StorageError)
        assert isinstance(error, Exception)

    def test_transaction_error_inherits_from_base(self) -> None:
        """Verify TransactionError inherits from StorageError."""
        error = TransactionError("insert", "Constraint violation")
        assert isinstance(error, StorageError)
        assert isinstance(error, Exception)


class TestStorageConnectionError:
    """Test suite for StorageConnectionError."""

    def test_stores_path(self) -> None:
        """Verify path attribute is set."""
        error = StorageConnectionError("/data/techpulse.duckdb", "File locked")
        assert error.path == "/data/techpulse.duckdb"

    def test_stores_reason(self) -> None:
        """Verify reason attribute is set."""
        error = StorageConnectionError("/data/techpulse.duckdb", "File locked")
        assert error.reason == "File locked"

    def test_string_representation(self) -> None:
        """Verify error string includes path and reason."""
        error = StorageConnectionError("/var/lib/db.duckdb", "Permission denied")
        error_str = str(error)
        assert "/var/lib/db.duckdb" in error_str
        assert "Permission denied" in error_str


class TestInvalidPayloadError:
    """Test suite for InvalidPayloadError."""

    def test_stores_payload_index(self) -> None:
        """Verify payload_index attribute is set."""
        error = InvalidPayloadError(42, "Unexpected token")
        assert error.payload_index == 42

    def test_stores_reason(self) -> None:
        """Verify reason attribute is set."""
        error = InvalidPayloadError(0, "Unexpected token")
        assert error.reason == "Unexpected token"

    def test_string_representation(self) -> None:
        """Verify error string includes index and reason."""
        error = InvalidPayloadError(5, "Invalid UTF-8 sequence")
        error_str = str(error)
        assert "5" in error_str
        assert "Invalid UTF-8 sequence" in error_str


class TestTransactionError:
    """Test suite for TransactionError."""

    def test_stores_operation(self) -> None:
        """Verify operation attribute is set."""
        error = TransactionError("insert", "Disk full")
        assert error.operation == "insert"

    def test_stores_reason(self) -> None:
        """Verify reason attribute is set."""
        error = TransactionError("commit", "Lock timeout")
        assert error.reason == "Lock timeout"

    def test_string_representation(self) -> None:
        """Verify error string includes operation and reason."""
        error = TransactionError("batch_insert", "Integrity constraint violated")
        error_str = str(error)
        assert "batch_insert" in error_str
        assert "Integrity constraint violated" in error_str


class TestCatchAllHandler:
    """Test suite verifying base class can catch all storage errors."""

    def test_base_class_catches_connection_error(self) -> None:
        """Verify StorageError catches StorageConnectionError."""
        try:
            raise StorageConnectionError("/db.duckdb", "Timeout")
        except StorageError:
            pass

    def test_base_class_catches_invalid_payload_error(self) -> None:
        """Verify StorageError catches InvalidPayloadError."""
        try:
            raise InvalidPayloadError(0, "Bad JSON")
        except StorageError:
            pass

    def test_base_class_catches_transaction_error(self) -> None:
        """Verify StorageError catches TransactionError."""
        try:
            raise TransactionError("insert", "Rollback triggered")
        except StorageError:
            pass
