"""Exception hierarchy for Hacker News API client.

This module defines the structured exception types used by the HackerNewsClient
to communicate failure modes to callers. The hierarchy enables precise error
handling based on failure category.
"""


class HackerNewsError(Exception):
    """Base exception for all Hacker News client errors.

    All exceptions raised by HackerNewsClient inherit from this class,
    allowing callers to catch all client errors with a single handler.
    """


class HackerNewsNetworkError(HackerNewsError):
    """Raised when a transient network connectivity issue occurs.

    This includes connection timeouts, DNS failures, and other network-layer
    problems. These errors are typically retryable.
    """


class HackerNewsAPIError(HackerNewsError):
    """Raised when the Hacker News API returns a non-200 HTTP status.

    Attributes:
        status_code: The HTTP status code returned by the API.
        message: A descriptive error message.
    """

    def __init__(self, status_code: int, message: str) -> None:
        """Initialize the API error with status code and message.

        Args:
            status_code: The HTTP status code from the API response.
            message: A human-readable error description.
        """
        self.status_code = status_code
        self.message = message
        super().__init__(f"HTTP {status_code}: {message}")


class HackerNewsDataError(HackerNewsError):
    """Raised when API response data fails Pydantic validation.

    This indicates the API returned data that does not conform to the
    expected schema. These errors are not retryable.
    """


class HackerNewsMaxRetriesError(HackerNewsError):
    """Raised when all retry attempts have been exhausted.

    This wraps the underlying error that caused the final retry failure.

    Attributes:
        attempts: The total number of attempts made before giving up.
        last_error: The exception from the final failed attempt.
    """

    def __init__(self, attempts: int, last_error: Exception) -> None:
        """Initialize with retry count and the final error.

        Args:
            attempts: Total number of retry attempts made.
            last_error: The exception raised on the final attempt.
        """
        self.attempts = attempts
        self.last_error = last_error
        super().__init__(f"Failed after {attempts} attempts. Last error: {last_error}")
