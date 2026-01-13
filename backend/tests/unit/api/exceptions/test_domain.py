"""Unit tests for domain exception classes."""

import pytest

from techpulse.api.exceptions.domain import (
    APIError,
    CacheConnectionError,
    DatabaseConnectionError,
    DataValidationError,
    QueryExecutionError,
    RecordNotFoundError,
)


class TestAPIError:
    """Test suite for base APIError exception."""

    def test_is_exception(self) -> None:
        """Verify APIError is an Exception subclass."""
        assert issubclass(APIError, Exception)

    def test_can_be_raised(self) -> None:
        """Verify APIError can be raised and caught."""
        with pytest.raises(APIError):
            raise APIError("test error")

    def test_message_preserved(self) -> None:
        """Verify error message is preserved."""
        error = APIError("test message")
        assert str(error) == "test message"


class TestDatabaseConnectionError:
    """Test suite for DatabaseConnectionError exception."""

    def test_inherits_from_api_error(self) -> None:
        """Verify DatabaseConnectionError inherits from APIError."""
        assert issubclass(DatabaseConnectionError, APIError)

    def test_stores_path_attribute(self) -> None:
        """Verify path attribute is stored."""
        error = DatabaseConnectionError(path="/path/to/db", reason="test")
        assert error.path == "/path/to/db"

    def test_stores_reason_attribute(self) -> None:
        """Verify reason attribute is stored."""
        error = DatabaseConnectionError(path="/path/to/db", reason="file not found")
        assert error.reason == "file not found"

    def test_formats_message_correctly(self) -> None:
        """Verify error message is formatted with path and reason."""
        error = DatabaseConnectionError(path="/db/file.duckdb", reason="locked")
        assert "/db/file.duckdb" in str(error)
        assert "locked" in str(error)

    def test_can_be_caught_as_api_error(self) -> None:
        """Verify can be caught using APIError handler."""
        with pytest.raises(APIError):
            raise DatabaseConnectionError(path="/path", reason="error")


class TestRecordNotFoundError:
    """Test suite for RecordNotFoundError exception."""

    def test_inherits_from_api_error(self) -> None:
        """Verify RecordNotFoundError inherits from APIError."""
        assert issubclass(RecordNotFoundError, APIError)

    def test_stores_entity_type_attribute(self) -> None:
        """Verify entity_type attribute is stored."""
        error = RecordNotFoundError(entity_type="Technology", identifier="rust")
        assert error.entity_type == "Technology"

    def test_stores_identifier_attribute(self) -> None:
        """Verify identifier attribute is stored."""
        error = RecordNotFoundError(entity_type="Technology", identifier="rust")
        assert error.identifier == "rust"

    def test_formats_message_correctly(self) -> None:
        """Verify error message includes entity type and identifier."""
        error = RecordNotFoundError(entity_type="Technology", identifier="rust")
        assert "Technology" in str(error)
        assert "rust" in str(error)
        assert "not found" in str(error)

    def test_can_be_caught_as_api_error(self) -> None:
        """Verify can be caught using APIError handler."""
        with pytest.raises(APIError):
            raise RecordNotFoundError(entity_type="User", identifier="123")


class TestQueryExecutionError:
    """Test suite for QueryExecutionError exception."""

    def test_inherits_from_api_error(self) -> None:
        """Verify QueryExecutionError inherits from APIError."""
        assert issubclass(QueryExecutionError, APIError)

    def test_stores_query_attribute(self) -> None:
        """Verify query attribute is stored."""
        error = QueryExecutionError(query="SELECT * FROM foo", reason="syntax error")
        assert error.query == "SELECT * FROM foo"

    def test_stores_reason_attribute(self) -> None:
        """Verify reason attribute is stored."""
        error = QueryExecutionError(query="SELECT 1", reason="timeout")
        assert error.reason == "timeout"

    def test_formats_message_correctly(self) -> None:
        """Verify error message includes reason."""
        error = QueryExecutionError(query="SELECT 1", reason="table not found")
        assert "table not found" in str(error)
        assert "Query execution failed" in str(error)

    def test_can_be_caught_as_api_error(self) -> None:
        """Verify can be caught using APIError handler."""
        with pytest.raises(APIError):
            raise QueryExecutionError(query="SELECT 1", reason="error")


class TestDataValidationError:
    """Test suite for DataValidationError exception."""

    def test_inherits_from_api_error(self) -> None:
        """Verify DataValidationError inherits from APIError."""
        assert issubclass(DataValidationError, APIError)

    def test_stores_model_name_attribute(self) -> None:
        """Verify model_name attribute is stored."""
        error = DataValidationError(model_name="TechnologyModel", reason="invalid")
        assert error.model_name == "TechnologyModel"

    def test_stores_reason_attribute(self) -> None:
        """Verify reason attribute is stored."""
        error = DataValidationError(model_name="Model", reason="missing field 'name'")
        assert error.reason == "missing field 'name'"

    def test_formats_message_correctly(self) -> None:
        """Verify error message includes model name and reason."""
        error = DataValidationError(model_name="TrendModel", reason="invalid date")
        assert "TrendModel" in str(error)
        assert "invalid date" in str(error)
        assert "Data validation failed" in str(error)

    def test_can_be_caught_as_api_error(self) -> None:
        """Verify can be caught using APIError handler."""
        with pytest.raises(APIError):
            raise DataValidationError(model_name="Model", reason="error")


class TestCacheConnectionError:
    """Test suite for CacheConnectionError exception."""

    def test_inherits_from_api_error(self) -> None:
        """Verify CacheConnectionError inherits from APIError."""
        assert issubclass(CacheConnectionError, APIError)

    def test_stores_reason_attribute(self) -> None:
        """Verify reason attribute is stored."""
        error = CacheConnectionError(reason="connection refused")
        assert error.reason == "connection refused"

    def test_stores_operation_attribute(self) -> None:
        """Verify operation attribute is stored."""
        error = CacheConnectionError(reason="timeout", operation="get")
        assert error.operation == "get"

    def test_default_operation_is_connect(self) -> None:
        """Verify default operation is 'connect'."""
        error = CacheConnectionError(reason="test")
        assert error.operation == "connect"

    def test_formats_message_correctly(self) -> None:
        """Verify error message includes operation and reason."""
        error = CacheConnectionError(reason="timeout", operation="set")
        assert "set" in str(error)
        assert "timeout" in str(error)
        assert "Cache" in str(error)

    def test_can_be_caught_as_api_error(self) -> None:
        """Verify can be caught using APIError handler."""
        with pytest.raises(APIError):
            raise CacheConnectionError(reason="error")


class TestExceptionHierarchy:
    """Test suite for the overall exception hierarchy."""

    def test_all_exceptions_inherit_from_api_error(self) -> None:
        """Verify all domain exceptions inherit from APIError."""
        exceptions = [
            CacheConnectionError,
            DatabaseConnectionError,
            RecordNotFoundError,
            QueryExecutionError,
            DataValidationError,
        ]
        for exc_class in exceptions:
            assert issubclass(exc_class, APIError)

    def test_all_exceptions_inherit_from_exception(self) -> None:
        """Verify all domain exceptions are proper Exceptions."""
        exceptions = [
            APIError,
            CacheConnectionError,
            DatabaseConnectionError,
            RecordNotFoundError,
            QueryExecutionError,
            DataValidationError,
        ]
        for exc_class in exceptions:
            assert issubclass(exc_class, Exception)
