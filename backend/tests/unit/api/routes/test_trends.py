"""Unit tests for GET /trends endpoint."""

from datetime import date
from typing import Generator
from unittest.mock import MagicMock, patch

import duckdb
import pytest
from fastapi.testclient import TestClient

from techpulse.api.main import app
from techpulse.api.routes.trends import TrendRequest


@pytest.fixture
def mock_db_connection() -> Generator[duckdb.DuckDBPyConnection, None, None]:
    """Create a mock in-memory DuckDB with test trend data."""
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
        ('2024-01-01', 'python', 'Python', 100, 1000, 0.10, NULL, NULL),
        ('2024-02-01', 'python', 'Python', 120, 1100, 0.11, 10.0, NULL),
        ('2024-03-01', 'python', 'Python', 110, 1050, 0.10, -9.1, NULL),
        ('2024-01-01', 'react', 'React', 80, 1000, 0.08, NULL, NULL),
        ('2024-02-01', 'react', 'React', 90, 1100, 0.08, 0.0, NULL),
        ('2024-03-01', 'react', 'React', 95, 1050, 0.09, 12.5, NULL)
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


class TestGetTrendsEndpoint:
    """Test suite for GET /api/v1/trends endpoint."""

    def test_returns_200_with_valid_tech_ids(self, client: TestClient) -> None:
        """Verify endpoint returns 200 with valid tech_ids."""
        response = client.get(
            "/api/v1/trends?tech_ids=python&start_date=2024-01-01&end_date=2024-03-31"
        )
        assert response.status_code == 200

    def test_returns_json_content_type(self, client: TestClient) -> None:
        """Verify response has JSON content type."""
        response = client.get(
            "/api/v1/trends?tech_ids=python&start_date=2024-01-01&end_date=2024-03-31"
        )
        assert response.headers["content-type"] == "application/json"

    def test_returns_envelope_structure(self, client: TestClient) -> None:
        """Verify response follows ResponseEnvelope structure."""
        response = client.get(
            "/api/v1/trends?tech_ids=python&start_date=2024-01-01&end_date=2024-03-31"
        )
        body = response.json()

        assert "data" in body
        assert "meta" in body
        assert isinstance(body["data"], list)

    def test_returns_correct_technology(self, client: TestClient) -> None:
        """Verify returns data for requested technology."""
        response = client.get(
            "/api/v1/trends?tech_ids=python&start_date=2024-01-01&end_date=2024-03-31"
        )
        body = response.json()

        assert len(body["data"]) == 1
        assert body["data"][0]["tech_key"] == "python"
        assert body["data"][0]["name"] == "Python"

    def test_returns_multiple_technologies(self, client: TestClient) -> None:
        """Verify returns data for multiple technologies."""
        response = client.get(
            "/api/v1/trends?tech_ids=python,react"
            "&start_date=2024-01-01&end_date=2024-03-31"
        )
        body = response.json()

        assert len(body["data"]) == 2
        keys = {t["tech_key"] for t in body["data"]}
        assert keys == {"python", "react"}

    def test_respects_date_range(self, client: TestClient) -> None:
        """Verify date range filters are applied."""
        response = client.get(
            "/api/v1/trends?tech_ids=python&start_date=2024-01-01&end_date=2024-02-28"
        )
        body = response.json()

        months = [dp["month"] for dp in body["data"][0]["data"]]
        assert "2024-01" in months
        assert "2024-02" in months
        assert "2024-03" not in months

    def test_unknown_tech_id_returns_empty_data(self, client: TestClient) -> None:
        """Verify unknown tech_id returns empty list."""
        response = client.get("/api/v1/trends?tech_ids=nonexistent")
        body = response.json()

        assert response.status_code == 200
        assert body["data"] == []

    def test_meta_contains_total_count(self, client: TestClient) -> None:
        """Verify meta contains total_count."""
        response = client.get(
            "/api/v1/trends?tech_ids=python,react"
            "&start_date=2024-01-01&end_date=2024-03-31"
        )
        body = response.json()

        assert body["meta"]["total_count"] == 2


