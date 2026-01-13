"""Integration tests for health check endpoints.

These tests verify the GET /health/live and /health/ready endpoint behavior
with realistic mocking of database and cache dependencies.
"""

from typing import Generator
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from techpulse.api.exceptions.domain import DatabaseConnectionError
from techpulse.api.main import app


@pytest.fixture
def mock_db_manager_healthy() -> Generator[MagicMock, None, None]:
    """Create mock database session manager that is healthy."""
    mock = MagicMock()
    mock.health_check.return_value = True
    mock.is_connected.return_value = True
    yield mock


@pytest.fixture
def mock_db_manager_unhealthy() -> Generator[MagicMock, None, None]:
    """Create mock database session manager that fails health check."""
    mock = MagicMock()
    mock.health_check.return_value = False
    mock.is_connected.return_value = True
    yield mock


@pytest.fixture
def mock_cache_service_healthy() -> Generator[MagicMock, None, None]:
    """Create mock cache service that is healthy."""
    mock = MagicMock()
    mock.health_check.return_value = True
    mock.is_connected.return_value = True
    yield mock


@pytest.fixture
def mock_cache_service_unhealthy() -> Generator[MagicMock, None, None]:
    """Create mock cache service that fails health check."""
    mock = MagicMock()
    mock.health_check.return_value = False
    mock.is_connected.return_value = False
    yield mock


@pytest.fixture
def client_all_healthy(
    mock_db_manager_healthy: MagicMock,
    mock_cache_service_healthy: MagicMock,
) -> Generator[TestClient, None, None]:
    """Create test client with all dependencies healthy."""
    with (
        patch(
            "techpulse.api.routes.health.get_session_manager",
            return_value=mock_db_manager_healthy,
        ),
        patch(
            "techpulse.api.routes.health.get_cache_service",
            return_value=mock_cache_service_healthy,
        ),
        patch(
            "techpulse.api.main.get_session_manager",
            return_value=mock_db_manager_healthy,
        ),
    ):
        yield TestClient(app, raise_server_exceptions=False)


class TestLivenessProbe:
    """Integration tests for liveness probe endpoint."""

    def test_liveness_returns_200_when_api_running(self) -> None:
        """Verify liveness probe returns 200 OK when API is running."""
        client = TestClient(app, raise_server_exceptions=False)
        response = client.get("/health/live")

        assert response.status_code == 200

    def test_liveness_response_format(self) -> None:
        """Verify liveness response follows expected format."""
        client = TestClient(app, raise_server_exceptions=False)
        response = client.get("/health/live")
        body = response.json()

        assert body == {"status": "ok"}

    def test_liveness_independent_of_database(
        self,
        mock_db_manager_unhealthy: MagicMock,
    ) -> None:
        """Verify liveness returns 200 even when database is unhealthy."""
        with patch(
            "techpulse.api.main.get_session_manager",
            return_value=mock_db_manager_unhealthy,
        ):
            client = TestClient(app, raise_server_exceptions=False)
            response = client.get("/health/live")

        assert response.status_code == 200

    def test_liveness_independent_of_cache(
        self,
        mock_cache_service_unhealthy: MagicMock,
    ) -> None:
        """Verify liveness returns 200 even when cache is unhealthy."""
        with patch(
            "techpulse.api.routes.health.get_cache_service",
            return_value=mock_cache_service_unhealthy,
        ):
            client = TestClient(app, raise_server_exceptions=False)
            response = client.get("/health/live")

        assert response.status_code == 200


class TestReadinessProbeAllHealthy:
    """Integration tests for readiness probe when all dependencies healthy."""

    def test_readiness_returns_200(
        self,
        client_all_healthy: TestClient,
    ) -> None:
        """Verify readiness returns 200 when all dependencies healthy."""
        response = client_all_healthy.get("/health/ready")
        assert response.status_code == 200

    def test_readiness_status_is_healthy(
        self,
        client_all_healthy: TestClient,
    ) -> None:
        """Verify readiness status is healthy when all dependencies up."""
        response = client_all_healthy.get("/health/ready")
        body = response.json()

        assert body["status"] == "healthy"

    def test_database_component_up(
        self,
        client_all_healthy: TestClient,
    ) -> None:
        """Verify database component shows up status."""
        response = client_all_healthy.get("/health/ready")
        body = response.json()

        assert body["components"]["database"]["status"] == "up"
        assert "latency_ms" in body["components"]["database"]

    def test_cache_component_up(
        self,
        client_all_healthy: TestClient,
    ) -> None:
        """Verify cache component shows up status."""
        response = client_all_healthy.get("/health/ready")
        body = response.json()

        assert body["components"]["cache"]["status"] == "up"
        assert "latency_ms" in body["components"]["cache"]


