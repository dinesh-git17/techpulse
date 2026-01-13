"""Integration tests for cache purge endpoint.

These tests verify the POST /internal/cache/purge endpoint behavior
including authentication, pattern-based purging, and error handling.
"""

from typing import Generator
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from techpulse.api.main import app

TEST_API_KEY = "test-purge-api-key-12345"  # pragma: allowlist secret


@pytest.fixture
def mock_settings() -> Generator[MagicMock, None, None]:
    """Create mock settings with configured purge API key."""
    mock = MagicMock()
    mock.cache_purge_api_key = TEST_API_KEY
    mock.redis_url = None
    mock.cache_ttl_seconds = 86400
    mock.db_path = "data/techpulse.duckdb"
    mock.api_host = "0.0.0.0"
    mock.api_port = 8000
    mock.log_format = "console"
    mock.cors_origins = "http://localhost:3000"
    mock.get_cors_origins_list.return_value = ["http://localhost:3000"]
    yield mock


@pytest.fixture
def mock_cache_service() -> Generator[MagicMock, None, None]:
    """Create mock cache service for testing purge operations."""
    mock = MagicMock()
    mock.is_connected.return_value = True
    mock.delete_pattern.return_value = 5
    yield mock


@pytest.fixture
def client(
    mock_settings: MagicMock,
    mock_cache_service: MagicMock,
) -> Generator[TestClient, None, None]:
    """Create test client with mocked dependencies."""
    with (
        patch(
            "techpulse.api.routes.internal.get_settings",
            return_value=mock_settings,
        ),
        patch(
            "techpulse.api.routes.internal.get_cache_service",
            return_value=mock_cache_service,
        ),
    ):
        yield TestClient(app)


class TestCachePurgeAuthentication:
    """Test suite for cache purge endpoint authentication."""

    def test_missing_api_key_returns_401(
        self,
        mock_settings: MagicMock,
    ) -> None:
        """Verify missing X-API-Key header returns 401."""
        with patch(
            "techpulse.api.routes.internal.get_settings",
            return_value=mock_settings,
        ):
            client = TestClient(app)
            response = client.post("/internal/cache/purge")

        assert response.status_code == 401
        body = response.json()
        assert body["detail"]["title"] == "Unauthorized"
        assert "X-API-Key" in body["detail"]["detail"]

    def test_invalid_api_key_returns_401(
        self,
        mock_settings: MagicMock,
    ) -> None:
        """Verify invalid X-API-Key returns 401."""
        with patch(
            "techpulse.api.routes.internal.get_settings",
            return_value=mock_settings,
        ):
            client = TestClient(app)
            response = client.post(
                "/internal/cache/purge",
                headers={"X-API-Key": "wrong-key"},
            )

        assert response.status_code == 401
        body = response.json()
        assert body["detail"]["title"] == "Unauthorized"
        assert "Invalid API key" in body["detail"]["detail"]

    def test_unconfigured_api_key_returns_401(self) -> None:
        """Verify unconfigured purge API key returns 401."""
        mock_settings = MagicMock()
        mock_settings.cache_purge_api_key = None

        with patch(
            "techpulse.api.routes.internal.get_settings",
            return_value=mock_settings,
        ):
            client = TestClient(app)
            response = client.post(
                "/internal/cache/purge",
                headers={"X-API-Key": "any-key"},
            )

        assert response.status_code == 401
        body = response.json()
        assert "not configured" in body["detail"]["detail"]

    def test_valid_api_key_returns_200(
        self,
        client: TestClient,
    ) -> None:
        """Verify valid X-API-Key returns 200."""
        response = client.post(
            "/internal/cache/purge",
            headers={"X-API-Key": TEST_API_KEY},
        )

        assert response.status_code == 200

    def test_error_type_is_unauthorized(
        self,
        mock_settings: MagicMock,
    ) -> None:
        """Verify error type is unauthorized for auth failures."""
        with patch(
            "techpulse.api.routes.internal.get_settings",
            return_value=mock_settings,
        ):
            client = TestClient(app)
            response = client.post(
                "/internal/cache/purge",
                headers={"X-API-Key": "wrong-key"},
            )

        body = response.json()
        assert body["detail"]["type"].endswith("unauthorized")


class TestCachePurgeAllKeys:
    """Test suite for purging all cache keys."""

    def test_purge_all_without_pattern(
        self,
        client: TestClient,
        mock_cache_service: MagicMock,
    ) -> None:
        """Verify purge without pattern clears all keys."""
        response = client.post(
            "/internal/cache/purge",
            headers={"X-API-Key": TEST_API_KEY},
        )

        assert response.status_code == 200
        mock_cache_service.delete_pattern.assert_called_once_with("tp:v1:*")

    def test_purge_all_returns_count(
        self,
        client: TestClient,
        mock_cache_service: MagicMock,
    ) -> None:
        """Verify purge response contains purged count."""
        mock_cache_service.delete_pattern.return_value = 42

        response = client.post(
            "/internal/cache/purge",
            headers={"X-API-Key": TEST_API_KEY},
        )

        body = response.json()
        assert body["purged_count"] == 42
        assert body["pattern"] == "tp:v1:*"

    def test_purge_with_empty_body(
        self,
        client: TestClient,
        mock_cache_service: MagicMock,
    ) -> None:
        """Verify purge with empty JSON body purges all keys."""
        response = client.post(
            "/internal/cache/purge",
            headers={"X-API-Key": TEST_API_KEY},
            json={},
        )

        assert response.status_code == 200
        mock_cache_service.delete_pattern.assert_called_once_with("tp:v1:*")


