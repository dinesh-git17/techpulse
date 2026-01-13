"""Domain exception classes for the API layer.

This module defines the exception hierarchy for API-layer errors.
These exceptions are caught by global handlers and transformed into
RFC 7807 Problem Details responses.
"""


class APIError(Exception):
    """Base exception for all API layer errors.

    All domain exceptions inherit from this class, allowing callers
    to catch all API errors with a single handler.
    """


class DatabaseConnectionError(APIError):
    """Raised when database connection cannot be established or is lost.

    This includes failures to open the database file, missing database
    files, and connection timeouts. Maps to HTTP 503 Service Unavailable.

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
        super().__init__(f"Database connection failed at '{path}': {reason}")


class RecordNotFoundError(APIError):
    """Raised when a requested entity does not exist in the database.

    Used by DAOs when a query for a specific record returns no results.
    Maps to HTTP 404 Not Found.

    Attributes:
        entity_type: The type of entity that was not found (e.g., "Technology").
        identifier: The identifier used to look up the entity.
    """

    def __init__(self, entity_type: str, identifier: str) -> None:
        """Initialize the not found error with entity details.

        Args:
            entity_type: The type of entity that was requested.
            identifier: The key or ID used to search for the entity.
        """
        self.entity_type = entity_type
        self.identifier = identifier
        super().__init__(f"{entity_type} with identifier '{identifier}' not found")


class QueryExecutionError(APIError):
    """Raised when SQL query execution fails.

    This covers syntax errors, timeouts, and other database-level
    execution failures. Maps to HTTP 500 Internal Server Error.

    Attributes:
        query: A sanitized representation of the failed query.
        reason: A descriptive explanation of the execution failure.
    """

    def __init__(self, query: str, reason: str) -> None:
        """Initialize the execution error with query and reason.

        Args:
            query: The SQL query that failed (may be truncated for safety).
            reason: A human-readable description of why execution failed.
        """
        self.query = query
        self.reason = reason
        super().__init__(f"Query execution failed: {reason}")


class DataValidationError(APIError):
    """Raised when database results fail Pydantic model validation.

    This indicates a schema mismatch between the database and the
    expected domain model. Maps to HTTP 422 Unprocessable Entity.

    Attributes:
        model_name: The name of the Pydantic model that failed validation.
        reason: A descriptive explanation of the validation failure.
    """

    def __init__(self, model_name: str, reason: str) -> None:
        """Initialize the validation error with model name and reason.

        Args:
            model_name: The name of the model that could not be populated.
            reason: A human-readable description of the validation failure.
        """
        self.model_name = model_name
        self.reason = reason
        super().__init__(f"Data validation failed for {model_name}: {reason}")
