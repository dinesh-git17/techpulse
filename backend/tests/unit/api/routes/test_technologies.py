"""Unit tests for GET /technologies endpoint."""

from typing import Generator
from unittest.mock import MagicMock, patch

import duckdb
import pytest
from fastapi.testclient import TestClient

from techpulse.api.main import app


@pytest.fixture
def mock_db_connection() -> Generator[duckdb.DuckDBPyConnection, None, None]:
    """Create a mock in-memory DuckDB with test data."""
    conn = duckdb.connect(":memory:")

    conn.execute("""
        CREATE TABLE tech_taxonomy (
            tech_key VARCHAR PRIMARY KEY,
            display_name VARCHAR NOT NULL,
            category VARCHAR NOT NULL,
            regex_pattern VARCHAR
        )
    """)

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
        INSERT INTO tech_taxonomy VALUES
        ('python', 'Python', 'Language', '\\b(python)\\b'),
        ('react', 'React', 'Framework', '\\b(react)\\b'),
        ('postgresql', 'PostgreSQL', 'Database', '\\b(postgresql)\\b')
    """)

    conn.execute("""
        INSERT INTO mart_monthly_trends VALUES
        ('2024-01-01', 'python', 'Python', 100, 1000, 0.10, NULL, NULL),
        ('2024-01-01', 'react', 'React', 80, 1000, 0.08, NULL, NULL),
        ('2024-01-01', 'postgresql', 'PostgreSQL', 50, 1000, 0.05, NULL, NULL)
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


class TestListTechnologiesEndpoint:
    """Test suite for GET /api/v1/technologies endpoint."""

    def test_returns_200_status(self, client: TestClient) -> None:
        """Verify endpoint returns 200 OK."""
        response = client.get("/api/v1/technologies")
        assert response.status_code == 200

    def test_returns_json_content_type(self, client: TestClient) -> None:
        """Verify response has JSON content type."""
        response = client.get("/api/v1/technologies")
        assert response.headers["content-type"] == "application/json"

    def test_returns_envelope_structure(self, client: TestClient) -> None:
        """Verify response follows ResponseEnvelope structure."""
        response = client.get("/api/v1/technologies")
        body = response.json()

        assert "data" in body
        assert "meta" in body
        assert isinstance(body["data"], list)

    def test_returns_correct_technology_count(self, client: TestClient) -> None:
        """Verify correct number of technologies returned."""
        response = client.get("/api/v1/technologies")
        body = response.json()

        assert len(body["data"]) == 3
        assert body["meta"]["total_count"] == 3

    def test_technology_has_required_fields(self, client: TestClient) -> None:
        """Verify each technology has key, name, and category fields."""
        response = client.get("/api/v1/technologies")
        body = response.json()

        for tech in body["data"]:
            assert "key" in tech
            assert "name" in tech
            assert "category" in tech

    def test_technologies_sorted_alphabetically(self, client: TestClient) -> None:
        """Verify technologies are sorted by name."""
        response = client.get("/api/v1/technologies")
        body = response.json()

        names = [tech["name"] for tech in body["data"]]
        assert names == sorted(names)

    def test_meta_contains_request_id(self, client: TestClient) -> None:
        """Verify meta contains a request_id."""
        response = client.get("/api/v1/technologies")
        body = response.json()

        assert "request_id" in body["meta"]
        assert body["meta"]["request_id"] is not None

    def test_meta_contains_timestamp(self, client: TestClient) -> None:
        """Verify meta contains a timestamp."""
        response = client.get("/api/v1/technologies")
        body = response.json()

        assert "timestamp" in body["meta"]
        assert body["meta"]["timestamp"] is not None


class TestListTechnologiesResponseContent:
    """Test suite for GET /api/v1/technologies response content."""

    def test_python_technology_present(self, client: TestClient) -> None:
        """Verify Python technology is in the response."""
        response = client.get("/api/v1/technologies")
        body = response.json()

        python = next((t for t in body["data"] if t["key"] == "python"), None)
        assert python is not None
        assert python["name"] == "Python"
        assert python["category"] == "Language"

    def test_react_technology_present(self, client: TestClient) -> None:
        """Verify React technology is in the response."""
        response = client.get("/api/v1/technologies")
        body = response.json()

        react = next((t for t in body["data"] if t["key"] == "react"), None)
        assert react is not None
        assert react["name"] == "React"
        assert react["category"] == "Framework"

    def test_postgresql_technology_present(self, client: TestClient) -> None:
        """Verify PostgreSQL technology is in the response."""
        response = client.get("/api/v1/technologies")
        body = response.json()

        postgres = next((t for t in body["data"] if t["key"] == "postgresql"), None)
        assert postgres is not None
        assert postgres["name"] == "PostgreSQL"
        assert postgres["category"] == "Database"


class TestListTechnologiesEmptyDatabase:
    """Test suite for GET /api/v1/technologies with empty data."""

    def test_returns_empty_list_when_no_trends(
        self, mock_db_connection: duckdb.DuckDBPyConnection
    ) -> None:
        """Verify empty list returned when mart_monthly_trends is empty."""
        mock_db_connection.execute("DELETE FROM mart_monthly_trends")

        mock_manager = MagicMock()
        mock_manager.get_cursor.return_value = mock_db_connection.cursor()
        mock_manager.health_check.return_value = True

        with (
            patch("techpulse.api.main.get_session_manager", return_value=mock_manager),
            patch(
                "techpulse.api.db.manager.get_session_manager",
                return_value=mock_manager,
            ),
        ):
            client = TestClient(app)
            response = client.get("/api/v1/technologies")

        body = response.json()
        assert response.status_code == 200
        assert body["data"] == []
        assert body["meta"]["total_count"] == 0
