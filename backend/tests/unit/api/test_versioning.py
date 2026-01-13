"""Unit tests for API versioning configuration."""

from unittest.mock import patch

from fastapi import APIRouter
from fastapi.testclient import TestClient

from techpulse.api.core.config import Settings
from techpulse.api.main import v1_router


class TestV1Router:
    """Test suite for v1 API router configuration."""

    def test_v1_router_has_correct_prefix(self) -> None:
        """Verify v1 router has /api/v1 prefix."""
        assert v1_router.prefix == "/api/v1"

    def test_v1_router_is_api_router(self) -> None:
        """Verify v1_router is an APIRouter instance."""
        assert isinstance(v1_router, APIRouter)


class TestHealthEndpointNotVersioned:
    """Test suite for health endpoint outside versioned prefix."""

    def test_health_at_root_path(self) -> None:
        """Verify health endpoint is at /health, not /api/v1/health."""
        with (
            patch("techpulse.api.main.get_settings") as mock_get_settings,
            patch("techpulse.api.main.init_session_manager"),
            patch("techpulse.api.main.close_session_manager"),
        ):
            mock_get_settings.return_value = Settings(
                cors_origins="http://localhost:3000",
                db_path="data/test.duckdb",
            )

            from techpulse.api.main import create_app

            test_app = create_app()
            client = TestClient(test_app)

            response = client.get("/health")
            assert response.status_code == 200

    def test_health_not_at_versioned_path(self) -> None:
        """Verify health endpoint is NOT at /api/v1/health."""
        with (
            patch("techpulse.api.main.get_settings") as mock_get_settings,
            patch("techpulse.api.main.init_session_manager"),
            patch("techpulse.api.main.close_session_manager"),
        ):
            mock_get_settings.return_value = Settings(
                cors_origins="http://localhost:3000",
                db_path="data/test.duckdb",
            )

            from techpulse.api.main import create_app

            test_app = create_app()
            client = TestClient(test_app)

            response = client.get("/api/v1/health")
            assert response.status_code == 404


class TestVersionedEndpoints:
    """Test suite for versioned endpoint mounting."""

    def test_endpoints_on_v1_router_have_prefix(self) -> None:
        """Verify endpoints added to v1_router get /api/v1 prefix."""
        with (
            patch("techpulse.api.main.get_settings") as mock_get_settings,
            patch("techpulse.api.main.init_session_manager"),
            patch("techpulse.api.main.close_session_manager"),
        ):
            mock_get_settings.return_value = Settings(
                cors_origins="http://localhost:3000",
                db_path="data/test.duckdb",
            )

            from techpulse.api.main import create_app, v1_router

            @v1_router.get("/test-endpoint")
            def test_endpoint() -> dict[str, str]:
                return {"message": "test"}

            test_app = create_app()
            client = TestClient(test_app)

            response = client.get("/api/v1/test-endpoint")
            assert response.status_code == 200
            assert response.json() == {"message": "test"}

    def test_v1_endpoint_not_at_root(self) -> None:
        """Verify v1 endpoints are NOT accessible at root path."""
        with (
            patch("techpulse.api.main.get_settings") as mock_get_settings,
            patch("techpulse.api.main.init_session_manager"),
            patch("techpulse.api.main.close_session_manager"),
        ):
            mock_get_settings.return_value = Settings(
                cors_origins="http://localhost:3000",
                db_path="data/test.duckdb",
            )

            from techpulse.api.main import create_app

            test_app = create_app()
            client = TestClient(test_app)

            response = client.get("/test-endpoint")
            assert response.status_code == 404


class TestAppConfiguration:
    """Test suite for application configuration."""

    def test_app_title(self) -> None:
        """Verify application title is set correctly."""
        with (
            patch("techpulse.api.main.get_settings") as mock_get_settings,
            patch("techpulse.api.main.init_session_manager"),
            patch("techpulse.api.main.close_session_manager"),
        ):
            mock_get_settings.return_value = Settings(
                cors_origins="http://localhost:3000",
                db_path="data/test.duckdb",
            )

            from techpulse.api.main import create_app

            test_app = create_app()
            assert test_app.title == "TechPulse API"

    def test_app_version(self) -> None:
        """Verify application version is set."""
        with (
            patch("techpulse.api.main.get_settings") as mock_get_settings,
            patch("techpulse.api.main.init_session_manager"),
            patch("techpulse.api.main.close_session_manager"),
        ):
            mock_get_settings.return_value = Settings(
                cors_origins="http://localhost:3000",
                db_path="data/test.duckdb",
            )

            from techpulse.api.main import create_app

            test_app = create_app()
            assert test_app.version == "1.0.0"

    def test_v1_router_included(self) -> None:
        """Verify v1 router is included in application."""
        with (
            patch("techpulse.api.main.get_settings") as mock_get_settings,
            patch("techpulse.api.main.init_session_manager"),
            patch("techpulse.api.main.close_session_manager"),
        ):
            mock_get_settings.return_value = Settings(
                cors_origins="http://localhost:3000",
                db_path="data/test.duckdb",
            )

            from techpulse.api.main import create_app

            test_app = create_app()
            route_paths = [route.path for route in test_app.routes]
            assert any("/api/v1" in path for path in route_paths)
