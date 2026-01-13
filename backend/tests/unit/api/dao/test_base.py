"""Unit tests for BaseDAO class."""

from typing import Generator

import duckdb
import pytest

from techpulse.api.dao.base import BaseDAO
from techpulse.api.exceptions.domain import QueryExecutionError


@pytest.fixture
def temp_db_connection() -> Generator[duckdb.DuckDBPyConnection, None, None]:
    """Create a temporary in-memory DuckDB connection for testing."""
    conn = duckdb.connect(":memory:")
    conn.execute("""
        CREATE TABLE test_items (
            id INTEGER PRIMARY KEY,
            name VARCHAR,
            value DOUBLE
        )
    """)
    conn.execute("INSERT INTO test_items VALUES (1, 'alpha', 10.5)")
    conn.execute("INSERT INTO test_items VALUES (2, 'beta', 20.0)")
    conn.execute("INSERT INTO test_items VALUES (3, 'gamma', 30.5)")
    conn.execute("INSERT INTO test_items VALUES (4, 'delta', 40.0)")
    conn.execute("INSERT INTO test_items VALUES (5, 'epsilon', 50.5)")
    yield conn
    conn.close()


@pytest.fixture
def dao(temp_db_connection: duckdb.DuckDBPyConnection) -> BaseDAO:
    """Create a BaseDAO instance with test connection."""
    cursor = temp_db_connection.cursor()
    return BaseDAO(cursor)


class TestBaseDAOInit:
    """Test suite for BaseDAO initialization."""

    def test_init_stores_cursor(
        self, temp_db_connection: duckdb.DuckDBPyConnection
    ) -> None:
        """Verify cursor is stored during initialization."""
        cursor = temp_db_connection.cursor()
        dao = BaseDAO(cursor)
        assert dao._cursor is cursor


class TestExecute:
    """Test suite for BaseDAO.execute method."""

    def test_execute_runs_query(self, dao: BaseDAO) -> None:
        """Verify execute runs the provided query."""
        dao.execute("CREATE TABLE new_table (id INTEGER)")
        result = dao._cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='new_table'"
        ).fetchone()
        assert result is not None

    def test_execute_with_params(self, dao: BaseDAO) -> None:
        """Verify execute handles parameterized queries."""
        dao.execute(
            "CREATE TABLE param_table AS SELECT ? as val",
            [42],
        )
        result = dao._cursor.execute("SELECT val FROM param_table").fetchone()
        assert result == (42,)

    def test_execute_without_params(self, dao: BaseDAO) -> None:
        """Verify execute works without params."""
        dao.execute("SELECT 1")

    def test_execute_raises_on_invalid_query(self, dao: BaseDAO) -> None:
        """Verify execute raises QueryExecutionError on invalid SQL."""
        with pytest.raises(QueryExecutionError) as exc_info:
            dao.execute("INVALID SQL SYNTAX")
        assert "INVALID SQL" in exc_info.value.query

    def test_execute_stores_reason_in_error(self, dao: BaseDAO) -> None:
        """Verify QueryExecutionError contains error reason."""
        with pytest.raises(QueryExecutionError) as exc_info:
            dao.execute("SELECT * FROM nonexistent_table")
        assert exc_info.value.reason != ""


class TestFetchOne:
    """Test suite for BaseDAO.fetch_one method."""

    def test_fetch_one_returns_dict(self, dao: BaseDAO) -> None:
        """Verify fetch_one returns a dictionary."""
        result = dao.fetch_one("SELECT * FROM test_items WHERE id = ?", [1])
        assert isinstance(result, dict)

    def test_fetch_one_returns_correct_data(self, dao: BaseDAO) -> None:
        """Verify fetch_one returns correct row data."""
        result = dao.fetch_one("SELECT * FROM test_items WHERE id = ?", [1])
        assert result is not None
        assert result["id"] == 1
        assert result["name"] == "alpha"
        assert result["value"] == 10.5

    def test_fetch_one_returns_none_when_no_match(self, dao: BaseDAO) -> None:
        """Verify fetch_one returns None when no row matches."""
        result = dao.fetch_one("SELECT * FROM test_items WHERE id = ?", [999])
        assert result is None

    def test_fetch_one_without_params(self, dao: BaseDAO) -> None:
        """Verify fetch_one works without params."""
        result = dao.fetch_one("SELECT COUNT(*) as cnt FROM test_items")
        assert result is not None
        assert result["cnt"] == 5

    def test_fetch_one_raises_on_invalid_query(self, dao: BaseDAO) -> None:
        """Verify fetch_one raises QueryExecutionError on invalid SQL."""
        with pytest.raises(QueryExecutionError):
            dao.fetch_one("SELECT * FROM nonexistent")

    def test_fetch_one_column_names_preserved(self, dao: BaseDAO) -> None:
        """Verify column names are preserved in result dict."""
        result = dao.fetch_one("SELECT id, name, value FROM test_items WHERE id = 1")
        assert result is not None
        assert set(result.keys()) == {"id", "name", "value"}


