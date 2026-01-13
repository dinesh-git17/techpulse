"""Health check endpoints for liveness and readiness probes.

This module provides deep health check endpoints that verify connectivity
to critical dependencies (DuckDB, Redis) with strict timeouts. These
endpoints are designed for use by Kubernetes/load balancers to determine
whether the service can receive traffic.
"""

import time
from concurrent.futures import (
    Future,
    ThreadPoolExecutor,
    TimeoutError as FuturesTimeoutError,
)
from typing import Callable, Optional, Union

import structlog
from fastapi import APIRouter, Response, status
from pydantic import BaseModel, Field

from techpulse.api.cache.service import CacheService, get_cache_service
from techpulse.api.db.manager import DatabaseSessionManager, get_session_manager
from techpulse.api.exceptions.domain import DatabaseConnectionError

logger = structlog.get_logger(__name__)

health_router = APIRouter(prefix="/health", tags=["health"])

HEALTH_CHECK_TIMEOUT_SECONDS: float = 2.0


class ComponentHealthUp(BaseModel):
    """Health status for a component that is operational.

    Attributes:
        status: Always "up" for healthy components.
        latency_ms: Time taken to complete the health check in milliseconds.
    """

    status: str = Field(
        default="up",
        description="Component status indicator.",
    )
    latency_ms: float = Field(
        ge=0,
        description="Health check latency in milliseconds.",
    )


class ComponentHealthDown(BaseModel):
    """Health status for a component that is not operational.

    Attributes:
        status: Always "down" for unhealthy components.
        error: Description of the failure reason.
    """

    status: str = Field(
        default="down",
        description="Component status indicator.",
    )
    error: str = Field(
        description="Error message describing the failure.",
    )


ComponentHealth = Union[ComponentHealthUp, ComponentHealthDown]


class ComponentsHealth(BaseModel):
    """Health status for all system components.

    Attributes:
        database: DuckDB connection health status.
        cache: Redis cache connection health status.
    """

    database: ComponentHealth = Field(
        description="DuckDB database connectivity status.",
    )
    cache: ComponentHealth = Field(
        description="Redis cache connectivity status.",
    )


class LivenessResponse(BaseModel):
    """Response model for liveness probe.

    Attributes:
        status: Always "ok" when the process is running.
    """

    status: str = Field(
        default="ok",
        description="Liveness status indicator.",
    )


class ReadinessResponse(BaseModel):
    """Response model for readiness probe.

    Attributes:
        status: "healthy" when all dependencies are available, "unhealthy" otherwise.
        components: Individual health status for each dependency.
    """

    status: str = Field(
        description="Overall readiness status: 'healthy' or 'unhealthy'.",
    )
    components: ComponentsHealth = Field(
        description="Health status for each system component.",
    )


def _check_database_health(manager: DatabaseSessionManager) -> ComponentHealth:
    """Execute database health check with latency measurement.

    Runs SELECT 1 against DuckDB and measures response time.

    Args:
        manager: The database session manager instance.

    Returns:
        ComponentHealthUp with latency if successful, ComponentHealthDown
        with error message if failed.
    """
    start_time = time.perf_counter()
    try:
        if manager.health_check():
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            return ComponentHealthUp(latency_ms=round(elapsed_ms, 2))
        return ComponentHealthDown(error="Health check returned false")
    except Exception as exc:
        return ComponentHealthDown(error=str(exc))


def _check_cache_health(cache_service: Optional[CacheService]) -> ComponentHealth:
    """Execute cache health check with latency measurement.

    Runs PING against Redis and measures response time.

    Args:
        cache_service: The cache service instance, or None if not configured.

    Returns:
        ComponentHealthUp with latency if successful, ComponentHealthDown
        with error message if failed or not configured.
    """
    if cache_service is None:
        return ComponentHealthDown(error="Cache service not configured")

    start_time = time.perf_counter()
    try:
        if cache_service.health_check():
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            return ComponentHealthUp(latency_ms=round(elapsed_ms, 2))
        return ComponentHealthDown(error="Health check returned false")
    except Exception as exc:
        return ComponentHealthDown(error=str(exc))


