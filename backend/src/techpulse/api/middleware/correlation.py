"""Request correlation middleware for distributed tracing.

This module provides middleware that generates or propagates request IDs
for correlation across logs and services, and binds request context to
the structlog context for consistent logging.
"""

import time
import uuid

import structlog
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp

logger = structlog.get_logger(__name__)

REQUEST_ID_HEADER = "X-Request-ID"


class CorrelationMiddleware(BaseHTTPMiddleware):
    """Middleware for request correlation and context logging.

    Generates a unique request ID (UUID v4) for each incoming request if not
    provided in the X-Request-ID header. Binds request metadata to the
    structlog context for consistent logging across the request lifecycle.

    Attributes:
        app: The ASGI application to wrap.
    """

    def __init__(self, app: ASGIApp) -> None:
        """Initialize the correlation middleware.

        Args:
            app: The ASGI application to wrap.
        """
        super().__init__(app)

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        """Process request with correlation ID and context binding.

        Extracts or generates a request ID, binds request metadata to the
        structlog context, processes the request, and logs completion with
        timing information.

        Args:
            request: The incoming HTTP request.
            call_next: Callable to invoke the next middleware or route handler.

        Returns:
            Response with X-Request-ID header included.
        """
        start_time = time.perf_counter()

        request_id = _extract_or_generate_request_id(request)
        remote_ip = _get_client_ip(request)
        user_agent = request.headers.get("user-agent", "")

        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(
            request_id=request_id,
            remote_ip=remote_ip,
            user_agent=user_agent,
            path=request.url.path,
            method=request.method,
        )

        response = await call_next(request)

        duration_ms = (time.perf_counter() - start_time) * 1000

        logger.info(
            "request_completed",
            status_code=response.status_code,
            duration_ms=round(duration_ms, 2),
        )

        response.headers[REQUEST_ID_HEADER] = request_id

        return response


def _extract_or_generate_request_id(request: Request) -> str:
    """Extract request ID from header or generate a new UUID v4.

    Args:
        request: The incoming HTTP request.

    Returns:
        Request ID string, either from header or newly generated.
    """
    request_id = request.headers.get(REQUEST_ID_HEADER)
    if request_id:
        return request_id
    return str(uuid.uuid4())


def _get_client_ip(request: Request) -> str:
    """Extract client IP address from request.

    Checks X-Forwarded-For header first for proxied requests, then falls
    back to the direct client host.

    Args:
        request: The incoming HTTP request.

    Returns:
        Client IP address string, or empty string if unavailable.
    """
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()

    if request.client:
        return request.client.host

    return ""
