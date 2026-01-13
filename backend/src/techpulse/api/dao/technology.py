"""Data Access Object for technology entities.

This module provides the TechnologyDAO class for querying technology
taxonomy data from the data warehouse.
"""

from techpulse.api.dao.base import BaseDAO
from techpulse.api.schemas.technology import Technology


class TechnologyDAO(BaseDAO):
    """Data access for technology taxonomy entities.

    Provides methods for querying the available technologies from the
    Gold layer. Technologies are derived from the mart_monthly_trends
    table joined with the tech_taxonomy seed for category information.

    Example:
        >>> dao = TechnologyDAO(cursor)
        >>> technologies = dao.list_all()
        >>> print(technologies[0].name)
        'AWS'
    """

    def list_all(self) -> list[Technology]:
        """Retrieve all available technologies sorted alphabetically by name.

        Queries distinct technologies from mart_monthly_trends and joins
        with tech_taxonomy to obtain category classification. Results are
        ordered alphabetically by display name.

        Returns:
            List of Technology objects sorted by name in ascending order.

        Raises:
            QueryExecutionError: If the database query fails.
        """
        query = """
            SELECT DISTINCT
                t.tech_key AS key,
                t.display_name AS name,
                t.category
            FROM tech_taxonomy t
            INNER JOIN mart_monthly_trends m ON t.tech_key = m.tech_key
            ORDER BY t.display_name ASC
        """
        rows = self.fetch_all(query)
        return [
            Technology(
                key=str(row["key"]),
                name=str(row["name"]),
                category=str(row["category"]),
            )
            for row in rows
        ]
