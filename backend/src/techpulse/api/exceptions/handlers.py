"""Global exception handlers for FastAPI application.

This module provides exception handlers that transform domain exceptions
into RFC 7807 Problem Details responses with appropriate HTTP status codes.
"""

import structlog
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from techpulse.api.exceptions.domain import (
    APIError,
    DatabaseConnectionError,
    DataValidationError,
    QueryExecutionError,
    RecordNotFoundError,
)
from techpulse.api.schemas.errors import ERROR_TYPE_BASE, ProblemDetail

logger = structlog.get_logger(__name__)


async def database_connection_error_handler(
    request: Request, exc: DatabaseConnectionError
) -> JSONResponse:
    """Handle DatabaseConnectionError with 503 Service Unavailable.

    Args:
        request: The incoming request that triggered the error.
        exc: The DatabaseConnectionError exception.

    Returns:
        JSONResponse with RFC 7807 Problem Details and 503 status.
    """
    logger.error(
        "database_connection_error",
        path=exc.path,
        reason=exc.reason,
        request_path=str(request.url.path),
    )

    problem = ProblemDetail(
        type=f"{ERROR_TYPE_BASE}/database-connection-error",
        title="Service Unavailable",
        status=503,
        detail=f"Database connection failed: {exc.reason}",
        instance=str(request.url.path),
    )

    return JSONResponse(
        status_code=503,
        content=problem.model_dump(),
        media_type="application/problem+json",
    )


async def record_not_found_error_handler(
    request: Request, exc: RecordNotFoundError
) -> JSONResponse:
    """Handle RecordNotFoundError with 404 Not Found.

    Args:
        request: The incoming request that triggered the error.
        exc: The RecordNotFoundError exception.

    Returns:
        JSONResponse with RFC 7807 Problem Details and 404 status.
    """
    logger.warning(
        "record_not_found",
        entity_type=exc.entity_type,
        identifier=exc.identifier,
        request_path=str(request.url.path),
    )

    problem = ProblemDetail(
        type=f"{ERROR_TYPE_BASE}/record-not-found",
        title="Record Not Found",
        status=404,
        detail=f"{exc.entity_type} with identifier '{exc.identifier}' does not exist.",
        instance=str(request.url.path),
    )

    return JSONResponse(
        status_code=404,
        content=problem.model_dump(),
        media_type="application/problem+json",
    )


async def query_execution_error_handler(
    request: Request, exc: QueryExecutionError
) -> JSONResponse:
    """Handle QueryExecutionError with 500 Internal Server Error.

    Args:
        request: The incoming request that triggered the error.
        exc: The QueryExecutionError exception.

    Returns:
        JSONResponse with RFC 7807 Problem Details and 500 status.
    """
    logger.error(
        "query_execution_error",
        query=exc.query,
        reason=exc.reason,
        request_path=str(request.url.path),
    )

    problem = ProblemDetail(
        type=f"{ERROR_TYPE_BASE}/query-execution-error",
        title="Internal Server Error",
        status=500,
        detail="An error occurred while processing your request.",
        instance=str(request.url.path),
    )

    return JSONResponse(
        status_code=500,
        content=problem.model_dump(),
        media_type="application/problem+json",
    )


async def data_validation_error_handler(
    request: Request, exc: DataValidationError
) -> JSONResponse:
    """Handle DataValidationError with 422 Unprocessable Entity.

    Args:
        request: The incoming request that triggered the error.
        exc: The DataValidationError exception.

    Returns:
        JSONResponse with RFC 7807 Problem Details and 422 status.
    """
    logger.error(
        "data_validation_error",
        model_name=exc.model_name,
        reason=exc.reason,
        request_path=str(request.url.path),
    )

    problem = ProblemDetail(
        type=f"{ERROR_TYPE_BASE}/data-validation-error",
        title="Unprocessable Entity",
        status=422,
        detail=f"Data validation failed: {exc.reason}",
        instance=str(request.url.path),
    )

    return JSONResponse(
        status_code=422,
        content=problem.model_dump(),
        media_type="application/problem+json",
    )


async def api_error_handler(request: Request, exc: APIError) -> JSONResponse:
    """Handle generic APIError with 500 Internal Server Error.

    Catches any APIError subclass not handled by specific handlers.

    Args:
        request: The incoming request that triggered the error.
        exc: The APIError exception.

    Returns:
        JSONResponse with RFC 7807 Problem Details and 500 status.
    """
    logger.error(
        "unhandled_api_error",
        error_type=type(exc).__name__,
        message=str(exc),
        request_path=str(request.url.path),
    )

    problem = ProblemDetail(
        type=f"{ERROR_TYPE_BASE}/internal-error",
        title="Internal Server Error",
        status=500,
        detail="An unexpected error occurred.",
        instance=str(request.url.path),
    )

    return JSONResponse(
        status_code=500,
        content=problem.model_dump(),
        media_type="application/problem+json",
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle any unhandled exception with 500 Internal Server Error.

    Provides a catch-all handler for unexpected exceptions to ensure
    all errors return consistent RFC 7807 format.

    Args:
        request: The incoming request that triggered the error.
        exc: The unhandled exception.

    Returns:
        JSONResponse with RFC 7807 Problem Details and 500 status.
    """
    logger.exception(
        "unhandled_exception",
        error_type=type(exc).__name__,
        message=str(exc),
        request_path=str(request.url.path),
    )

    problem = ProblemDetail(
        type=f"{ERROR_TYPE_BASE}/internal-error",
        title="Internal Server Error",
        status=500,
        detail="An unexpected error occurred.",
        instance=str(request.url.path),
    )

    return JSONResponse(
        status_code=500,
        content=problem.model_dump(),
        media_type="application/problem+json",
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Register all exception handlers with the FastAPI application.

    Call this function during application startup to register all
    domain exception handlers and the catch-all handler.

    Args:
        app: The FastAPI application instance.
    """
    app.add_exception_handler(
        DatabaseConnectionError,
        database_connection_error_handler,  # type: ignore[arg-type]
    )
    app.add_exception_handler(
        RecordNotFoundError,
        record_not_found_error_handler,  # type: ignore[arg-type]
    )
    app.add_exception_handler(
        QueryExecutionError,
        query_execution_error_handler,  # type: ignore[arg-type]
    )
    app.add_exception_handler(
        DataValidationError,
        data_validation_error_handler,  # type: ignore[arg-type]
    )
    app.add_exception_handler(
        APIError,
        api_error_handler,  # type: ignore[arg-type]
    )
    app.add_exception_handler(Exception, unhandled_exception_handler)