class TestReadinessProbeDatabaseFailure:
    """Integration tests for readiness probe when database fails."""

    def test_readiness_returns_503_on_database_failure(
        self,
        mock_db_manager_unhealthy: MagicMock,
        mock_cache_service_healthy: MagicMock,
    ) -> None:
        """Verify readiness returns 503 when database health check fails."""
        with (
            patch(
                "techpulse.api.routes.health.get_session_manager",
                return_value=mock_db_manager_unhealthy,
            ),
            patch(
                "techpulse.api.routes.health.get_cache_service",
                return_value=mock_cache_service_healthy,
            ),
            patch(
                "techpulse.api.main.get_session_manager",
                return_value=mock_db_manager_unhealthy,
            ),
        ):
            client = TestClient(app, raise_server_exceptions=False)
            response = client.get("/health/ready")

        assert response.status_code == 503

    def test_readiness_status_unhealthy_on_database_failure(
        self,
        mock_db_manager_unhealthy: MagicMock,
        mock_cache_service_healthy: MagicMock,
    ) -> None:
        """Verify readiness status is unhealthy when database fails."""
        with (
            patch(
                "techpulse.api.routes.health.get_session_manager",
                return_value=mock_db_manager_unhealthy,
            ),
            patch(
                "techpulse.api.routes.health.get_cache_service",
                return_value=mock_cache_service_healthy,
            ),
            patch(
                "techpulse.api.main.get_session_manager",
                return_value=mock_db_manager_unhealthy,
            ),
        ):
            client = TestClient(app, raise_server_exceptions=False)
            response = client.get("/health/ready")

        body = response.json()
        assert body["status"] == "unhealthy"

    def test_database_shows_down_on_failure(
        self,
        mock_db_manager_unhealthy: MagicMock,
        mock_cache_service_healthy: MagicMock,
    ) -> None:
        """Verify database component shows down with error on failure."""
        with (
            patch(
                "techpulse.api.routes.health.get_session_manager",
                return_value=mock_db_manager_unhealthy,
            ),
            patch(
                "techpulse.api.routes.health.get_cache_service",
                return_value=mock_cache_service_healthy,
            ),
            patch(
                "techpulse.api.main.get_session_manager",
                return_value=mock_db_manager_unhealthy,
            ),
        ):
            client = TestClient(app, raise_server_exceptions=False)
            response = client.get("/health/ready")

        body = response.json()
        assert body["components"]["database"]["status"] == "down"
        assert "error" in body["components"]["database"]

    def test_cache_still_up_when_database_fails(
        self,
        mock_db_manager_unhealthy: MagicMock,
        mock_cache_service_healthy: MagicMock,
    ) -> None:
        """Verify cache component shows up even when database fails."""
        with (
            patch(
                "techpulse.api.routes.health.get_session_manager",
                return_value=mock_db_manager_unhealthy,
            ),
            patch(
                "techpulse.api.routes.health.get_cache_service",
                return_value=mock_cache_service_healthy,
            ),
            patch(
                "techpulse.api.main.get_session_manager",
                return_value=mock_db_manager_unhealthy,
            ),
        ):
            client = TestClient(app, raise_server_exceptions=False)
            response = client.get("/health/ready")

        body = response.json()
        assert body["components"]["cache"]["status"] == "up"


