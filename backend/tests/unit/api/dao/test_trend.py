"""Unit tests for TrendDAO class."""

from datetime import date
from typing import Generator

import duckdb
import pytest

from techpulse.api.dao.trend import TrendDAO
from techpulse.api.exceptions.domain import QueryExecutionError
from techpulse.api.schemas.trend import TechnologyTrend, TrendDataPoint


@pytest.fixture
def temp_db_with_trends() -> Generator[duckdb.DuckDBPyConnection, None, None]:
    """Create a temporary in-memory DuckDB with test trend data."""
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
        ('2024-03-01', 'react', 'React', 95, 1050, 0.09, 12.5, NULL),
        ('2024-01-01', 'postgresql', 'PostgreSQL', 50, 1000, 0.05, NULL, NULL),
        ('2024-02-01', 'postgresql', 'PostgreSQL', NULL, 1100, NULL, NULL, NULL),
        ('2024-03-01', 'postgresql', 'PostgreSQL', 60, 1050, 0.06, NULL, NULL),
        ('2023-12-01', 'python', 'Python', 95, 950, 0.10, NULL, NULL),
        ('2024-04-01', 'python', 'Python', 130, 1200, 0.11, 10.0, NULL)
    """)

    yield conn
    conn.close()


@pytest.fixture
def trend_dao(temp_db_with_trends: duckdb.DuckDBPyConnection) -> TrendDAO:
    """Create a TrendDAO instance with test connection."""
    cursor = temp_db_with_trends.cursor()
    return TrendDAO(cursor)


class TestTrendDAOGetTrends:
    """Test suite for TrendDAO.get_trends method."""

    def test_get_trends_returns_list_of_technology_trend(
        self, trend_dao: TrendDAO
    ) -> None:
        """Verify get_trends returns list of TechnologyTrend objects."""
        result = trend_dao.get_trends(
            tech_keys=["python"],
            start_date=date(2024, 1, 1),
            end_date=date(2024, 3, 31),
        )
        assert isinstance(result, list)
        assert all(isinstance(item, TechnologyTrend) for item in result)

    def test_get_trends_returns_correct_technology(self, trend_dao: TrendDAO) -> None:
        """Verify get_trends returns data for requested technology."""
        result = trend_dao.get_trends(
            tech_keys=["python"],
            start_date=date(2024, 1, 1),
            end_date=date(2024, 3, 31),
        )
        assert len(result) == 1
        assert result[0].tech_key == "python"
        assert result[0].name == "Python"

    def test_get_trends_returns_multiple_technologies(
        self, trend_dao: TrendDAO
    ) -> None:
        """Verify get_trends returns data for multiple technologies."""
        result = trend_dao.get_trends(
            tech_keys=["python", "react"],
            start_date=date(2024, 1, 1),
            end_date=date(2024, 3, 31),
        )
        assert len(result) == 2
        keys = {t.tech_key for t in result}
        assert keys == {"python", "react"}

    def test_get_trends_data_points_are_trend_data_point(
        self, trend_dao: TrendDAO
    ) -> None:
        """Verify data points are TrendDataPoint objects."""
        result = trend_dao.get_trends(
            tech_keys=["python"],
            start_date=date(2024, 1, 1),
            end_date=date(2024, 3, 31),
        )
        assert len(result[0].data) > 0
        assert all(isinstance(dp, TrendDataPoint) for dp in result[0].data)

    def test_get_trends_data_points_sorted_chronologically(
        self, trend_dao: TrendDAO
    ) -> None:
        """Verify data points are sorted by month ascending."""
        result = trend_dao.get_trends(
            tech_keys=["python"],
            start_date=date(2024, 1, 1),
            end_date=date(2024, 3, 31),
        )
        months = [dp.month for dp in result[0].data]
        assert months == sorted(months)

    def test_get_trends_month_format_yyyy_mm(self, trend_dao: TrendDAO) -> None:
        """Verify month is formatted as YYYY-MM."""
        result = trend_dao.get_trends(
            tech_keys=["python"],
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31),
        )
        assert result[0].data[0].month == "2024-01"

    def test_get_trends_respects_date_range_start(self, trend_dao: TrendDAO) -> None:
        """Verify start_date boundary is respected."""
        result = trend_dao.get_trends(
            tech_keys=["python"],
            start_date=date(2024, 2, 1),
            end_date=date(2024, 3, 31),
        )
        months = [dp.month for dp in result[0].data]
        assert "2024-01" not in months
        assert "2024-02" in months

    def test_get_trends_respects_date_range_end(self, trend_dao: TrendDAO) -> None:
        """Verify end_date boundary is respected."""
        result = trend_dao.get_trends(
            tech_keys=["python"],
            start_date=date(2024, 1, 1),
            end_date=date(2024, 2, 28),
        )
        months = [dp.month for dp in result[0].data]
        assert "2024-03" not in months
        assert "2024-02" in months

    def test_get_trends_null_mention_count_as_zero(self, trend_dao: TrendDAO) -> None:
        """Verify NULL mention_count is serialized as 0."""
        result = trend_dao.get_trends(
            tech_keys=["postgresql"],
            start_date=date(2024, 1, 1),
            end_date=date(2024, 3, 31),
        )
        feb_data = next((dp for dp in result[0].data if dp.month == "2024-02"), None)
        assert feb_data is not None
        assert feb_data.count == 0

    def test_get_trends_correct_mention_counts(self, trend_dao: TrendDAO) -> None:
        """Verify correct mention counts are returned."""
        result = trend_dao.get_trends(
            tech_keys=["python"],
            start_date=date(2024, 1, 1),
            end_date=date(2024, 3, 31),
        )
        counts = {dp.month: dp.count for dp in result[0].data}
        assert counts["2024-01"] == 100
        assert counts["2024-02"] == 120
        assert counts["2024-03"] == 110

    def test_get_trends_results_sorted_by_name(self, trend_dao: TrendDAO) -> None:
        """Verify results are sorted alphabetically by tech_name."""
        result = trend_dao.get_trends(
            tech_keys=["react", "python", "postgresql"],
            start_date=date(2024, 1, 1),
            end_date=date(2024, 3, 31),
        )
        names = [t.name for t in result]
        assert names == sorted(names)


class TestTrendDAOEdgeCases:
    """Test suite for TrendDAO edge cases."""

    def test_get_trends_empty_tech_keys_returns_empty_list(
        self, trend_dao: TrendDAO
    ) -> None:
        """Verify empty tech_keys returns empty list without query."""
        result = trend_dao.get_trends(
            tech_keys=[],
            start_date=date(2024, 1, 1),
            end_date=date(2024, 3, 31),
        )
        assert result == []

    def test_get_trends_unknown_tech_key_returns_empty(
        self, trend_dao: TrendDAO
    ) -> None:
        """Verify unknown tech_key returns empty list."""
        result = trend_dao.get_trends(
            tech_keys=["nonexistent"],
            start_date=date(2024, 1, 1),
            end_date=date(2024, 3, 31),
        )
        assert result == []

    def test_get_trends_mixed_known_unknown_keys(self, trend_dao: TrendDAO) -> None:
        """Verify mixed known/unknown keys returns only known."""
        result = trend_dao.get_trends(
            tech_keys=["python", "nonexistent"],
            start_date=date(2024, 1, 1),
            end_date=date(2024, 3, 31),
        )
        assert len(result) == 1
        assert result[0].tech_key == "python"

    def test_get_trends_date_range_no_data(self, trend_dao: TrendDAO) -> None:
        """Verify date range with no data returns empty list."""
        result = trend_dao.get_trends(
            tech_keys=["python"],
            start_date=date(2020, 1, 1),
            end_date=date(2020, 12, 31),
        )
        assert result == []

    def test_get_trends_single_month_range(self, trend_dao: TrendDAO) -> None:
        """Verify single month date range works."""
        result = trend_dao.get_trends(
            tech_keys=["python"],
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31),
        )
        assert len(result) == 1
        assert len(result[0].data) == 1
        assert result[0].data[0].month == "2024-01"

    def test_get_trends_data_outside_range_excluded(self, trend_dao: TrendDAO) -> None:
        """Verify data outside date range is excluded."""
        result = trend_dao.get_trends(
            tech_keys=["python"],
            start_date=date(2024, 1, 1),
            end_date=date(2024, 3, 31),
        )
        months = [dp.month for dp in result[0].data]
        assert "2023-12" not in months
        assert "2024-04" not in months


class TestTrendDAOErrorHandling:
    """Test suite for TrendDAO error handling."""

    def test_get_trends_raises_on_missing_table(
        self, temp_db_with_trends: duckdb.DuckDBPyConnection
    ) -> None:
        """Verify QueryExecutionError raised when table missing."""
        temp_db_with_trends.execute("DROP TABLE mart_monthly_trends")
        cursor = temp_db_with_trends.cursor()
        dao = TrendDAO(cursor)

        with pytest.raises(QueryExecutionError):
            dao.get_trends(
                tech_keys=["python"],
                start_date=date(2024, 1, 1),
                end_date=date(2024, 3, 31),
            )


class TestTrendDAOGroupByTechnology:
    """Test suite for TrendDAO._group_by_technology helper."""

    def test_group_by_technology_empty_rows(self, trend_dao: TrendDAO) -> None:
        """Verify empty rows returns empty list."""
        result = trend_dao._group_by_technology([])
        assert result == []

    def test_group_by_technology_single_tech_single_month(
        self, trend_dao: TrendDAO
    ) -> None:
        """Verify single technology with single month grouped correctly."""
        rows = [
            {
                "tech_key": "python",
                "tech_name": "Python",
                "month": date(2024, 1, 1),
                "mention_count": 100,
            }
        ]
        result = trend_dao._group_by_technology(rows)
        assert len(result) == 1
        assert result[0].tech_key == "python"
        assert len(result[0].data) == 1

    def test_group_by_technology_single_tech_multiple_months(
        self, trend_dao: TrendDAO
    ) -> None:
        """Verify single technology with multiple months grouped correctly."""
        rows = [
            {
                "tech_key": "python",
                "tech_name": "Python",
                "month": date(2024, 1, 1),
                "mention_count": 100,
            },
            {
                "tech_key": "python",
                "tech_name": "Python",
                "month": date(2024, 2, 1),
                "mention_count": 120,
            },
        ]
        result = trend_dao._group_by_technology(rows)
        assert len(result) == 1
        assert len(result[0].data) == 2

    def test_group_by_technology_multiple_techs(self, trend_dao: TrendDAO) -> None:
        """Verify multiple technologies grouped separately."""
        rows = [
            {
                "tech_key": "python",
                "tech_name": "Python",
                "month": date(2024, 1, 1),
                "mention_count": 100,
            },
            {
                "tech_key": "react",
                "tech_name": "React",
                "month": date(2024, 1, 1),
                "mention_count": 80,
            },
        ]
        result = trend_dao._group_by_technology(rows)
        assert len(result) == 2

    def test_group_by_technology_sorted_alphabetically(
        self, trend_dao: TrendDAO
    ) -> None:
        """Verify results sorted alphabetically by name."""
        rows = [
            {
                "tech_key": "react",
                "tech_name": "React",
                "month": date(2024, 1, 1),
                "mention_count": 80,
            },
            {
                "tech_key": "python",
                "tech_name": "Python",
                "month": date(2024, 1, 1),
                "mention_count": 100,
            },
        ]
        result = trend_dao._group_by_technology(rows)
        names = [t.name for t in result]
        assert names == ["Python", "React"]

    def test_group_by_technology_handles_string_month(
        self, trend_dao: TrendDAO
    ) -> None:
        """Verify string month format is handled."""
        rows = [
            {
                "tech_key": "python",
                "tech_name": "Python",
                "month": "2024-01-01",
                "mention_count": 100,
            }
        ]
        result = trend_dao._group_by_technology(rows)
        assert result[0].data[0].month == "2024-01"
