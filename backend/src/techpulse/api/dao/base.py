"""Base Data Access Object providing standard database operations.

This module defines the abstract BaseDAO class that provides common
patterns for executing queries and mapping results. All domain-specific
DAOs should inherit from this class.
"""

from collections.abc import Sequence
from typing import Optional, Union

import duckdb
import structlog

from techpulse.api.exceptions.domain import QueryExecutionError

logger = structlog.get_logger(__name__)

ParamValue = Union[str, int, float, bool, None]
Params = Sequence[ParamValue]


class BaseDAO:
    """Base class for Data Access Objects.

    Provides standard methods for executing queries and fetching results
    from the database. All methods use parameterized queries to prevent
    SQL injection and wrap database errors in domain-specific exceptions.

    This class is designed to be subclassed by domain-specific DAOs that
    implement entity-specific query logic.

    Attributes:
        cursor: The DuckDB cursor for executing queries.

    Example:
        >>> class TechnologyDAO(BaseDAO):
        ...     def get_by_key(self, key: str) -> dict | None:
        ...         return self.fetch_one(
        ...             "SELECT * FROM dim_technologies WHERE tech_key = ?",
        ...             [key]
        ...         )
    """

    def __init__(self, cursor: duckdb.DuckDBPyConnection) -> None:
        """Initialize the DAO with a database cursor.

        Args:
            cursor: An active DuckDB cursor for executing queries.
        """
        self._cursor = cursor
        self._log = logger.bind(component=self.__class__.__name__)

    def execute(self, query: str, params: Optional[Params] = None) -> None:
        """Execute a query without returning results.

        Use this method for queries that modify data or don't return
        rows. In the read-only API context, this is primarily useful
        for setting session variables or running EXPLAIN queries.

        Args:
            query: The SQL query to execute with ? placeholders.
            params: Sequence of parameter values to bind to placeholders.

        Raises:
            QueryExecutionError: If the query fails to execute.
        """
        params = params or []
        try:
            self._cursor.execute(query, list(params))
        except duckdb.Error as error:
            self._log.error(
                "query_execution_failed",
                query=self._truncate_query(query),
                error=str(error),
            )
            raise QueryExecutionError(
                query=self._truncate_query(query),
                reason=str(error),
            ) from error

    def fetch_one(
        self, query: str, params: Optional[Params] = None
    ) -> Optional[dict[str, ParamValue]]:
        """Execute a query and return a single row as a dictionary.

        Returns None if the query returns no rows. Use this method when
        expecting exactly zero or one result.

        Args:
            query: The SQL query to execute with ? placeholders.
            params: Sequence of parameter values to bind to placeholders.

        Returns:
            A dictionary mapping column names to values, or None if no
            row was found.

        Raises:
            QueryExecutionError: If the query fails to execute.
        """
        params = params or []
        try:
            result = self._cursor.execute(query, list(params))
            row = result.fetchone()
            if row is None:
                return None
            columns = [desc[0] for desc in result.description]
            return dict(zip(columns, row, strict=True))
        except duckdb.Error as error:
            self._log.error(
                "query_execution_failed",
                query=self._truncate_query(query),
                error=str(error),
            )
            raise QueryExecutionError(
                query=self._truncate_query(query),
                reason=str(error),
            ) from error

    def fetch_all(
        self, query: str, params: Optional[Params] = None
    ) -> list[dict[str, ParamValue]]:
        """Execute a query and return all rows as a list of dictionaries.

        Use this method when you need all matching rows. For large result
        sets, consider using fetch_many with pagination instead.

        Args:
            query: The SQL query to execute with ? placeholders.
            params: Sequence of parameter values to bind to placeholders.

        Returns:
            A list of dictionaries, each mapping column names to values.
            Returns an empty list if no rows match.

        Raises:
            QueryExecutionError: If the query fails to execute.
        """
        params = params or []
        try:
            result = self._cursor.execute(query, list(params))
            rows = result.fetchall()
            if not rows:
                return []
            columns = [desc[0] for desc in result.description]
            return [dict(zip(columns, row, strict=True)) for row in rows]
        except duckdb.Error as error:
            self._log.error(
                "query_execution_failed",
                query=self._truncate_query(query),
                error=str(error),
            )
            raise QueryExecutionError(
                query=self._truncate_query(query),
                reason=str(error),
            ) from error

    def fetch_many(
        self,
        query: str,
        params: Optional[Params] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> list[dict[str, ParamValue]]:
        """Execute a query with pagination and return rows as dictionaries.

        Automatically appends LIMIT and OFFSET clauses to the query.
        The base query should NOT include its own LIMIT/OFFSET clauses.

        Args:
            query: The SQL query to execute with ? placeholders.
                Should not include LIMIT or OFFSET clauses.
            params: Sequence of parameter values to bind to placeholders.
            limit: Maximum number of rows to return (default 20).
            offset: Number of rows to skip before returning results.

        Returns:
            A list of dictionaries, each mapping column names to values.
            Returns an empty list if no rows match.

        Raises:
            QueryExecutionError: If the query fails to execute.
            ValueError: If limit is negative or offset is negative.
        """
        if limit < 0:
            raise ValueError("limit must be non-negative")
        if offset < 0:
            raise ValueError("offset must be non-negative")

        params = params or []
        paginated_query = f"{query} LIMIT ? OFFSET ?"
        paginated_params = list(params) + [limit, offset]

        try:
            result = self._cursor.execute(paginated_query, paginated_params)
            rows = result.fetchall()
            if not rows:
                return []
            columns = [desc[0] for desc in result.description]
            return [dict(zip(columns, row, strict=True)) for row in rows]
        except duckdb.Error as error:
            self._log.error(
                "query_execution_failed",
                query=self._truncate_query(paginated_query),
                error=str(error),
            )
            raise QueryExecutionError(
                query=self._truncate_query(paginated_query),
                reason=str(error),
            ) from error

    def _truncate_query(self, query: str, max_length: int = 200) -> str:
        """Truncate a query string for safe logging.

        Prevents excessively long queries from bloating log output
        while preserving enough context for debugging.

        Args:
            query: The SQL query to truncate.
            max_length: Maximum length before truncation.

        Returns:
            The query, truncated with '...' suffix if necessary.
        """
        if len(query) <= max_length:
            return query
        return query[:max_length] + "..."
