"""Unit tests for health check endpoints.

Tests cover liveness probe, readiness probe, component health checks,
timeout behavior, and response format validation.
"""

import time
from typing import Generator
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from techpulse.api.main import app
from techpulse.api.routes.health import (
    HEALTH_CHECK_TIMEOUT_SECONDS,
    ComponentHealthDown,
    ComponentHealthUp,
    _check_cache_health,
    _check_database_health,
    _execute_with_timeout,
)


@pytest.fixture
def mock_db_manager() -> Generator[MagicMock, None, None]:
    """Create mock database session manager."""
    mock = MagicMock()
    mock.health_check.return_value = True
    yield mock


@pytest.fixture
def mock_cache_service() -> Generator[MagicMock, None, None]:
    """Create mock cache service."""
    mock = MagicMock()
    mock.health_check.return_value = True
    yield mock


@pytest.fixture
def client_all_healthy(
    mock_db_manager: MagicMock,
    mock_cache_service: MagicMock,
) -> Generator[TestClient, None, None]:
    """Create test client with all dependencies healthy."""
    with (
        patch(
            "techpulse.api.routes.health.get_session_manager",
            return_value=mock_db_manager,
        ),
        patch(
            "techpulse.api.routes.health.get_cache_service",
            return_value=mock_cache_service,
        ),
        patch(
            "techpulse.api.main.get_session_manager",
            return_value=mock_db_manager,
        ),
    ):
        yield TestClient(app)


class TestLivenessEndpoint:
    """Test suite for GET /health/live endpoint."""

    def test_returns_200_status(self) -> None:
        """Verify liveness endpoint returns 200 OK."""
        client = TestClient(app, raise_server_exceptions=False)
        response = client.get("/health/live")
        assert response.status_code == 200

    def test_returns_ok_status_in_body(self) -> None:
        """Verify liveness response contains status ok."""
        client = TestClient(app, raise_server_exceptions=False)
        response = client.get("/health/live")
        body = response.json()
        assert body["status"] == "ok"

    def test_returns_json_content_type(self) -> None:
        """Verify liveness response has JSON content type."""
        client = TestClient(app, raise_server_exceptions=False)
        response = client.get("/health/live")
        assert response.headers["content-type"] == "application/json"


class TestReadinessEndpointHealthy:
    """Test suite for GET /health/ready when all dependencies are healthy."""

    def test_returns_200_when_all_healthy(
        self,
        client_all_healthy: TestClient,
    ) -> None:
        """Verify readiness returns 200 when all dependencies healthy."""
        response = client_all_healthy.get("/health/ready")
        assert response.status_code == 200

    def test_returns_healthy_status(
        self,
        client_all_healthy: TestClient,
    ) -> None:
        """Verify readiness returns healthy status in body."""
        response = client_all_healthy.get("/health/ready")
        body = response.json()
        assert body["status"] == "healthy"

    def test_contains_components_object(
        self,
        client_all_healthy: TestClient,
    ) -> None:
        """Verify response contains components object."""
        response = client_all_healthy.get("/health/ready")
        body = response.json()
        assert "components" in body
        assert "database" in body["components"]
        assert "cache" in body["components"]

    def test_database_component_shows_up(
        self,
        client_all_healthy: TestClient,
    ) -> None:
        """Verify database component status is up when healthy."""
        response = client_all_healthy.get("/health/ready")
        body = response.json()
        assert body["components"]["database"]["status"] == "up"

    def test_cache_component_shows_up(
        self,
        client_all_healthy: TestClient,
    ) -> None:
        """Verify cache component status is up when healthy."""
        response = client_all_healthy.get("/health/ready")
        body = response.json()
        assert body["components"]["cache"]["status"] == "up"

    def test_database_includes_latency_ms(
        self,
        client_all_healthy: TestClient,
    ) -> None:
        """Verify database component includes latency_ms when healthy."""
        response = client_all_healthy.get("/health/ready")
        body = response.json()
        assert "latency_ms" in body["components"]["database"]
        assert isinstance(body["components"]["database"]["latency_ms"], (int, float))

    def test_cache_includes_latency_ms(
        self,
        client_all_healthy: TestClient,
    ) -> None:
        """Verify cache component includes latency_ms when healthy."""
        response = client_all_healthy.get("/health/ready")
        body = response.json()
        assert "latency_ms" in body["components"]["cache"]
        assert isinstance(body["components"]["cache"]["latency_ms"], (int, float))


