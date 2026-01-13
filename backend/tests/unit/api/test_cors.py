"""Unit tests for CORS configuration."""

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from techpulse.api.core.config import Settings


@pytest.fixture
def mock_settings_single_origin() -> Settings:
    """Create settings with a single CORS origin."""
    return Settings(
        cors_origins="http://localhost:3000",
        db_path="data/test.duckdb",
    )


@pytest.fixture
def mock_settings_multiple_origins() -> Settings:
    """Create settings with multiple CORS origins."""
    return Settings(
        cors_origins="http://localhost:3000,https://techpulse.dev,https://app.techpulse.dev",
        db_path="data/test.duckdb",
    )


class TestCORSMiddleware:
    """Test suite for CORS middleware configuration."""

    def test_cors_allows_configured_origin(self) -> None:
        """Verify CORS allows requests from configured origin."""
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

            response = client.get(
                "/health",
                headers={"Origin": "http://localhost:3000"},
            )

            assert response.status_code == 200
            assert (
                response.headers.get("access-control-allow-origin")
                == "http://localhost:3000"
            )

    def test_cors_preflight_request_handled(self) -> None:
        """Verify preflight OPTIONS requests are handled correctly."""
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

            response = client.options(
                "/health",
                headers={
                    "Origin": "http://localhost:3000",
                    "Access-Control-Request-Method": "GET",
                },
            )

            assert response.status_code == 200
            assert "access-control-allow-methods" in response.headers

    def test_cors_allows_credentials(self) -> None:
        """Verify CORS allows credentials."""
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

            response = client.get(
                "/health",
                headers={"Origin": "http://localhost:3000"},
            )

            assert response.headers.get("access-control-allow-credentials") == "true"

    def test_cors_allows_standard_methods(self) -> None:
        """Verify CORS allows standard HTTP methods."""
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

            response = client.options(
                "/health",
                headers={
                    "Origin": "http://localhost:3000",
                    "Access-Control-Request-Method": "POST",
                },
            )

            allowed_methods = response.headers.get("access-control-allow-methods", "")
            assert "GET" in allowed_methods
            assert "POST" in allowed_methods
            assert "PUT" in allowed_methods
            assert "DELETE" in allowed_methods


class TestCORSOriginsParsing:
    """Test suite for CORS origins parsing from environment."""

    def test_single_origin_parsed(self, mock_settings_single_origin: Settings) -> None:
        """Verify single origin is parsed correctly."""
        origins = mock_settings_single_origin.get_cors_origins_list()
        assert origins == ["http://localhost:3000"]

    def test_multiple_origins_parsed(
        self, mock_settings_multiple_origins: Settings
    ) -> None:
        """Verify multiple origins are parsed correctly."""
        origins = mock_settings_multiple_origins.get_cors_origins_list()
        assert len(origins) == 3
        assert "http://localhost:3000" in origins
        assert "https://techpulse.dev" in origins
        assert "https://app.techpulse.dev" in origins

    def test_whitespace_trimmed(self) -> None:
        """Verify whitespace is trimmed from origins."""
        settings = Settings(
            cors_origins=" http://localhost:3000 , https://example.com ",
            db_path="data/test.duckdb",
        )
        origins = settings.get_cors_origins_list()
        assert origins == ["http://localhost:3000", "https://example.com"]

    def test_default_origin_is_localhost(self) -> None:
        """Verify default CORS origin is localhost:3000."""
        settings = Settings(db_path="data/test.duckdb")
        origins = settings.get_cors_origins_list()
        assert origins == ["http://localhost:3000"]
