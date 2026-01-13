"""Integration tests for trends endpoint safety limits.

These tests verify that the API enforces safety bounds to prevent
resource exhaustion from unbounded queries.
"""

from typing import Generator
from unittest.mock import MagicMock, patch

import duckdb
import pytest
from fastapi.testclient import TestClient

from techpulse.api.main import app
from techpulse.api.routes.trends import MAX_DATE_RANGE_MONTHS, MAX_TECHNOLOGIES


@pytest.fixture
def mock_db_connection() -> Generator[duckdb.DuckDBPyConnection, None, None]:
    """Create a mock in-memory DuckDB with minimal test data."""
    conn = duckdb.connect(":memory:")

    conn.execute("""
        CREATE TABLE mart_monthly_trends (
            month DATE,
            tech_key VARCHAR,
            tech_name VARCHAR,
            mention_count BIGINT,
            total_jobs BIGINT,
            pct_share DOUBLE,
            mom_growth_pct DOUBLE,
            yoy_growth_pct DOUBLE
        )
    """)

    conn.execute("""
        INSERT INTO mart_monthly_trends VALUES
        ('2024-01-01', 'python', 'Python', 100, 1000, 0.10, NULL, NULL)
    """)

    yield conn
    conn.close()


@pytest.fixture
def client(mock_db_connection: duckdb.DuckDBPyConnection) -> TestClient:
    """Create a test client with mocked database connection."""
    mock_manager = MagicMock()
    mock_manager.get_cursor.return_value = mock_db_connection.cursor()
    mock_manager.health_check.return_value = True

    with (
        patch("techpulse.api.main.get_session_manager", return_value=mock_manager),
        patch(
            "techpulse.api.db.manager.get_session_manager", return_value=mock_manager
        ),
    ):
        yield TestClient(app)


class TestMaxTechnologiesLimit:
    """Test suite for maximum technologies per request limit."""

    def test_max_technologies_constant_is_10(self) -> None:
        """Verify MAX_TECHNOLOGIES constant is set to 10."""
        assert MAX_TECHNOLOGIES == 10

    def test_exactly_10_technologies_allowed(self, client: TestClient) -> None:
        """Verify exactly 10 technologies are accepted."""
        tech_ids = ",".join([f"tech{i}" for i in range(10)])
        response = client.get(
            f"/api/v1/trends?tech_ids={tech_ids}"
            "&start_date=2024-01-01&end_date=2024-01-31"
        )
        assert response.status_code == 200

    def test_11_technologies_returns_422(self, client: TestClient) -> None:
        """Verify 11 technologies returns 422."""
        tech_ids = ",".join([f"tech{i}" for i in range(11)])
        response = client.get(
            f"/api/v1/trends?tech_ids={tech_ids}"
            "&start_date=2024-01-01&end_date=2024-01-31"
        )
        assert response.status_code == 422

    def test_15_technologies_returns_422(self, client: TestClient) -> None:
        """Verify 15 technologies returns 422."""
        tech_ids = ",".join([f"tech{i}" for i in range(15)])
        response = client.get(
            f"/api/v1/trends?tech_ids={tech_ids}"
            "&start_date=2024-01-01&end_date=2024-01-31"
        )
        assert response.status_code == 422

    def test_error_message_indicates_limit(self, client: TestClient) -> None:
        """Verify error message indicates the limit was exceeded."""
        tech_ids = ",".join([f"tech{i}" for i in range(11)])
        response = client.get(
            f"/api/v1/trends?tech_ids={tech_ids}"
            "&start_date=2024-01-01&end_date=2024-01-31"
        )
        body = response.json()

        assert "detail" in body
        detail = body["detail"]
        assert "10" in detail["detail"]
        assert "11" in detail["detail"]

    def test_error_type_is_limit_exceeded(self, client: TestClient) -> None:
        """Verify error type is limit-exceeded."""
        tech_ids = ",".join([f"tech{i}" for i in range(11)])
        response = client.get(
            f"/api/v1/trends?tech_ids={tech_ids}"
            "&start_date=2024-01-01&end_date=2024-01-31"
        )
        body = response.json()

        assert body["detail"]["type"].endswith("limit-exceeded")

    def test_error_title_is_limit_exceeded(self, client: TestClient) -> None:
        """Verify error title is 'Limit Exceeded'."""
        tech_ids = ",".join([f"tech{i}" for i in range(11)])
        response = client.get(
            f"/api/v1/trends?tech_ids={tech_ids}"
            "&start_date=2024-01-01&end_date=2024-01-31"
        )
        body = response.json()

        assert body["detail"]["title"] == "Limit Exceeded"