class TestReadinessEndpointDatabaseFailure:
    """Test suite for GET /health/ready when database fails."""

    def test_returns_503_when_database_unhealthy(
        self,
        mock_cache_service: MagicMock,
    ) -> None:
        """Verify readiness returns 503 when database health check fails."""
        mock_db = MagicMock()
        mock_db.health_check.return_value = False

        with (
            patch(
                "techpulse.api.routes.health.get_session_manager",
                return_value=mock_db,
            ),
            patch(
                "techpulse.api.routes.health.get_cache_service",
                return_value=mock_cache_service,
            ),
            patch(
                "techpulse.api.main.get_session_manager",
                return_value=mock_db,
            ),
        ):
            client = TestClient(app, raise_server_exceptions=False)
            response = client.get("/health/ready")

        assert response.status_code == 503

    def test_returns_unhealthy_status_when_database_fails(
        self,
        mock_cache_service: MagicMock,
    ) -> None:
        """Verify readiness returns unhealthy status when database fails."""
        mock_db = MagicMock()
        mock_db.health_check.return_value = False

        with (
            patch(
                "techpulse.api.routes.health.get_session_manager",
                return_value=mock_db,
            ),
            patch(
                "techpulse.api.routes.health.get_cache_service",
                return_value=mock_cache_service,
            ),
            patch(
                "techpulse.api.main.get_session_manager",
                return_value=mock_db,
            ),
        ):
            client = TestClient(app, raise_server_exceptions=False)
            response = client.get("/health/ready")

        body = response.json()
        assert body["status"] == "unhealthy"

    def test_database_shows_down_with_error(
        self,
        mock_cache_service: MagicMock,
    ) -> None:
        """Verify database component shows down status with error message."""
        mock_db = MagicMock()
        mock_db.health_check.return_value = False

        with (
            patch(
                "techpulse.api.routes.health.get_session_manager",
                return_value=mock_db,
            ),
            patch(
                "techpulse.api.routes.health.get_cache_service",
                return_value=mock_cache_service,
            ),
            patch(
                "techpulse.api.main.get_session_manager",
                return_value=mock_db,
            ),
        ):
            client = TestClient(app, raise_server_exceptions=False)
            response = client.get("/health/ready")

        body = response.json()
        assert body["components"]["database"]["status"] == "down"
        assert "error" in body["components"]["database"]

    def test_cache_still_shows_up_when_database_fails(
        self,
        mock_cache_service: MagicMock,
    ) -> None:
        """Verify cache shows up even when database fails."""
        mock_db = MagicMock()
        mock_db.health_check.return_value = False

        with (
            patch(
                "techpulse.api.routes.health.get_session_manager",
                return_value=mock_db,
            ),
            patch(
                "techpulse.api.routes.health.get_cache_service",
                return_value=mock_cache_service,
            ),
            patch(
                "techpulse.api.main.get_session_manager",
                return_value=mock_db,
            ),
        ):
            client = TestClient(app, raise_server_exceptions=False)
            response = client.get("/health/ready")

        body = response.json()
        assert body["components"]["cache"]["status"] == "up"


