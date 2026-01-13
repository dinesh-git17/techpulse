"""TechPulse API entry point.

This module initializes the FastAPI application with lifespan management,
configures logging based on environment settings, manages database
connectivity, CORS middleware, and API versioning.
"""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Union

import structlog
from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware

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

# Route modules are imported after v1_router definition to register endpoints

v1_router = APIRouter(prefix="/api/v1")

# Import route modules to register endpoints with v1_router.
# These imports must occur after v1_router is defined.
from techpulse.api.routes import technologies as _technologies_routes  # noqa: F401, E402
from techpulse.api.routes import trends as _trends_routes  # noqa: F401, E402


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
        cors_origins=settings.get_cors_origins_list(),
    )

    init_session_manager(settings.db_path)

    yield

    close_session_manager()
    logger.info("application_shutdown")


def _health() -> dict[str, Union[str, bool]]:
    """Return API health status including database connectivity.

    Performs a health check on the database connection by executing
    SELECT 1. Returns db_connected status based on the result.

    This endpoint is outside the versioned API prefix for infrastructure
    monitoring tools that expect a standard health check path.

    Returns:
        Dictionary containing status, system name, and db_connected flag.
    """
    try:
        manager = get_session_manager()
        db_connected = manager.health_check()
    except DatabaseConnectionError:
        db_connected = False

    return {"status": "ok", "system": "TechPulse", "db_connected": db_connected}


def create_app() -> FastAPI:
    """Create and configure the FastAPI application.

    Initializes the application with lifespan management, CORS middleware,
    exception handlers, versioned routing, and the health endpoint.

    Returns:
        Configured FastAPI application instance.
    """
    settings = get_settings()

    application = FastAPI(
        title="TechPulse API",
        version="1.0.0",
        lifespan=lifespan,
    )

    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.get_cors_origins_list(),
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )

    register_exception_handlers(application)

    application.include_router(v1_router)

    application.get("/health")(_health)

    return application


app = create_app()

health = _health