class TestMaxDateRangeLimit:
    """Test suite for maximum date range limit."""

    def test_max_date_range_constant_is_60(self) -> None:
        """Verify MAX_DATE_RANGE_MONTHS constant is set to 60."""
        assert MAX_DATE_RANGE_MONTHS == 60

    def test_exactly_60_months_allowed(self, client: TestClient) -> None:
        """Verify exactly 60 months (5 years) are accepted."""
        response = client.get(
            "/api/v1/trends?tech_ids=python&start_date=2019-01-01&end_date=2024-01-01"
        )
        assert response.status_code == 200

    def test_61_months_returns_422(self, client: TestClient) -> None:
        """Verify 61 months returns 422."""
        response = client.get(
            "/api/v1/trends?tech_ids=python&start_date=2019-01-01&end_date=2024-02-01"
        )
        assert response.status_code == 422

    def test_10_years_returns_422(self, client: TestClient) -> None:
        """Verify 10 years (120 months) returns 422."""
        response = client.get(
            "/api/v1/trends?tech_ids=python&start_date=2014-01-01&end_date=2024-01-01"
        )
        assert response.status_code == 422

    def test_error_message_indicates_date_limit(self, client: TestClient) -> None:
        """Verify error message indicates the date range limit was exceeded."""
        response = client.get(
            "/api/v1/trends?tech_ids=python&start_date=2014-01-01&end_date=2024-01-01"
        )
        body = response.json()

        assert "detail" in body
        detail = body["detail"]
        assert "60" in detail["detail"]
        assert "months" in detail["detail"].lower()

    def test_error_shows_requested_range(self, client: TestClient) -> None:
        """Verify error message shows the requested range."""
        response = client.get(
            "/api/v1/trends?tech_ids=python&start_date=2014-01-01&end_date=2024-01-01"
        )
        body = response.json()

        detail = body["detail"]["detail"]
        assert "120" in detail

    def test_date_range_error_type_is_limit_exceeded(self, client: TestClient) -> None:
        """Verify date range error type is limit-exceeded."""
        response = client.get(
            "/api/v1/trends?tech_ids=python&start_date=2014-01-01&end_date=2024-01-01"
        )
        body = response.json()

        assert body["detail"]["type"].endswith("limit-exceeded")


class TestCombinedLimits:
    """Test suite for combined limit scenarios."""

    def test_valid_request_within_all_limits(self, client: TestClient) -> None:
        """Verify request within all limits succeeds."""
        tech_ids = ",".join([f"tech{i}" for i in range(5)])
        response = client.get(
            f"/api/v1/trends?tech_ids={tech_ids}"
            "&start_date=2024-01-01&end_date=2024-06-01"
        )
        assert response.status_code == 200

    def test_tech_limit_checked_before_date_limit(self, client: TestClient) -> None:
        """Verify technology limit is checked first (fails early)."""
        tech_ids = ",".join([f"tech{i}" for i in range(15)])
        response = client.get(
            f"/api/v1/trends?tech_ids={tech_ids}"
            "&start_date=2010-01-01&end_date=2024-01-01"
        )
        assert response.status_code == 422
        body = response.json()
        assert "technologies" in body["detail"]["detail"].lower()


class TestDefaultDateRangeWithLimits:
    """Test suite for default date range behavior with limits."""

    def test_default_12_months_within_limit(self, client: TestClient) -> None:
        """Verify default 12-month range is within the 60-month limit."""
        response = client.get("/api/v1/trends?tech_ids=python")
        assert response.status_code == 200

    def test_default_range_does_not_trigger_limit(self, client: TestClient) -> None:
        """Verify default range never triggers the date limit."""
        response = client.get("/api/v1/trends?tech_ids=python,react,node")
        assert response.status_code == 200
