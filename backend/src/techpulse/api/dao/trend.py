"""Data Access Object for trend data.

This module provides the TrendDAO class for querying monthly trend
data from the Gold layer mart_monthly_trends table.
"""

from collections import defaultdict
from datetime import date
from typing import Union, cast

from techpulse.api.dao.base import BaseDAO, Params
from techpulse.api.schemas.trend import TechnologyTrend, TrendDataPoint

RowValue = Union[str, int, float, bool, None]


class TrendDAO(BaseDAO):
    """Data access for technology trend time series.

    Provides methods for querying monthly trend data from the Gold layer.
    Results are grouped by technology with chronologically sorted data points.

    Example:
        >>> dao = TrendDAO(cursor)
        >>> trends = dao.get_trends(
        ...     tech_keys=["python", "react"],
        ...     start_date=date(2024, 1, 1),
        ...     end_date=date(2024, 12, 31),
        ... )
        >>> print(trends[0].name)
        'Python'
    """

    def get_trends(
        self,
        tech_keys: list[str],
        start_date: date,
        end_date: date,
    ) -> list[TechnologyTrend]:
        """Retrieve monthly trend data for specified technologies.

        Queries mart_monthly_trends for the given technologies within the
        date range. Results are grouped by technology with monthly data
        points sorted chronologically. NULL mention counts are returned as 0.

        Args:
            tech_keys: List of technology keys to query (e.g., ["python"]).
            start_date: Start of date range (inclusive).
            end_date: End of date range (inclusive).

        Returns:
            List of TechnologyTrend objects, one per requested technology
            that exists in the data. Technologies not found return empty
            data arrays within the response structure. Results are sorted
            alphabetically by tech_name.

        Raises:
            QueryExecutionError: If the database query fails.
        """
        if not tech_keys:
            return []

        query = """
            SELECT
                tech_key,
                tech_name,
                month,
                COALESCE(mention_count, 0) AS mention_count
            FROM mart_monthly_trends
            WHERE tech_key = ANY(?)
              AND month >= ?
              AND month <= ?
            ORDER BY tech_name ASC, month ASC
        """

        params = cast(Params, [tech_keys, start_date, end_date])
        rows = self.fetch_all(query, params)

        return self._group_by_technology(rows)

    def _group_by_technology(
        self,
        rows: list[dict[str, RowValue]],
    ) -> list[TechnologyTrend]:
        """Group flat query results into TechnologyTrend objects.

        Transforms a flat list of row dictionaries into a list of
        TechnologyTrend objects, each containing an array of monthly
        data points.

        Args:
            rows: List of row dictionaries from the database query.

        Returns:
            List of TechnologyTrend objects sorted alphabetically by name.
        """
        tech_data: dict[str, dict[str, RowValue]] = {}
        tech_points: defaultdict[str, list[TrendDataPoint]] = defaultdict(list)

        for row in rows:
            tech_key = str(row["tech_key"])
            tech_name = str(row["tech_name"])
            month_date = row["month"]
            mention_count = int(row["mention_count"] or 0)

            if tech_key not in tech_data:
                tech_data[tech_key] = {"name": tech_name}

            if isinstance(month_date, date):
                month_str = month_date.strftime("%Y-%m")
            else:
                month_str = str(month_date)[:7]

            tech_points[tech_key].append(
                TrendDataPoint(month=month_str, count=mention_count)
            )

        result = []
        for tech_key in tech_data:
            result.append(
                TechnologyTrend(
                    tech_key=tech_key,
                    name=str(tech_data[tech_key]["name"]),
                    data=tech_points[tech_key],
                )
            )

        return sorted(result, key=lambda t: t.name)