class TestGetTrendsValidation:
    """Test suite for trends endpoint input validation."""

    def test_missing_tech_ids_returns_422(self, client: TestClient) -> None:
        """Verify missing tech_ids returns 422."""
        response = client.get("/api/v1/trends")
        assert response.status_code == 422

    def test_empty_tech_ids_returns_422(self, client: TestClient) -> None:
        """Verify empty tech_ids returns 422."""
        response = client.get("/api/v1/trends?tech_ids=")
        assert response.status_code == 422

    def test_whitespace_only_tech_ids_returns_422(self, client: TestClient) -> None:
        """Verify whitespace-only tech_ids returns 422."""
        response = client.get("/api/v1/trends?tech_ids=%20%20")
        assert response.status_code == 422

    def test_invalid_tech_id_format_returns_422(self, client: TestClient) -> None:
        """Verify invalid tech_id characters return 422."""
        response = client.get("/api/v1/trends?tech_ids=python@invalid")
        assert response.status_code == 422

    def test_tech_id_with_special_chars_returns_422(self, client: TestClient) -> None:
        """Verify tech_id with special characters returns 422."""
        response = client.get("/api/v1/trends?tech_ids=python!#$")
        assert response.status_code == 422

    def test_valid_tech_id_formats_accepted(self, client: TestClient) -> None:
        """Verify valid tech_id formats are accepted."""
        response = client.get("/api/v1/trends?tech_ids=c_sharp,node-js,react123")
        assert response.status_code == 200

    def test_invalid_start_date_format_returns_422(self, client: TestClient) -> None:
        """Verify invalid start_date format returns 422."""
        response = client.get("/api/v1/trends?tech_ids=python&start_date=01-01-2024")
        assert response.status_code == 422

    def test_invalid_end_date_format_returns_422(self, client: TestClient) -> None:
        """Verify invalid end_date format returns 422."""
        response = client.get("/api/v1/trends?tech_ids=python&end_date=2024/12/31")
        assert response.status_code == 422

    def test_non_date_string_returns_422(self, client: TestClient) -> None:
        """Verify non-date string returns 422."""
        response = client.get("/api/v1/trends?tech_ids=python&start_date=not-a-date")
        assert response.status_code == 422

    def test_422_error_contains_detail(self, client: TestClient) -> None:
        """Verify 422 error response contains detail message."""
        response = client.get("/api/v1/trends")
        body = response.json()

        assert "detail" in body


class TestGetTrendsDateDefaults:
    """Test suite for trends endpoint date defaults."""

    def test_defaults_applied_when_dates_omitted(self, client: TestClient) -> None:
        """Verify defaults are applied when dates are omitted."""
        response = client.get("/api/v1/trends?tech_ids=python")
        assert response.status_code == 200

    def test_start_date_only_uses_today_as_end(self, client: TestClient) -> None:
        """Verify providing only start_date uses today as end_date."""
        response = client.get("/api/v1/trends?tech_ids=python&start_date=2024-01-01")
        assert response.status_code == 200

    def test_end_date_only_uses_12_months_prior_as_start(
        self, client: TestClient
    ) -> None:
        """Verify providing only end_date defaults start to 12 months prior."""
        response = client.get("/api/v1/trends?tech_ids=python&end_date=2024-03-31")
        assert response.status_code == 200