class TestFetchAll:
    """Test suite for BaseDAO.fetch_all method."""

    def test_fetch_all_returns_list(self, dao: BaseDAO) -> None:
        """Verify fetch_all returns a list."""
        result = dao.fetch_all("SELECT * FROM test_items")
        assert isinstance(result, list)

    def test_fetch_all_returns_all_rows(self, dao: BaseDAO) -> None:
        """Verify fetch_all returns all matching rows."""
        result = dao.fetch_all("SELECT * FROM test_items")
        assert len(result) == 5

    def test_fetch_all_returns_dicts(self, dao: BaseDAO) -> None:
        """Verify each row in fetch_all is a dictionary."""
        result = dao.fetch_all("SELECT * FROM test_items LIMIT 1")
        assert len(result) == 1
        assert isinstance(result[0], dict)

    def test_fetch_all_returns_empty_list_when_no_match(self, dao: BaseDAO) -> None:
        """Verify fetch_all returns empty list when no rows match."""
        result = dao.fetch_all("SELECT * FROM test_items WHERE id > 1000")
        assert result == []

    def test_fetch_all_with_params(self, dao: BaseDAO) -> None:
        """Verify fetch_all handles parameterized queries."""
        result = dao.fetch_all("SELECT * FROM test_items WHERE value > ?", [25.0])
        assert len(result) == 3
        for row in result:
            assert row["value"] > 25.0

    def test_fetch_all_without_params(self, dao: BaseDAO) -> None:
        """Verify fetch_all works without params."""
        result = dao.fetch_all("SELECT * FROM test_items WHERE id < 3")
        assert len(result) == 2

    def test_fetch_all_raises_on_invalid_query(self, dao: BaseDAO) -> None:
        """Verify fetch_all raises QueryExecutionError on invalid SQL."""
        with pytest.raises(QueryExecutionError):
            dao.fetch_all("SELECT * FROM nonexistent")

    def test_fetch_all_preserves_order(self, dao: BaseDAO) -> None:
        """Verify fetch_all preserves query ORDER BY."""
        result = dao.fetch_all("SELECT * FROM test_items ORDER BY id DESC")
        ids = [row["id"] for row in result]
        assert ids == [5, 4, 3, 2, 1]


