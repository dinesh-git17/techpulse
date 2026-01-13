"""Unit tests for exception handlers."""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from techpulse.api.exceptions.domain import (
    APIError,
    DatabaseConnectionError,
    DataValidationError,
    QueryExecutionError,
    RecordNotFoundError,
)
from techpulse.api.exceptions.handlers import register_exception_handlers
from techpulse.api.schemas.errors import ERROR_TYPE_BASE


@pytest.fixture
def test_app() -> FastAPI:
    """Create a test FastAPI app with exception handlers registered."""
    app = FastAPI()
    register_exception_handlers(app)
    return app


@pytest.fixture
def client(test_app: FastAPI) -> TestClient:
    """Create a test client for the test app."""
    return TestClient(test_app, raise_server_exceptions=False)


class TestDatabaseConnectionErrorHandler:
    """Test suite for database connection error handler."""

    def test_returns_503_status(self, test_app: FastAPI, client: TestClient) -> None:
        """Verify handler returns 503 status code."""

        @test_app.get("/test")
        def raise_error() -> None:
            raise DatabaseConnectionError(path="/db/test.duckdb", reason="locked")

        response = client.get("/test")
        assert response.status_code == 503

    def test_returns_rfc7807_format(
        self, test_app: FastAPI, client: TestClient
    ) -> None:
        """Verify response follows RFC 7807 format."""

        @test_app.get("/test")
        def raise_error() -> None:
            raise DatabaseConnectionError(path="/db/test.duckdb", reason="locked")

        response = client.get("/test")
        data = response.json()
        assert "type" in data
        assert "title" in data
        assert "status" in data
        assert "detail" in data

    def test_includes_correct_error_type(
        self, test_app: FastAPI, client: TestClient
    ) -> None:
        """Verify error type is correct."""

        @test_app.get("/test")
        def raise_error() -> None:
            raise DatabaseConnectionError(path="/db/test.duckdb", reason="locked")

        response = client.get("/test")
        data = response.json()
        assert data["type"] == f"{ERROR_TYPE_BASE}/database-connection-error"

    def test_includes_instance_path(
        self, test_app: FastAPI, client: TestClient
    ) -> None:
        """Verify instance contains request path."""

        @test_app.get("/api/v1/items")
        def raise_error() -> None:
            raise DatabaseConnectionError(path="/db/test.duckdb", reason="locked")

        response = client.get("/api/v1/items")
        data = response.json()
        assert data["instance"] == "/api/v1/items"

    def test_content_type_is_problem_json(
        self, test_app: FastAPI, client: TestClient
    ) -> None:
        """Verify Content-Type is application/problem+json."""

        @test_app.get("/test")
        def raise_error() -> None:
            raise DatabaseConnectionError(path="/db/test.duckdb", reason="locked")

        response = client.get("/test")
        assert response.headers["content-type"] == "application/problem+json"


class TestRecordNotFoundErrorHandler:
    """Test suite for record not found error handler."""

    def test_returns_404_status(self, test_app: FastAPI, client: TestClient) -> None:
        """Verify handler returns 404 status code."""

        @test_app.get("/test")
        def raise_error() -> None:
            raise RecordNotFoundError(entity_type="Technology", identifier="unknown")

        response = client.get("/test")
        assert response.status_code == 404

    def test_includes_entity_in_detail(
        self, test_app: FastAPI, client: TestClient
    ) -> None:
        """Verify detail includes entity type and identifier."""

        @test_app.get("/test")
        def raise_error() -> None:
            raise RecordNotFoundError(entity_type="Technology", identifier="unknown")

        response = client.get("/test")
        data = response.json()
        assert "Technology" in data["detail"]
        assert "unknown" in data["detail"]

    def test_includes_correct_error_type(
        self, test_app: FastAPI, client: TestClient
    ) -> None:
        """Verify error type is correct."""

        @test_app.get("/test")
        def raise_error() -> None:
            raise RecordNotFoundError(entity_type="Technology", identifier="unknown")

        response = client.get("/test")
        data = response.json()
        assert data["type"] == f"{ERROR_TYPE_BASE}/record-not-found"


class TestQueryExecutionErrorHandler:
    """Test suite for query execution error handler."""

    def test_returns_500_status(self, test_app: FastAPI, client: TestClient) -> None:
        """Verify handler returns 500 status code."""

        @test_app.get("/test")
        def raise_error() -> None:
            raise QueryExecutionError(query="SELECT * FROM foo", reason="syntax error")

        response = client.get("/test")
        assert response.status_code == 500

    def test_does_not_expose_query_details(
        self, test_app: FastAPI, client: TestClient
    ) -> None:
        """Verify response does not expose internal query details."""

        @test_app.get("/test")
        def raise_error() -> None:
            raise QueryExecutionError(
                query="SELECT secret FROM users", reason="table not found"
            )

        response = client.get("/test")
        data = response.json()
        assert "SELECT" not in data["detail"]
        assert "secret" not in data["detail"]

    def test_includes_correct_error_type(
        self, test_app: FastAPI, client: TestClient
    ) -> None:
        """Verify error type is correct."""

        @test_app.get("/test")
        def raise_error() -> None:
            raise QueryExecutionError(query="SELECT 1", reason="timeout")

        response = client.get("/test")
        data = response.json()
        assert data["type"] == f"{ERROR_TYPE_BASE}/query-execution-error"


