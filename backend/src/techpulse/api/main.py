"""TechPulse API entry point.

This module initializes the FastAPI application with lifespan management,
configures logging based on environment settings, manages database
connectivity, and provides the health check endpoint.
"""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Union

import structlog
from fastapi import FastAPI

from techpulse.api.core.config import get_settings
from techpulse.api.core.logging import configure_logging
from techpulse.api.db.manager import (
    close_session_manager,
    get_session_manager,
    init_session_manager,
)
from techpulse.api.exceptions.domain import DatabaseConnectionError
from techpulse.api.exceptions.handlers import register_exception_handlers

logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(application: FastAPI) -> AsyncGenerator[None, None]:
    """Manage application startup and shutdown lifecycle.

    Configures logging and establishes database connection on startup.
    Closes database connection on shutdown.

    Args:
        application: The FastAPI application instance.

    Yields:
        None after startup completes, allowing the application to run.

    Raises:
        DatabaseConnectionError: If database connection fails during startup.
    """
    settings = get_settings()
    configure_logging(settings.log_format)

    logger.info(
        "application_startup",
        host=settings.api_host,
        port=settings.api_port,
        log_format=settings.log_format,
        db_path=str(settings.db_path),
    )

    init_session_manager(settings.db_path)

    yield

    close_session_manager()
    logger.info("application_shutdown")


app = FastAPI(
    title="TechPulse API",
    lifespan=lifespan,
)

register_exception_handlers(app)


@app.get("/health")
def health() -> dict[str, Union[str, bool]]:
    """Return API health status including database connectivity.

    Performs a health check on the database connection by executing
    SELECT 1. Returns db_connected status based on the result.

    Returns:
        Dictionary containing status, system name, and db_connected flag.
    """
    try:
        manager = get_session_manager()
        db_connected = manager.health_check()
    except DatabaseConnectionError:
        db_connected = False

    return {"status": "ok", "system": "TechPulse", "db_connected": db_connected}