class TestReadinessEndpointCacheFailure:
    """Test suite for GET /health/ready when cache fails."""

    def test_returns_503_when_cache_unhealthy(
        self,
        mock_db_manager: MagicMock,
    ) -> None:
        """Verify readiness returns 503 when cache health check fails."""
        mock_cache = MagicMock()
        mock_cache.health_check.return_value = False

        with (
            patch(
                "techpulse.api.routes.health.get_session_manager",
                return_value=mock_db_manager,
            ),
            patch(
                "techpulse.api.routes.health.get_cache_service",
                return_value=mock_cache,
            ),
            patch(
                "techpulse.api.main.get_session_manager",
                return_value=mock_db_manager,
            ),
        ):
            client = TestClient(app, raise_server_exceptions=False)
            response = client.get("/health/ready")

        assert response.status_code == 503

    def test_returns_unhealthy_status_when_cache_fails(
        self,
        mock_db_manager: MagicMock,
    ) -> None:
        """Verify readiness returns unhealthy status when cache fails."""
        mock_cache = MagicMock()
        mock_cache.health_check.return_value = False

        with (
            patch(
                "techpulse.api.routes.health.get_session_manager",
                return_value=mock_db_manager,
            ),
            patch(
                "techpulse.api.routes.health.get_cache_service",
                return_value=mock_cache,
            ),
            patch(
                "techpulse.api.main.get_session_manager",
                return_value=mock_db_manager,
            ),
        ):
            client = TestClient(app, raise_server_exceptions=False)
            response = client.get("/health/ready")

        body = response.json()
        assert body["status"] == "unhealthy"

    def test_cache_shows_down_with_error(
        self,
        mock_db_manager: MagicMock,
    ) -> None:
        """Verify cache component shows down status with error message."""
        mock_cache = MagicMock()
        mock_cache.health_check.return_value = False

        with (
            patch(
                "techpulse.api.routes.health.get_session_manager",
                return_value=mock_db_manager,
            ),
            patch(
                "techpulse.api.routes.health.get_cache_service",
                return_value=mock_cache,
            ),
            patch(
                "techpulse.api.main.get_session_manager",
                return_value=mock_db_manager,
            ),
        ):
            client = TestClient(app, raise_server_exceptions=False)
            response = client.get("/health/ready")

        body = response.json()
        assert body["components"]["cache"]["status"] == "down"
        assert "error" in body["components"]["cache"]

    def test_database_still_shows_up_when_cache_fails(
        self,
        mock_db_manager: MagicMock,
    ) -> None:
        """Verify database shows up even when cache fails."""
        mock_cache = MagicMock()
        mock_cache.health_check.return_value = False

        with (
            patch(
                "techpulse.api.routes.health.get_session_manager",
                return_value=mock_db_manager,
            ),
            patch(
                "techpulse.api.routes.health.get_cache_service",
                return_value=mock_cache,
            ),
            patch(
                "techpulse.api.main.get_session_manager",
                return_value=mock_db_manager,
            ),
        ):
            client = TestClient(app, raise_server_exceptions=False)
            response = client.get("/health/ready")

        body = response.json()
        assert body["components"]["database"]["status"] == "up"


class TestReadinessEndpointCacheNotConfigured:
    """Test suite for GET /health/ready when cache is not configured."""

    def test_returns_503_when_cache_not_configured(
        self,
        mock_db_manager: MagicMock,
    ) -> None:
        """Verify readiness returns 503 when cache service is None."""
        with (
            patch(
                "techpulse.api.routes.health.get_session_manager",
                return_value=mock_db_manager,
            ),
            patch(
                "techpulse.api.routes.health.get_cache_service",
                return_value=None,
            ),
            patch(
                "techpulse.api.main.get_session_manager",
                return_value=mock_db_manager,
            ),
        ):
            client = TestClient(app, raise_server_exceptions=False)
            response = client.get("/health/ready")

        assert response.status_code == 503

    def test_cache_shows_not_configured_error(
        self,
        mock_db_manager: MagicMock,
    ) -> None:
        """Verify cache shows appropriate error when not configured."""
        with (
            patch(
                "techpulse.api.routes.health.get_session_manager",
                return_value=mock_db_manager,
            ),
            patch(
                "techpulse.api.routes.health.get_cache_service",
                return_value=None,
            ),
            patch(
                "techpulse.api.main.get_session_manager",
                return_value=mock_db_manager,
            ),
        ):
            client = TestClient(app, raise_server_exceptions=False)
            response = client.get("/health/ready")

        body = response.json()
        assert body["components"]["cache"]["status"] == "down"
        assert "not configured" in body["components"]["cache"]["error"]