class TestDataValidationErrorHandler:
    """Test suite for data validation error handler."""

    def test_returns_422_status(self, test_app: FastAPI, client: TestClient) -> None:
        """Verify handler returns 422 status code."""

        @test_app.get("/test")
        def raise_error() -> None:
            raise DataValidationError(model_name="TrendModel", reason="invalid date")

        response = client.get("/test")
        assert response.status_code == 422

    def test_includes_reason_in_detail(
        self, test_app: FastAPI, client: TestClient
    ) -> None:
        """Verify detail includes validation reason."""

        @test_app.get("/test")
        def raise_error() -> None:
            raise DataValidationError(model_name="TrendModel", reason="missing field")

        response = client.get("/test")
        data = response.json()
        assert "missing field" in data["detail"]

    def test_includes_correct_error_type(
        self, test_app: FastAPI, client: TestClient
    ) -> None:
        """Verify error type is correct."""

        @test_app.get("/test")
        def raise_error() -> None:
            raise DataValidationError(model_name="Model", reason="invalid")

        response = client.get("/test")
        data = response.json()
        assert data["type"] == f"{ERROR_TYPE_BASE}/data-validation-error"


class TestAPIErrorHandler:
    """Test suite for generic API error handler."""

    def test_returns_500_status(self, test_app: FastAPI, client: TestClient) -> None:
        """Verify handler returns 500 status code for generic APIError."""

        @test_app.get("/test")
        def raise_error() -> None:
            raise APIError("Something went wrong")

        response = client.get("/test")
        assert response.status_code == 500

    def test_includes_generic_error_type(
        self, test_app: FastAPI, client: TestClient
    ) -> None:
        """Verify error type is internal-error."""

        @test_app.get("/test")
        def raise_error() -> None:
            raise APIError("Something went wrong")

        response = client.get("/test")
        data = response.json()
        assert data["type"] == f"{ERROR_TYPE_BASE}/internal-error"


class TestUnhandledExceptionHandler:
    """Test suite for unhandled exception handler."""

    def test_returns_500_status(self, test_app: FastAPI, client: TestClient) -> None:
        """Verify handler returns 500 for unhandled exceptions."""

        @test_app.get("/test")
        def raise_error() -> None:
            raise RuntimeError("Unexpected error")

        response = client.get("/test")
        assert response.status_code == 500

    def test_does_not_expose_error_details(
        self, test_app: FastAPI, client: TestClient
    ) -> None:
        """Verify response does not expose internal error details."""

        @test_app.get("/test")
        def raise_error() -> None:
            raise RuntimeError("Secret internal error message")

        response = client.get("/test")
        data = response.json()
        assert "Secret" not in data["detail"]
        assert "internal error message" not in data["detail"]

    def test_returns_rfc7807_format(
        self, test_app: FastAPI, client: TestClient
    ) -> None:
        """Verify unhandled exceptions return RFC 7807 format."""

        @test_app.get("/test")
        def raise_error() -> None:
            raise ValueError("Bad value")

        response = client.get("/test")
        data = response.json()
        assert "type" in data
        assert "title" in data
        assert "status" in data
        assert "detail" in data

    def test_content_type_is_problem_json(
        self, test_app: FastAPI, client: TestClient
    ) -> None:
        """Verify Content-Type is application/problem+json."""

        @test_app.get("/test")
        def raise_error() -> None:
            raise Exception("Generic exception")

        response = client.get("/test")
        assert response.headers["content-type"] == "application/problem+json"


class TestRegisterExceptionHandlers:
    """Test suite for register_exception_handlers function."""

    def test_all_handlers_registered(self) -> None:
        """Verify all exception handlers are registered."""
        app = FastAPI()
        register_exception_handlers(app)

        assert DatabaseConnectionError in app.exception_handlers
        assert RecordNotFoundError in app.exception_handlers
        assert QueryExecutionError in app.exception_handlers
        assert DataValidationError in app.exception_handlers
        assert APIError in app.exception_handlers
        assert Exception in app.exception_handlers

    def test_handlers_are_callable(self) -> None:
        """Verify registered handlers are callable."""
        app = FastAPI()
        register_exception_handlers(app)

        for handler in app.exception_handlers.values():
            assert callable(handler)