class TestReadinessProbeCacheFailure:
    """Integration tests for readiness probe when cache fails."""

    def test_readiness_returns_503_on_cache_failure(
        self,
        mock_db_manager_healthy: MagicMock,
        mock_cache_service_unhealthy: MagicMock,
    ) -> None:
        """Verify readiness returns 503 when cache health check fails."""
        with (
            patch(
                "techpulse.api.routes.health.get_session_manager",
                return_value=mock_db_manager_healthy,
            ),
            patch(
                "techpulse.api.routes.health.get_cache_service",
                return_value=mock_cache_service_unhealthy,
            ),
            patch(
                "techpulse.api.main.get_session_manager",
                return_value=mock_db_manager_healthy,
            ),
        ):
            client = TestClient(app, raise_server_exceptions=False)
            response = client.get("/health/ready")

        assert response.status_code == 503

    def test_readiness_status_unhealthy_on_cache_failure(
        self,
        mock_db_manager_healthy: MagicMock,
        mock_cache_service_unhealthy: MagicMock,
    ) -> None:
        """Verify readiness status is unhealthy when cache fails."""
        with (
            patch(
                "techpulse.api.routes.health.get_session_manager",
                return_value=mock_db_manager_healthy,
            ),
            patch(
                "techpulse.api.routes.health.get_cache_service",
                return_value=mock_cache_service_unhealthy,
            ),
            patch(
                "techpulse.api.main.get_session_manager",
                return_value=mock_db_manager_healthy,
            ),
        ):
            client = TestClient(app, raise_server_exceptions=False)
            response = client.get("/health/ready")

        body = response.json()
        assert body["status"] == "unhealthy"

    def test_cache_shows_down_on_failure(
        self,
        mock_db_manager_healthy: MagicMock,
        mock_cache_service_unhealthy: MagicMock,
    ) -> None:
        """Verify cache component shows down with error on failure."""
        with (
            patch(
                "techpulse.api.routes.health.get_session_manager",
                return_value=mock_db_manager_healthy,
            ),
            patch(
                "techpulse.api.routes.health.get_cache_service",
                return_value=mock_cache_service_unhealthy,
            ),
            patch(
                "techpulse.api.main.get_session_manager",
                return_value=mock_db_manager_healthy,
            ),
        ):
            client = TestClient(app, raise_server_exceptions=False)
            response = client.get("/health/ready")

        body = response.json()
        assert body["components"]["cache"]["status"] == "down"
        assert "error" in body["components"]["cache"]

    def test_database_still_up_when_cache_fails(
        self,
        mock_db_manager_healthy: MagicMock,
        mock_cache_service_unhealthy: MagicMock,
    ) -> None:
        """Verify database component shows up even when cache fails."""
        with (
            patch(
                "techpulse.api.routes.health.get_session_manager",
                return_value=mock_db_manager_healthy,
            ),
            patch(
                "techpulse.api.routes.health.get_cache_service",
                return_value=mock_cache_service_unhealthy,
            ),
            patch(
                "techpulse.api.main.get_session_manager",
                return_value=mock_db_manager_healthy,
            ),
        ):
            client = TestClient(app, raise_server_exceptions=False)
            response = client.get("/health/ready")

        body = response.json()
        assert body["components"]["database"]["status"] == "up"


class TestReadinessProbeCacheNotConfigured:
    """Integration tests for readiness probe when cache is not configured."""

    def test_readiness_returns_503_when_cache_none(
        self,
        mock_db_manager_healthy: MagicMock,
    ) -> None:
        """Verify readiness returns 503 when cache service is None."""
        with (
            patch(
                "techpulse.api.routes.health.get_session_manager",
                return_value=mock_db_manager_healthy,
            ),
            patch(
                "techpulse.api.routes.health.get_cache_service",
                return_value=None,
            ),
            patch(
                "techpulse.api.main.get_session_manager",
                return_value=mock_db_manager_healthy,
            ),
        ):
            client = TestClient(app, raise_server_exceptions=False)
            response = client.get("/health/ready")

        assert response.status_code == 503

    def test_cache_shows_not_configured_error(
        self,
        mock_db_manager_healthy: MagicMock,
    ) -> None:
        """Verify cache shows not configured error when service is None."""
        with (
            patch(
                "techpulse.api.routes.health.get_session_manager",
                return_value=mock_db_manager_healthy,
            ),
            patch(
                "techpulse.api.routes.health.get_cache_service",
                return_value=None,
            ),
            patch(
                "techpulse.api.main.get_session_manager",
                return_value=mock_db_manager_healthy,
            ),
        ):
            client = TestClient(app, raise_server_exceptions=False)
            response = client.get("/health/ready")

        body = response.json()
        assert body["components"]["cache"]["status"] == "down"
        assert "not configured" in body["components"]["cache"]["error"]