class TestCachePurgeWithPattern:
    """Test suite for targeted cache purging with patterns."""

    def test_purge_trends_endpoint(
        self,
        client: TestClient,
        mock_cache_service: MagicMock,
    ) -> None:
        """Verify purge with trends pattern targets correct keys."""
        response = client.post(
            "/internal/cache/purge",
            headers={"X-API-Key": TEST_API_KEY},
            json={"pattern": "trends"},
        )

        assert response.status_code == 200
        mock_cache_service.delete_pattern.assert_called_once_with("tp:v1:trends:*")

    def test_purge_technologies_endpoint(
        self,
        client: TestClient,
        mock_cache_service: MagicMock,
    ) -> None:
        """Verify purge with technologies pattern targets correct keys."""
        response = client.post(
            "/internal/cache/purge",
            headers={"X-API-Key": TEST_API_KEY},
            json={"pattern": "technologies"},
        )

        assert response.status_code == 200
        mock_cache_service.delete_pattern.assert_called_once_with(
            "tp:v1:technologies:*"
        )

    def test_purge_pattern_returns_in_response(
        self,
        client: TestClient,
        mock_cache_service: MagicMock,
    ) -> None:
        """Verify response contains the pattern used for purging."""
        mock_cache_service.delete_pattern.return_value = 10

        response = client.post(
            "/internal/cache/purge",
            headers={"X-API-Key": TEST_API_KEY},
            json={"pattern": "trends"},
        )

        body = response.json()
        assert body["pattern"] == "tp:v1:trends:*"
        assert body["purged_count"] == 10


class TestCachePurgeWhenCacheDisconnected:
    """Test suite for cache purge behavior when cache is unavailable."""

    def test_purge_returns_zero_when_cache_not_connected(
        self,
        mock_settings: MagicMock,
    ) -> None:
        """Verify purge returns zero count when cache is disconnected."""
        mock_cache = MagicMock()
        mock_cache.is_connected.return_value = False

        with (
            patch(
                "techpulse.api.routes.internal.get_settings",
                return_value=mock_settings,
            ),
            patch(
                "techpulse.api.routes.internal.get_cache_service",
                return_value=mock_cache,
            ),
        ):
            client = TestClient(app)
            response = client.post(
                "/internal/cache/purge",
                headers={"X-API-Key": TEST_API_KEY},
            )

        assert response.status_code == 200
        body = response.json()
        assert body["purged_count"] == 0
        mock_cache.delete_pattern.assert_not_called()

    def test_purge_returns_zero_when_cache_service_none(
        self,
        mock_settings: MagicMock,
    ) -> None:
        """Verify purge returns zero count when cache service is None."""
        with (
            patch(
                "techpulse.api.routes.internal.get_settings",
                return_value=mock_settings,
            ),
            patch(
                "techpulse.api.routes.internal.get_cache_service",
                return_value=None,
            ),
        ):
            client = TestClient(app)
            response = client.post(
                "/internal/cache/purge",
                headers={"X-API-Key": TEST_API_KEY},
            )

        assert response.status_code == 200
        body = response.json()
        assert body["purged_count"] == 0


class TestCachePurgeLogging:
    """Test suite for cache purge logging behavior."""

    def test_successful_purge_logs_completion(
        self,
        client: TestClient,
        mock_cache_service: MagicMock,
    ) -> None:
        """Verify successful purge logs completion event."""
        mock_cache_service.delete_pattern.return_value = 15

        with patch("techpulse.api.routes.internal.logger") as mock_logger:
            response = client.post(
                "/internal/cache/purge",
                headers={"X-API-Key": TEST_API_KEY},
                json={"pattern": "trends"},
            )

        assert response.status_code == 200
        mock_logger.info.assert_called_with(
            "cache_purge_completed",
            pattern="tp:v1:trends:*",
            purged_count=15,
        )

    def test_invalid_key_logs_rejection(
        self,
        mock_settings: MagicMock,
    ) -> None:
        """Verify invalid API key logs rejection event."""
        with (
            patch(
                "techpulse.api.routes.internal.get_settings",
                return_value=mock_settings,
            ),
            patch("techpulse.api.routes.internal.logger") as mock_logger,
        ):
            client = TestClient(app)
            client.post(
                "/internal/cache/purge",
                headers={"X-API-Key": "wrong-key"},
            )

        mock_logger.warning.assert_called_with(
            "cache_purge_rejected",
            reason="invalid_api_key",
        )

    def test_missing_key_logs_rejection(
        self,
        mock_settings: MagicMock,
    ) -> None:
        """Verify missing API key logs rejection event."""
        with (
            patch(
                "techpulse.api.routes.internal.get_settings",
                return_value=mock_settings,
            ),
            patch("techpulse.api.routes.internal.logger") as mock_logger,
        ):
            client = TestClient(app)
            client.post("/internal/cache/purge")

        mock_logger.warning.assert_called_with(
            "cache_purge_rejected",
            reason="missing_api_key",
        )


class TestCachePurgeEndpointMetadata:
    """Test suite for endpoint metadata and documentation."""

    def test_endpoint_exists_at_correct_path(self) -> None:
        """Verify endpoint is registered at /internal/cache/purge."""
        routes = [route.path for route in app.routes]
        assert "/internal/cache/purge" in routes

    def test_endpoint_accepts_post_method(self, client: TestClient) -> None:
        """Verify endpoint accepts POST method."""
        response = client.get("/internal/cache/purge")
        assert response.status_code == 405

    def test_response_model_has_required_fields(
        self,
        client: TestClient,
    ) -> None:
        """Verify response contains all required fields."""
        response = client.post(
            "/internal/cache/purge",
            headers={"X-API-Key": TEST_API_KEY},
        )

        body = response.json()
        assert "purged_count" in body
        assert "pattern" in body
        assert isinstance(body["purged_count"], int)
        assert isinstance(body["pattern"], str)
