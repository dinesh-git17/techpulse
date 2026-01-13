"""API exception hierarchy for domain-specific error handling."""

from techpulse.api.exceptions.domain import (
    APIError,
    DatabaseConnectionError,
    DataValidationError,
    QueryExecutionError,
    RecordNotFoundError,
)
from techpulse.api.exceptions.handlers import register_exception_handlers

__all__ = [
    "APIError",
    "DatabaseConnectionError",
    "DataValidationError",
    "QueryExecutionError",
    "RecordNotFoundError",
    "register_exception_handlers",
]
