"""Unit tests for correlation middleware."""

import uuid
from io import StringIO
from typing import Generator

import pytest
import structlog
from fastapi import FastAPI
from fastapi.testclient import TestClient

from techpulse.api.middleware.correlation import (
    REQUEST_ID_HEADER,
    CorrelationMiddleware,
    _extract_or_generate_request_id,
    _get_client_ip,
)


@pytest.fixture
def app() -> FastAPI:
    """Create a test FastAPI application with correlation middleware."""
    application = FastAPI()
    application.add_middleware(CorrelationMiddleware)

    @application.get("/test")
    def test_endpoint() -> dict[str, str]:
        return {"status": "ok"}

    @application.get("/log-test")
    def log_test_endpoint() -> dict[str, str]:
        logger = structlog.get_logger()
        logger.info("test_log_event", custom_field="test_value")
        return {"status": "ok"}

    return application


@pytest.fixture
def client(app: FastAPI) -> TestClient:
    """Create a test client for the application."""
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_structlog() -> Generator[None, None, None]:
    """Reset structlog contextvars after each test."""
    yield
    structlog.contextvars.clear_contextvars()


class TestRequestIdGeneration:
    """Test suite for X-Request-ID generation and propagation."""

    def test_generates_uuid_when_no_header_present(self, client: TestClient) -> None:
        """Verify middleware generates UUID v4 when no X-Request-ID header."""
        response = client.get("/test")

        assert response.status_code == 200
        assert REQUEST_ID_HEADER in response.headers

        request_id = response.headers[REQUEST_ID_HEADER]
        parsed_uuid = uuid.UUID(request_id)
        assert parsed_uuid.version == 4

    def test_accepts_incoming_request_id(self, client: TestClient) -> None:
        """Verify middleware uses incoming X-Request-ID header."""
        custom_id = "custom-request-id-12345"
        response = client.get("/test", headers={REQUEST_ID_HEADER: custom_id})

        assert response.status_code == 200
        assert response.headers[REQUEST_ID_HEADER] == custom_id

    def test_returns_request_id_in_response_headers(self, client: TestClient) -> None:
        """Verify X-Request-ID is always included in response headers."""
        response = client.get("/test")

        assert REQUEST_ID_HEADER in response.headers
        assert len(response.headers[REQUEST_ID_HEADER]) > 0

    def test_each_request_gets_unique_id(self, client: TestClient) -> None:
        """Verify each request without header gets a unique ID."""
        response1 = client.get("/test")
        response2 = client.get("/test")

        id1 = response1.headers[REQUEST_ID_HEADER]
        id2 = response2.headers[REQUEST_ID_HEADER]

        assert id1 != id2


class TestExtractOrGenerateRequestId:
    """Test suite for _extract_or_generate_request_id function."""

    def test_returns_header_value_when_present(self) -> None:
        """Verify function returns header value when X-Request-ID present."""
        from starlette.testclient import TestClient as StarletteClient
        from starlette.applications import Starlette
        from starlette.requests import Request
        from starlette.responses import PlainTextResponse
        from starlette.routing import Route

        captured_request_id: str = ""

        async def capture_endpoint(request: Request) -> PlainTextResponse:
            nonlocal captured_request_id
            captured_request_id = _extract_or_generate_request_id(request)
            return PlainTextResponse("ok")

        app = Starlette(routes=[Route("/", capture_endpoint)])
        client = StarletteClient(app)

        client.get("/", headers={REQUEST_ID_HEADER: "test-id-123"})
        assert captured_request_id == "test-id-123"

    def test_generates_uuid_when_header_missing(self) -> None:
        """Verify function generates UUID when header missing."""
        from starlette.testclient import TestClient as StarletteClient
        from starlette.applications import Starlette
        from starlette.requests import Request
        from starlette.responses import PlainTextResponse
        from starlette.routing import Route

        captured_request_id: str = ""

        async def capture_endpoint(request: Request) -> PlainTextResponse:
            nonlocal captured_request_id
            captured_request_id = _extract_or_generate_request_id(request)
            return PlainTextResponse("ok")

        app = Starlette(routes=[Route("/", capture_endpoint)])
        client = StarletteClient(app)

        client.get("/")
        parsed_uuid = uuid.UUID(captured_request_id)
        assert parsed_uuid.version == 4