class TestReadinessProbeDatabaseNotInitialized:
    """Integration tests for readiness probe when database manager not initialized."""

    def test_readiness_returns_503_when_db_not_initialized(
        self,
        mock_cache_service_healthy: MagicMock,
    ) -> None:
        """Verify readiness returns 503 when database manager raises exception."""
        with (
            patch(
                "techpulse.api.routes.health.get_session_manager",
                side_effect=DatabaseConnectionError(
                    path="unknown",
                    reason="Session manager not initialized",
                ),
            ),
            patch(
                "techpulse.api.routes.health.get_cache_service",
                return_value=mock_cache_service_healthy,
            ),
            patch(
                "techpulse.api.main.get_session_manager",
                side_effect=DatabaseConnectionError(
                    path="unknown",
                    reason="Session manager not initialized",
                ),
            ),
        ):
            client = TestClient(app, raise_server_exceptions=False)
            response = client.get("/health/ready")

        assert response.status_code == 503

    def test_database_shows_error_when_not_initialized(
        self,
        mock_cache_service_healthy: MagicMock,
    ) -> None:
        """Verify database shows error message when manager not initialized."""
        with (
            patch(
                "techpulse.api.routes.health.get_session_manager",
                side_effect=DatabaseConnectionError(
                    path="unknown",
                    reason="Session manager not initialized",
                ),
            ),
            patch(
                "techpulse.api.routes.health.get_cache_service",
                return_value=mock_cache_service_healthy,
            ),
            patch(
                "techpulse.api.main.get_session_manager",
                side_effect=DatabaseConnectionError(
                    path="unknown",
                    reason="Session manager not initialized",
                ),
            ),
        ):
            client = TestClient(app, raise_server_exceptions=False)
            response = client.get("/health/ready")

        body = response.json()
        assert body["components"]["database"]["status"] == "down"
        assert "error" in body["components"]["database"]


class TestReadinessProbeResponseHeaders:
    """Integration tests for readiness probe response headers."""

    def test_response_includes_request_id_header(
        self,
        client_all_healthy: TestClient,
    ) -> None:
        """Verify response includes X-Request-ID header."""
        response = client_all_healthy.get("/health/ready")

        assert "x-request-id" in response.headers

    def test_response_content_type_is_json(
        self,
        client_all_healthy: TestClient,
    ) -> None:
        """Verify response content type is application/json."""
        response = client_all_healthy.get("/health/ready")

        assert response.headers["content-type"] == "application/json"


class TestReadinessProbeLatencyMeasurement:
    """Integration tests for latency measurement in readiness probe."""

    def test_latency_is_non_negative(
        self,
        client_all_healthy: TestClient,
    ) -> None:
        """Verify latency measurements are non-negative."""
        response = client_all_healthy.get("/health/ready")
        body = response.json()

        assert body["components"]["database"]["latency_ms"] >= 0
        assert body["components"]["cache"]["latency_ms"] >= 0

    def test_latency_is_numeric(
        self,
        client_all_healthy: TestClient,
    ) -> None:
        """Verify latency measurements are numeric values."""
        response = client_all_healthy.get("/health/ready")
        body = response.json()

        assert isinstance(
            body["components"]["database"]["latency_ms"],
            (int, float),
        )
        assert isinstance(
            body["components"]["cache"]["latency_ms"],
            (int, float),
        )


class TestBothDependenciesFailure:
    """Integration tests when both database and cache fail."""

    def test_readiness_returns_503_when_both_fail(
        self,
        mock_db_manager_unhealthy: MagicMock,
        mock_cache_service_unhealthy: MagicMock,
    ) -> None:
        """Verify readiness returns 503 when both dependencies fail."""
        with (
            patch(
                "techpulse.api.routes.health.get_session_manager",
                return_value=mock_db_manager_unhealthy,
            ),
            patch(
                "techpulse.api.routes.health.get_cache_service",
                return_value=mock_cache_service_unhealthy,
            ),
            patch(
                "techpulse.api.main.get_session_manager",
                return_value=mock_db_manager_unhealthy,
            ),
        ):
            client = TestClient(app, raise_server_exceptions=False)
            response = client.get("/health/ready")

        assert response.status_code == 503

    def test_both_components_show_down(
        self,
        mock_db_manager_unhealthy: MagicMock,
        mock_cache_service_unhealthy: MagicMock,
    ) -> None:
        """Verify both components show down status when both fail."""
        with (
            patch(
                "techpulse.api.routes.health.get_session_manager",
                return_value=mock_db_manager_unhealthy,
            ),
            patch(
                "techpulse.api.routes.health.get_cache_service",
                return_value=mock_cache_service_unhealthy,
            ),
            patch(
                "techpulse.api.main.get_session_manager",
                return_value=mock_db_manager_unhealthy,
            ),
        ):
            client = TestClient(app, raise_server_exceptions=False)
            response = client.get("/health/ready")

        body = response.json()
        assert body["components"]["database"]["status"] == "down"
        assert body["components"]["cache"]["status"] == "down"
