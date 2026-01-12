"""Unit tests for Hacker News exception hierarchy."""

from techpulse.source.hn.errors import (
    HackerNewsAPIError,
    HackerNewsDataError,
    HackerNewsError,
    HackerNewsMaxRetriesError,
    HackerNewsNetworkError,
)


class TestExceptionHierarchy:
    """Test suite for exception class hierarchy."""

    def test_network_error_inherits_from_base(self) -> None:
        """Verify HackerNewsNetworkError inherits from HackerNewsError."""
        error = HackerNewsNetworkError("Connection failed")
        assert isinstance(error, HackerNewsError)
        assert isinstance(error, Exception)

    def test_api_error_inherits_from_base(self) -> None:
        """Verify HackerNewsAPIError inherits from HackerNewsError."""
        error = HackerNewsAPIError(404, "Not found")
        assert isinstance(error, HackerNewsError)
        assert isinstance(error, Exception)

    def test_data_error_inherits_from_base(self) -> None:
        """Verify HackerNewsDataError inherits from HackerNewsError."""
        error = HackerNewsDataError("Validation failed")
        assert isinstance(error, HackerNewsError)
        assert isinstance(error, Exception)

    def test_max_retries_error_inherits_from_base(self) -> None:
        """Verify HackerNewsMaxRetriesError inherits from HackerNewsError."""
        error = HackerNewsMaxRetriesError(5, Exception("Network timeout"))
        assert isinstance(error, HackerNewsError)
        assert isinstance(error, Exception)


class TestHackerNewsAPIError:
    """Test suite for HackerNewsAPIError."""

    def test_stores_status_code(self) -> None:
        """Verify status_code attribute is set."""
        error = HackerNewsAPIError(404, "Resource not found")
        assert error.status_code == 404

    def test_stores_message(self) -> None:
        """Verify message attribute is set."""
        error = HackerNewsAPIError(500, "Internal server error")
        assert error.message == "Internal server error"

    def test_string_representation(self) -> None:
        """Verify error string includes status code and message."""
        error = HackerNewsAPIError(403, "Forbidden")
        error_str = str(error)
        assert "403" in error_str
        assert "Forbidden" in error_str


class TestHackerNewsMaxRetriesError:
    """Test suite for HackerNewsMaxRetriesError."""

    def test_stores_attempts(self) -> None:
        """Verify attempts attribute is set."""
        error = HackerNewsMaxRetriesError(5, Exception("Timeout"))
        assert error.attempts == 5

    def test_stores_last_error(self) -> None:
        """Verify last_error attribute is set."""
        original_error = ValueError("Original error")
        error = HackerNewsMaxRetriesError(3, original_error)
        assert error.last_error is original_error

    def test_string_representation(self) -> None:
        """Verify error string includes attempt count and last error."""
        original_error = ConnectionError("Network unreachable")
        error = HackerNewsMaxRetriesError(5, original_error)
        error_str = str(error)
        assert "5" in error_str
        assert "Network unreachable" in error_str


class TestCatchAllHandler:
    """Test suite verifying base class can catch all client errors."""

    def test_base_class_catches_network_error(self) -> None:
        """Verify HackerNewsError catches HackerNewsNetworkError."""
        try:
            raise HackerNewsNetworkError("Connection failed")
        except HackerNewsError:
            pass

    def test_base_class_catches_api_error(self) -> None:
        """Verify HackerNewsError catches HackerNewsAPIError."""
        try:
            raise HackerNewsAPIError(500, "Server error")
        except HackerNewsError:
            pass

    def test_base_class_catches_data_error(self) -> None:
        """Verify HackerNewsError catches HackerNewsDataError."""
        try:
            raise HackerNewsDataError("Invalid JSON")
        except HackerNewsError:
            pass

    def test_base_class_catches_max_retries_error(self) -> None:
        """Verify HackerNewsError catches HackerNewsMaxRetriesError."""
        try:
            raise HackerNewsMaxRetriesError(5, Exception("Timeout"))
        except HackerNewsError:
            pass