def _execute_with_timeout(
    check_func: Callable[[], ComponentHealth],
    timeout_seconds: float,
) -> ComponentHealth:
    """Execute a health check function with timeout enforcement.

    Uses a thread pool to enforce strict timeout boundaries on health checks.
    If the check exceeds the timeout, returns a failure status immediately
    rather than hanging.

    Args:
        check_func: Zero-argument callable that returns ComponentHealth.
        timeout_seconds: Maximum time to wait for the check to complete.

    Returns:
        ComponentHealth from the check function, or ComponentHealthDown
        if timeout is exceeded.
    """
    with ThreadPoolExecutor(max_workers=1) as executor:
        future: Future[ComponentHealth] = executor.submit(check_func)
        try:
            result: ComponentHealth = future.result(timeout=timeout_seconds)
            return result
        except FuturesTimeoutError:
            return ComponentHealthDown(
                error=f"Health check timed out after {timeout_seconds}s"
            )


@health_router.get(
    "/live",
    response_model=LivenessResponse,
    summary="Liveness probe",
    description="Returns 200 OK if the FastAPI process is running. "
    "Used by orchestrators to determine if the container needs to be restarted.",
)
def liveness() -> LivenessResponse:
    """Return liveness status for the API process.

    This endpoint confirms the FastAPI application is responding to HTTP
    requests. It does not check dependencies - use /health/ready for that.

    Returns:
        LivenessResponse with status "ok".
    """
    return LivenessResponse(status="ok")


@health_router.get(
    "/ready",
    response_model=ReadinessResponse,
    summary="Readiness probe",
    description="Returns 200 OK if all critical dependencies (DuckDB, Redis) "
    "are healthy. Returns 503 if any dependency is unavailable. "
    "Each health check enforces a 2-second timeout.",
    responses={
        200: {
            "description": "All dependencies healthy",
            "content": {
                "application/json": {
                    "example": {
                        "status": "healthy",
                        "components": {
                            "database": {"status": "up", "latency_ms": 12.5},
                            "cache": {"status": "up", "latency_ms": 2.3},
                        },
                    }
                }
            },
        },
        503: {
            "description": "One or more dependencies unhealthy",
            "content": {
                "application/json": {
                    "example": {
                        "status": "unhealthy",
                        "components": {
                            "database": {"status": "up", "latency_ms": 15.0},
                            "cache": {"status": "down", "error": "Connection refused"},
                        },
                    }
                }
            },
        },
    },
)
def readiness(response: Response) -> ReadinessResponse:
    """Return readiness status based on dependency health checks.

    Executes health checks against DuckDB (SELECT 1) and Redis (PING) with
    strict 2-second timeouts. If any critical dependency fails, the endpoint
    returns 503 Service Unavailable to signal that the service should not
    receive traffic.

    Args:
        response: FastAPI response object for setting status code.

    Returns:
        ReadinessResponse with overall status and per-component health details.
    """
    try:
        manager = get_session_manager()
        database_health = _execute_with_timeout(
            lambda: _check_database_health(manager),
            HEALTH_CHECK_TIMEOUT_SECONDS,
        )
    except DatabaseConnectionError as exc:
        database_health = ComponentHealthDown(error=str(exc))

    cache_service = get_cache_service()
    cache_health = _execute_with_timeout(
        lambda: _check_cache_health(cache_service),
        HEALTH_CHECK_TIMEOUT_SECONDS,
    )

    database_is_healthy = database_health.status == "up"
    cache_is_healthy = cache_health.status == "up"
    all_healthy = database_is_healthy and cache_is_healthy

    overall_status = "healthy" if all_healthy else "unhealthy"

    if not all_healthy:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        logger.warning(
            "readiness_check_failed",
            database_status=database_health.status,
            cache_status=cache_health.status,
        )
    else:
        database_latency: Optional[float] = (
            database_health.latency_ms
            if isinstance(database_health, ComponentHealthUp)
            else None
        )
        cache_latency: Optional[float] = (
            cache_health.latency_ms
            if isinstance(cache_health, ComponentHealthUp)
            else None
        )
        logger.info(
            "readiness_check_passed",
            database_latency_ms=database_latency,
            cache_latency_ms=cache_latency,
        )

    return ReadinessResponse(
        status=overall_status,
        components=ComponentsHealth(
            database=database_health,
            cache=cache_health,
        ),
    )
