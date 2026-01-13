"""Unit tests for TechnologyDAO class."""

from typing import Generator

import duckdb
import pytest

from techpulse.api.dao.technology import TechnologyDAO
from techpulse.api.exceptions.domain import QueryExecutionError
from techpulse.api.schemas.technology import Technology


@pytest.fixture
def temp_db_with_taxonomy() -> Generator[duckdb.DuckDBPyConnection, None, None]:
    """Create a temporary in-memory DuckDB with test taxonomy data."""
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
        ('postgresql', 'PostgreSQL', 'Database', '\\b(postgresql)\\b'),
        ('aws', 'AWS', 'Cloud', '\\b(aws)\\b'),
        ('orphan_tech', 'Orphan', 'Tool', '\\b(orphan)\\b')
    """)

    conn.execute("""
        INSERT INTO mart_monthly_trends VALUES
        ('2024-01-01', 'python', 'Python', 100, 1000, 0.10, NULL, NULL),
        ('2024-01-01', 'react', 'React', 80, 1000, 0.08, NULL, NULL),
        ('2024-01-01', 'postgresql', 'PostgreSQL', 50, 1000, 0.05, NULL, NULL),
        ('2024-02-01', 'python', 'Python', 110, 1100, 0.10, 0.0, NULL),
        ('2024-02-01', 'react', 'React', 90, 1100, 0.08, 0.0, NULL),
        ('2024-02-01', 'aws', 'AWS', 70, 1100, 0.06, NULL, NULL)
    """)

    yield conn
    conn.close()


@pytest.fixture
def technology_dao(
    temp_db_with_taxonomy: duckdb.DuckDBPyConnection,
) -> TechnologyDAO:
    """Create a TechnologyDAO instance with test connection."""
    cursor = temp_db_with_taxonomy.cursor()
    return TechnologyDAO(cursor)


class TestTechnologyDAOListAll:
    """Test suite for TechnologyDAO.list_all method."""

    def test_list_all_returns_list_of_technology_objects(
        self, technology_dao: TechnologyDAO
    ) -> None:
        """Verify list_all returns a list of Technology instances."""
        result = technology_dao.list_all()
        assert isinstance(result, list)
        assert all(isinstance(item, Technology) for item in result)

    def test_list_all_returns_correct_count(
        self, technology_dao: TechnologyDAO
    ) -> None:
        """Verify list_all returns only technologies present in mart_monthly_trends."""
        result = technology_dao.list_all()
        assert len(result) == 4

    def test_list_all_excludes_orphan_technologies(
        self, technology_dao: TechnologyDAO
    ) -> None:
        """Verify technologies not in mart_monthly_trends are excluded."""
        result = technology_dao.list_all()
        keys = [tech.key for tech in result]
        assert "orphan_tech" not in keys

    def test_list_all_sorted_alphabetically_by_name(
        self, technology_dao: TechnologyDAO
    ) -> None:
        """Verify results are sorted alphabetically by display name."""
        result = technology_dao.list_all()
        names = [tech.name for tech in result]
        assert names == sorted(names)

    def test_list_all_returns_correct_fields(
        self, technology_dao: TechnologyDAO
    ) -> None:
        """Verify each Technology has correct key, name, and category."""
        result = technology_dao.list_all()
        python = next((t for t in result if t.key == "python"), None)

        assert python is not None
        assert python.key == "python"
        assert python.name == "Python"
        assert python.category == "Language"

    def test_list_all_returns_all_categories(
        self, technology_dao: TechnologyDAO
    ) -> None:
        """Verify technologies from different categories are returned."""
        result = technology_dao.list_all()
        categories = {tech.category for tech in result}
        assert categories == {"Language", "Framework", "Database", "Cloud"}

    def test_list_all_returns_distinct_technologies(
        self, technology_dao: TechnologyDAO
    ) -> None:
        """Verify duplicate entries in mart_monthly_trends yield single result."""
        result = technology_dao.list_all()
        keys = [tech.key for tech in result]
        assert len(keys) == len(set(keys))

    def test_list_all_with_empty_trends_table(
        self, temp_db_with_taxonomy: duckdb.DuckDBPyConnection
    ) -> None:
        """Verify list_all returns empty list when mart_monthly_trends is empty."""
        temp_db_with_taxonomy.execute("DELETE FROM mart_monthly_trends")
        cursor = temp_db_with_taxonomy.cursor()
        dao = TechnologyDAO(cursor)

        result = dao.list_all()
        assert result == []


class TestTechnologyDAOErrorHandling:
    """Test suite for TechnologyDAO error handling."""

    def test_list_all_raises_on_missing_table(
        self, temp_db_with_taxonomy: duckdb.DuckDBPyConnection
    ) -> None:
        """Verify QueryExecutionError raised when mart_monthly_trends missing."""
        temp_db_with_taxonomy.execute("DROP TABLE mart_monthly_trends")
        cursor = temp_db_with_taxonomy.cursor()
        dao = TechnologyDAO(cursor)

        with pytest.raises(QueryExecutionError):
            dao.list_all()

    def test_list_all_raises_on_missing_taxonomy_table(
        self, temp_db_with_taxonomy: duckdb.DuckDBPyConnection
    ) -> None:
        """Verify QueryExecutionError raised when tech_taxonomy missing."""
        temp_db_with_taxonomy.execute("DROP TABLE tech_taxonomy")
        cursor = temp_db_with_taxonomy.cursor()
        dao = TechnologyDAO(cursor)

        with pytest.raises(QueryExecutionError):
            dao.list_all()
