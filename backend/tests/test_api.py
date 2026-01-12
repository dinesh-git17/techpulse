"""Tests for TechPulse API endpoints."""

from techpulse.api.main import app, health


class TestHealthEndpoint:
    """Test suite for the health check endpoint."""

    def test_health_returns_ok_status(self) -> None:
        """Verify health endpoint returns ok status."""
        result = health()
        assert result["status"] == "ok"

    def test_health_returns_system_name(self) -> None:
        """Verify health endpoint returns correct system name."""
        result = health()
        assert result["system"] == "TechPulse"

    def test_health_response_structure(self) -> None:
        """Verify health endpoint returns expected keys."""
        result = health()
        assert set(result.keys()) == {"status", "system"}


class TestAppConfiguration:
    """Test suite for FastAPI application configuration."""

    def test_app_title(self) -> None:
        """Verify application title is set correctly."""
        assert app.title == "TechPulse API"

    def test_health_route_registered(self) -> None:
        """Verify health route is registered."""
        routes = [route.path for route in app.routes]
        assert "/health" in routes
