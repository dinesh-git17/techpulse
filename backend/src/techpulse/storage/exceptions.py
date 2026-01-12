"""Exception hierarchy for DuckDB storage layer.

This module defines the structured exception types used by the storage
components (DuckDBManager, DuckDBStore) to communicate failure modes
to callers. The hierarchy enables precise error handling based on
failure category.
"""


class StorageError(Exception):
    """Base exception for all storage layer errors.

    All exceptions raised by storage components inherit from this class,
    allowing callers to catch all storage errors with a single handler.
    """


class StorageConnectionError(StorageError):
    """Raised when database connection cannot be established.

    This includes failures to open or create the database file, lock
    acquisition failures after exhausting retries, and other connection-layer
    problems.

    Attributes:
        path: The database file path that failed to connect.
        reason: A descriptive explanation of the connection failure.
    """

    def __init__(self, path: str, reason: str) -> None:
        """Initialize the connection error with path and reason.

        Args:
            path: The filesystem path to the database file.
            reason: A human-readable description of why connection failed.
        """
        self.path = path
        self.reason = reason
        super().__init__(f"Failed to connect to database at '{path}': {reason}")


class InvalidPayloadError(StorageError):
    """Raised when JSON payload fails DuckDB syntax validation.

    This indicates the payload provided for insertion is not valid JSON
    or cannot be processed by DuckDB's JSON type. These errors are not
    retryable without correcting the payload.

    Attributes:
        payload_index: The zero-based index of the invalid payload in the batch.
        reason: A descriptive explanation of the validation failure.
    """

    def __init__(self, payload_index: int, reason: str) -> None:
        """Initialize the payload error with index and reason.

        Args:
            payload_index: The index of the invalid item in the batch.
            reason: A human-readable description of the validation failure.
        """
        self.payload_index = payload_index
        self.reason = reason
        super().__init__(f"Invalid payload at index {payload_index}: {reason}")


class TransactionError(StorageError):
    """Raised when a batch transaction fails to commit.

    This indicates the database transaction could not be completed,
    and all changes within the transaction have been rolled back.

    Attributes:
        operation: The operation that was being performed (e.g., 'insert').
        reason: A descriptive explanation of the transaction failure.
    """

    def __init__(self, operation: str, reason: str) -> None:
        """Initialize the transaction error with operation and reason.

        Args:
            operation: The database operation that failed.
            reason: A human-readable description of why the transaction failed.
        """
        self.operation = operation
        self.reason = reason
        super().__init__(f"Transaction failed during '{operation}': {reason}")