class TestGetClientIp:
    """Test suite for _get_client_ip function."""

    def test_returns_x_forwarded_for_first_ip(self) -> None:
        """Verify function returns first IP from X-Forwarded-For header."""
        from starlette.testclient import TestClient as StarletteClient
        from starlette.applications import Starlette
        from starlette.requests import Request
        from starlette.responses import PlainTextResponse
        from starlette.routing import Route

        captured_ip: str = ""

        async def capture_endpoint(request: Request) -> PlainTextResponse:
            nonlocal captured_ip
            captured_ip = _get_client_ip(request)
            return PlainTextResponse("ok")

        app = Starlette(routes=[Route("/", capture_endpoint)])
        client = StarletteClient(app)

        client.get("/", headers={"x-forwarded-for": "203.0.113.195, 70.41.3.18"})
        assert captured_ip == "203.0.113.195"

    def test_returns_client_host_when_no_forwarded_header(self) -> None:
        """Verify function returns client host when X-Forwarded-For missing."""
        from starlette.testclient import TestClient as StarletteClient
        from starlette.applications import Starlette
        from starlette.requests import Request
        from starlette.responses import PlainTextResponse
        from starlette.routing import Route

        captured_ip: str = ""

        async def capture_endpoint(request: Request) -> PlainTextResponse:
            nonlocal captured_ip
            captured_ip = _get_client_ip(request)
            return PlainTextResponse("ok")

        app = Starlette(routes=[Route("/", capture_endpoint)])
        client = StarletteClient(app)

        client.get("/")
        assert captured_ip == "testclient"


class TestContextBinding:
    """Test suite for structlog context binding."""

    def test_binds_request_id_to_context(self, client: TestClient) -> None:
        """Verify request_id is bound to structlog context."""
        output = StringIO()
        structlog.configure(
            processors=[
                structlog.contextvars.merge_contextvars,
                structlog.processors.JSONRenderer(),
            ],
            wrapper_class=structlog.make_filtering_bound_logger(0),
            context_class=dict,
            logger_factory=structlog.PrintLoggerFactory(output),
            cache_logger_on_first_use=False,
        )

        custom_id = "context-test-id"
        client.get("/log-test", headers={REQUEST_ID_HEADER: custom_id})

        log_output = output.getvalue()
        assert custom_id in log_output

    def test_binds_path_to_context(self, client: TestClient) -> None:
        """Verify path is bound to structlog context."""
        output = StringIO()
        structlog.configure(
            processors=[
                structlog.contextvars.merge_contextvars,
                structlog.processors.JSONRenderer(),
            ],
            wrapper_class=structlog.make_filtering_bound_logger(0),
            context_class=dict,
            logger_factory=structlog.PrintLoggerFactory(output),
            cache_logger_on_first_use=False,
        )

        client.get("/log-test")

        log_output = output.getvalue()
        assert "/log-test" in log_output

    def test_binds_method_to_context(self, client: TestClient) -> None:
        """Verify method is bound to structlog context."""
        output = StringIO()
        structlog.configure(
            processors=[
                structlog.contextvars.merge_contextvars,
                structlog.processors.JSONRenderer(),
            ],
            wrapper_class=structlog.make_filtering_bound_logger(0),
            context_class=dict,
            logger_factory=structlog.PrintLoggerFactory(output),
            cache_logger_on_first_use=False,
        )

        client.get("/log-test")

        log_output = output.getvalue()
        assert "GET" in log_output

    def test_binds_user_agent_to_context(self, client: TestClient) -> None:
        """Verify user_agent is bound to structlog context."""
        output = StringIO()
        structlog.configure(
            processors=[
                structlog.contextvars.merge_contextvars,
                structlog.processors.JSONRenderer(),
            ],
            wrapper_class=structlog.make_filtering_bound_logger(0),
            context_class=dict,
            logger_factory=structlog.PrintLoggerFactory(output),
            cache_logger_on_first_use=False,
        )

        client.get("/log-test", headers={"user-agent": "TestAgent/1.0"})

        log_output = output.getvalue()
        assert "TestAgent/1.0" in log_output