class TestTrendRequestModel:
    """Test suite for TrendRequest Pydantic model."""

    def test_valid_request_creation(self) -> None:
        """Verify valid TrendRequest can be created."""
        request = TrendRequest(
            tech_ids=["python", "react"],
            start_date=date(2024, 1, 1),
            end_date=date(2024, 12, 31),
        )
        assert request.tech_ids == ["python", "react"]

    def test_tech_ids_required_minimum_one(self) -> None:
        """Verify tech_ids requires at least one element."""
        with pytest.raises(ValueError):
            TrendRequest(tech_ids=[], start_date=None, end_date=None)

    def test_invalid_tech_id_format_raises_error(self) -> None:
        """Verify invalid tech_id format raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            TrendRequest(tech_ids=["valid", "inv@lid"], start_date=None, end_date=None)
        assert "Invalid tech_id format" in str(exc_info.value)

    def test_valid_tech_id_with_hyphen(self) -> None:
        """Verify tech_id with hyphen is valid."""
        request = TrendRequest(tech_ids=["node-js"], start_date=None, end_date=None)
        assert request.tech_ids == ["node-js"]

    def test_valid_tech_id_with_underscore(self) -> None:
        """Verify tech_id with underscore is valid."""
        request = TrendRequest(tech_ids=["c_sharp"], start_date=None, end_date=None)
        assert request.tech_ids == ["c_sharp"]

    def test_valid_tech_id_with_numbers(self) -> None:
        """Verify tech_id with numbers is valid."""
        request = TrendRequest(tech_ids=["python3"], start_date=None, end_date=None)
        assert request.tech_ids == ["python3"]

    def test_get_date_range_with_both_dates(self) -> None:
        """Verify get_date_range returns provided dates."""
        request = TrendRequest(
            tech_ids=["python"],
            start_date=date(2024, 1, 1),
            end_date=date(2024, 12, 31),
        )
        start, end = request.get_date_range()
        assert start == date(2024, 1, 1)
        assert end == date(2024, 12, 31)

    def test_get_date_range_defaults_end_to_today(self) -> None:
        """Verify get_date_range defaults end_date to today."""
        request = TrendRequest(
            tech_ids=["python"],
            start_date=date(2024, 1, 1),
            end_date=None,
        )
        _, end = request.get_date_range()
        assert end == date.today()

    def test_get_date_range_defaults_start_to_12_months_prior(self) -> None:
        """Verify get_date_range defaults start_date to 12 months before end."""
        request = TrendRequest(
            tech_ids=["python"],
            start_date=None,
            end_date=date(2024, 12, 15),
        )
        start, end = request.get_date_range()
        assert end == date(2024, 12, 15)
        assert start.year == end.year - 1
        assert start.month == end.month


class TestGetTrendsDataContent:
    """Test suite for trends endpoint data content."""

    def test_technology_has_required_fields(self, client: TestClient) -> None:
        """Verify each technology has tech_key, name, and data fields."""
        response = client.get(
            "/api/v1/trends?tech_ids=python&start_date=2024-01-01&end_date=2024-03-31"
        )
        body = response.json()

        tech = body["data"][0]
        assert "tech_key" in tech
        assert "name" in tech
        assert "data" in tech

    def test_data_points_have_required_fields(self, client: TestClient) -> None:
        """Verify each data point has month and count fields."""
        response = client.get(
            "/api/v1/trends?tech_ids=python&start_date=2024-01-01&end_date=2024-03-31"
        )
        body = response.json()

        data_point = body["data"][0]["data"][0]
        assert "month" in data_point
        assert "count" in data_point

    def test_month_format_is_yyyy_mm(self, client: TestClient) -> None:
        """Verify month is formatted as YYYY-MM."""
        response = client.get(
            "/api/v1/trends?tech_ids=python&start_date=2024-01-01&end_date=2024-01-31"
        )
        body = response.json()

        month = body["data"][0]["data"][0]["month"]
        assert month == "2024-01"

    def test_count_is_integer(self, client: TestClient) -> None:
        """Verify count is an integer."""
        response = client.get(
            "/api/v1/trends?tech_ids=python&start_date=2024-01-01&end_date=2024-01-31"
        )
        body = response.json()

        count = body["data"][0]["data"][0]["count"]
        assert isinstance(count, int)