class TestCheckDatabaseHealthFunction:
    """Test suite for _check_database_health helper function."""

    def test_returns_up_when_health_check_passes(self) -> None:
        """Verify returns ComponentHealthUp when health check succeeds."""
        mock_manager = MagicMock()
        mock_manager.health_check.return_value = True

        result = _check_database_health(mock_manager)

        assert isinstance(result, ComponentHealthUp)
        assert result.status == "up"

    def test_returns_down_when_health_check_fails(self) -> None:
        """Verify returns ComponentHealthDown when health check returns False."""
        mock_manager = MagicMock()
        mock_manager.health_check.return_value = False

        result = _check_database_health(mock_manager)

        assert isinstance(result, ComponentHealthDown)
        assert result.status == "down"

    def test_returns_down_with_exception_error(self) -> None:
        """Verify returns ComponentHealthDown with error on exception."""
        mock_manager = MagicMock()
        mock_manager.health_check.side_effect = Exception("Connection lost")

        result = _check_database_health(mock_manager)

        assert isinstance(result, ComponentHealthDown)
        assert "Connection lost" in result.error

    def test_measures_latency_on_success(self) -> None:
        """Verify latency_ms is present on successful check."""
        mock_manager = MagicMock()
        mock_manager.health_check.return_value = True

        result = _check_database_health(mock_manager)

        assert hasattr(result, "latency_ms")
        assert result.latency_ms >= 0


class TestCheckCacheHealthFunction:
    """Test suite for _check_cache_health helper function."""

    def test_returns_up_when_health_check_passes(self) -> None:
        """Verify returns ComponentHealthUp when health check succeeds."""
        mock_cache = MagicMock()
        mock_cache.health_check.return_value = True

        result = _check_cache_health(mock_cache)

        assert isinstance(result, ComponentHealthUp)
        assert result.status == "up"

    def test_returns_down_when_health_check_fails(self) -> None:
        """Verify returns ComponentHealthDown when health check returns False."""
        mock_cache = MagicMock()
        mock_cache.health_check.return_value = False

        result = _check_cache_health(mock_cache)

        assert isinstance(result, ComponentHealthDown)
        assert result.status == "down"

    def test_returns_down_when_cache_is_none(self) -> None:
        """Verify returns ComponentHealthDown when cache service is None."""
        result = _check_cache_health(None)

        assert isinstance(result, ComponentHealthDown)
        assert "not configured" in result.error

    def test_returns_down_with_exception_error(self) -> None:
        """Verify returns ComponentHealthDown with error on exception."""
        mock_cache = MagicMock()
        mock_cache.health_check.side_effect = Exception("Redis unavailable")

        result = _check_cache_health(mock_cache)

        assert isinstance(result, ComponentHealthDown)
        assert "Redis unavailable" in result.error

    def test_measures_latency_on_success(self) -> None:
        """Verify latency_ms is present on successful check."""
        mock_cache = MagicMock()
        mock_cache.health_check.return_value = True

        result = _check_cache_health(mock_cache)

        assert hasattr(result, "latency_ms")
        assert result.latency_ms >= 0