class TestRequestCompletionLogging:
    """Test suite for request completion logging."""

    def test_logs_request_completed_event(self, client: TestClient) -> None:
        """Verify request_completed event is logged."""
        output = StringIO()
        structlog.configure(
            processors=[
                structlog.contextvars.merge_contextvars,
                structlog.processors.JSONRenderer(),
            ],
            wrapper_class=structlog.make_filtering_bound_logger(0),
            context_class=dict,
            logger_factory=structlog.PrintLoggerFactory(output),
            cache_logger_on_first_use=False,
        )

        client.get("/test")

        log_output = output.getvalue()
        assert "request_completed" in log_output

    def test_logs_status_code(self, client: TestClient) -> None:
        """Verify status_code is included in completion log."""
        output = StringIO()
        structlog.configure(
            processors=[
                structlog.contextvars.merge_contextvars,
                structlog.processors.JSONRenderer(),
            ],
            wrapper_class=structlog.make_filtering_bound_logger(0),
            context_class=dict,
            logger_factory=structlog.PrintLoggerFactory(output),
            cache_logger_on_first_use=False,
        )

        client.get("/test")

        log_output = output.getvalue()
        assert "status_code" in log_output
        assert "200" in log_output

    def test_logs_duration_ms(self, client: TestClient) -> None:
        """Verify duration_ms is included in completion log."""
        output = StringIO()
        structlog.configure(
            processors=[
                structlog.contextvars.merge_contextvars,
                structlog.processors.JSONRenderer(),
            ],
            wrapper_class=structlog.make_filtering_bound_logger(0),
            context_class=dict,
            logger_factory=structlog.PrintLoggerFactory(output),
            cache_logger_on_first_use=False,
        )

        client.get("/test")

        log_output = output.getvalue()
        assert "duration_ms" in log_output

    def test_duration_is_positive_number(self, client: TestClient) -> None:
        """Verify duration_ms is a positive number."""
        import json

        output = StringIO()
        structlog.configure(
            processors=[
                structlog.contextvars.merge_contextvars,
                structlog.processors.JSONRenderer(),
            ],
            wrapper_class=structlog.make_filtering_bound_logger(0),
            context_class=dict,
            logger_factory=structlog.PrintLoggerFactory(output),
            cache_logger_on_first_use=False,
        )

        client.get("/test")

        log_lines = output.getvalue().strip().split("\n")
        for line in log_lines:
            log_entry = json.loads(line)
            if log_entry.get("event") == "request_completed":
                assert log_entry["duration_ms"] > 0
                break


class TestMiddlewareIntegration:
    """Test suite for middleware integration scenarios."""

    def test_works_with_http_exception_responses(self, app: FastAPI) -> None:
        """Verify middleware works correctly with HTTP exception responses."""
        from fastapi import HTTPException

        @app.get("/not-found")
        def not_found_endpoint() -> None:
            raise HTTPException(status_code=404, detail="Not found")

        client = TestClient(app)
        response = client.get("/not-found")

        assert response.status_code == 404
        assert REQUEST_ID_HEADER in response.headers

    def test_context_isolated_between_requests(self, client: TestClient) -> None:
        """Verify context is isolated between concurrent requests."""
        id1 = "request-1-id"
        id2 = "request-2-id"

        response1 = client.get("/test", headers={REQUEST_ID_HEADER: id1})
        response2 = client.get("/test", headers={REQUEST_ID_HEADER: id2})

        assert response1.headers[REQUEST_ID_HEADER] == id1
        assert response2.headers[REQUEST_ID_HEADER] == id2

    def test_empty_user_agent_handled(self, client: TestClient) -> None:
        """Verify middleware handles missing user-agent header."""
        response = client.get("/test", headers={"user-agent": ""})

        assert response.status_code == 200
        assert REQUEST_ID_HEADER in response.headers