class TestFetchMany:
    """Test suite for BaseDAO.fetch_many method."""

    def test_fetch_many_returns_list(self, dao: BaseDAO) -> None:
        """Verify fetch_many returns a list."""
        result = dao.fetch_many("SELECT * FROM test_items", limit=2)
        assert isinstance(result, list)

    def test_fetch_many_respects_limit(self, dao: BaseDAO) -> None:
        """Verify fetch_many respects the limit parameter."""
        result = dao.fetch_many("SELECT * FROM test_items", limit=2)
        assert len(result) == 2

    def test_fetch_many_respects_offset(self, dao: BaseDAO) -> None:
        """Verify fetch_many respects the offset parameter."""
        result = dao.fetch_many(
            "SELECT * FROM test_items ORDER BY id", limit=2, offset=2
        )
        assert len(result) == 2
        assert result[0]["id"] == 3
        assert result[1]["id"] == 4

    def test_fetch_many_with_params(self, dao: BaseDAO) -> None:
        """Verify fetch_many handles parameterized queries."""
        result = dao.fetch_many(
            "SELECT * FROM test_items WHERE value > ?",
            params=[20.0],
            limit=2,
        )
        assert len(result) == 2
        for row in result:
            assert row["value"] > 20.0

    def test_fetch_many_default_limit(self, dao: BaseDAO) -> None:
        """Verify fetch_many uses default limit of 20."""
        result = dao.fetch_many("SELECT * FROM test_items")
        assert len(result) == 5

    def test_fetch_many_default_offset(self, dao: BaseDAO) -> None:
        """Verify fetch_many uses default offset of 0."""
        result = dao.fetch_many("SELECT * FROM test_items ORDER BY id", limit=1)
        assert result[0]["id"] == 1

    def test_fetch_many_returns_empty_list_when_offset_exceeds(
        self, dao: BaseDAO
    ) -> None:
        """Verify fetch_many returns empty list when offset exceeds rows."""
        result = dao.fetch_many("SELECT * FROM test_items", limit=10, offset=100)
        assert result == []

    def test_fetch_many_raises_on_invalid_query(self, dao: BaseDAO) -> None:
        """Verify fetch_many raises QueryExecutionError on invalid SQL."""
        with pytest.raises(QueryExecutionError):
            dao.fetch_many("SELECT * FROM nonexistent")

    def test_fetch_many_raises_on_negative_limit(self, dao: BaseDAO) -> None:
        """Verify fetch_many raises ValueError on negative limit."""
        with pytest.raises(ValueError) as exc_info:
            dao.fetch_many("SELECT * FROM test_items", limit=-1)
        assert "limit must be non-negative" in str(exc_info.value)

    def test_fetch_many_raises_on_negative_offset(self, dao: BaseDAO) -> None:
        """Verify fetch_many raises ValueError on negative offset."""
        with pytest.raises(ValueError) as exc_info:
            dao.fetch_many("SELECT * FROM test_items", offset=-1)
        assert "offset must be non-negative" in str(exc_info.value)

    def test_fetch_many_pagination_workflow(self, dao: BaseDAO) -> None:
        """Verify fetch_many supports typical pagination workflow."""
        page1 = dao.fetch_many(
            "SELECT * FROM test_items ORDER BY id", limit=2, offset=0
        )
        page2 = dao.fetch_many(
            "SELECT * FROM test_items ORDER BY id", limit=2, offset=2
        )
        page3 = dao.fetch_many(
            "SELECT * FROM test_items ORDER BY id", limit=2, offset=4
        )

        assert len(page1) == 2
        assert len(page2) == 2
        assert len(page3) == 1

        all_ids = [r["id"] for r in page1 + page2 + page3]
        assert all_ids == [1, 2, 3, 4, 5]


class TestTruncateQuery:
    """Test suite for BaseDAO._truncate_query method."""

    def test_short_query_not_truncated(self, dao: BaseDAO) -> None:
        """Verify short queries are not truncated."""
        query = "SELECT * FROM test"
        result = dao._truncate_query(query)
        assert result == query

    def test_long_query_truncated(self, dao: BaseDAO) -> None:
        """Verify long queries are truncated."""
        query = "SELECT " + "a, " * 100 + "b FROM test"
        result = dao._truncate_query(query, max_length=50)
        assert len(result) == 53
        assert result.endswith("...")

    def test_query_at_max_length_not_truncated(self, dao: BaseDAO) -> None:
        """Verify query at exactly max_length is not truncated."""
        query = "x" * 200
        result = dao._truncate_query(query, max_length=200)
        assert result == query
        assert "..." not in result

    def test_query_over_max_length_truncated(self, dao: BaseDAO) -> None:
        """Verify query over max_length is truncated."""
        query = "x" * 201
        result = dao._truncate_query(query, max_length=200)
        assert len(result) == 203
        assert result.endswith("...")


class TestSubclassing:
    """Test suite for BaseDAO subclassing pattern."""

    def test_subclass_inherits_methods(
        self, temp_db_connection: duckdb.DuckDBPyConnection
    ) -> None:
        """Verify subclasses inherit all BaseDAO methods."""

        class TestDAO(BaseDAO):
            pass

        cursor = temp_db_connection.cursor()
        dao = TestDAO(cursor)
        result = dao.fetch_one("SELECT 1 as val")
        assert result == {"val": 1}

    def test_subclass_can_add_methods(
        self, temp_db_connection: duckdb.DuckDBPyConnection
    ) -> None:
        """Verify subclasses can add domain-specific methods."""

        class ItemDAO(BaseDAO):
            def get_by_id(self, item_id: int) -> dict | None:
                return self.fetch_one(
                    "SELECT * FROM test_items WHERE id = ?", [item_id]
                )

        cursor = temp_db_connection.cursor()
        dao = ItemDAO(cursor)
        result = dao.get_by_id(1)
        assert result is not None
        assert result["name"] == "alpha"