class TestExecuteWithTimeout:
    """Test suite for _execute_with_timeout helper function."""

    def test_returns_result_when_within_timeout(self) -> None:
        """Verify returns check result when completed within timeout."""

        def quick_check() -> ComponentHealthUp:
            return ComponentHealthUp(latency_ms=1.0)

        result = _execute_with_timeout(quick_check, timeout_seconds=1.0)

        assert isinstance(result, ComponentHealthUp)
        assert result.latency_ms == 1.0

    def test_returns_down_when_timeout_exceeded(self) -> None:
        """Verify returns ComponentHealthDown when timeout is exceeded."""

        def slow_check() -> ComponentHealthUp:
            time.sleep(0.5)
            return ComponentHealthUp(latency_ms=500.0)

        result = _execute_with_timeout(slow_check, timeout_seconds=0.1)

        assert isinstance(result, ComponentHealthDown)
        assert "timed out" in result.error

    def test_timeout_error_includes_duration(self) -> None:
        """Verify timeout error message includes the timeout duration."""

        def slow_check() -> ComponentHealthUp:
            time.sleep(1.0)
            return ComponentHealthUp(latency_ms=1000.0)

        result = _execute_with_timeout(slow_check, timeout_seconds=0.1)

        assert "0.1s" in result.error


class TestHealthCheckTimeoutConstant:
    """Test suite for health check timeout configuration."""

    def test_timeout_is_two_seconds(self) -> None:
        """Verify health check timeout is 2 seconds as per Epic spec."""
        assert HEALTH_CHECK_TIMEOUT_SECONDS == 2.0


class TestReadinessEndpointLogging:
    """Test suite for readiness endpoint logging behavior."""

    def test_logs_warning_on_failure(
        self,
        mock_db_manager: MagicMock,
    ) -> None:
        """Verify warning logged when readiness check fails."""
        mock_cache = MagicMock()
        mock_cache.health_check.return_value = False

        with (
            patch(
                "techpulse.api.routes.health.get_session_manager",
                return_value=mock_db_manager,
            ),
            patch(
                "techpulse.api.routes.health.get_cache_service",
                return_value=mock_cache,
            ),
            patch(
                "techpulse.api.main.get_session_manager",
                return_value=mock_db_manager,
            ),
            patch("techpulse.api.routes.health.logger") as mock_logger,
        ):
            client = TestClient(app, raise_server_exceptions=False)
            client.get("/health/ready")

        mock_logger.warning.assert_called_once()
        call_args = mock_logger.warning.call_args
        assert call_args[0][0] == "readiness_check_failed"

    def test_logs_info_on_success(
        self,
        client_all_healthy: TestClient,
    ) -> None:
        """Verify info logged when readiness check passes."""
        with patch("techpulse.api.routes.health.logger") as mock_logger:
            with (
                patch(
                    "techpulse.api.routes.health.get_session_manager",
                ) as mock_get_db,
                patch(
                    "techpulse.api.routes.health.get_cache_service",
                ) as mock_get_cache,
            ):
                mock_db = MagicMock()
                mock_db.health_check.return_value = True
                mock_get_db.return_value = mock_db

                mock_cache = MagicMock()
                mock_cache.health_check.return_value = True
                mock_get_cache.return_value = mock_cache

                client = TestClient(app, raise_server_exceptions=False)
                client.get("/health/ready")

        mock_logger.info.assert_called()


class TestHealthEndpointRegistration:
    """Test suite for health endpoint registration."""

    def test_live_endpoint_registered(self) -> None:
        """Verify /health/live endpoint is registered."""
        routes = [route.path for route in app.routes]
        assert "/health/live" in routes

    def test_ready_endpoint_registered(self) -> None:
        """Verify /health/ready endpoint is registered."""
        routes = [route.path for route in app.routes]
        assert "/health/ready" in routes

    def test_endpoints_accept_get_method(self) -> None:
        """Verify health endpoints accept GET method."""
        client = TestClient(app, raise_server_exceptions=False)

        live_post = client.post("/health/live")
        ready_post = client.post("/health/ready")

        assert live_post.status_code == 405
        assert ready_post.status_code == 405
