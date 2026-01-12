"""Unit tests for Bronze layer schema definitions."""

import tempfile
from pathlib import Path

import duckdb

from techpulse.storage.manager import DuckDBManager
from techpulse.storage.schema import (
    RAW_HN_ITEMS_DDL,
    RAW_HN_ITEMS_TABLE,
    initialize_schema,
    table_exists,
)


class TestSchemaConstants:
    """Test suite for schema constant definitions."""

    def test_table_name_constant(self) -> None:
        """Verify RAW_HN_ITEMS_TABLE is defined correctly."""
        assert RAW_HN_ITEMS_TABLE == "raw_hn_items"

    def test_ddl_contains_table_name(self) -> None:
        """Verify DDL contains the correct table name."""
        assert RAW_HN_ITEMS_TABLE in RAW_HN_ITEMS_DDL

    def test_ddl_contains_required_columns(self) -> None:
        """Verify DDL defines all required columns."""
        assert "load_id" in RAW_HN_ITEMS_DDL
        assert "ingested_at" in RAW_HN_ITEMS_DDL
        assert "payload" in RAW_HN_ITEMS_DDL

    def test_ddl_specifies_column_types(self) -> None:
        """Verify DDL specifies correct column types."""
        assert "UUID" in RAW_HN_ITEMS_DDL
        assert "TIMESTAMPTZ" in RAW_HN_ITEMS_DDL
        assert "JSON" in RAW_HN_ITEMS_DDL

    def test_ddl_enforces_not_null_constraints(self) -> None:
        """Verify DDL enforces NOT NULL on all columns."""
        ddl_lower = RAW_HN_ITEMS_DDL.lower()
        assert ddl_lower.count("not null") == 3

    def test_ddl_is_idempotent(self) -> None:
        """Verify DDL uses CREATE TABLE IF NOT EXISTS."""
        assert "IF NOT EXISTS" in RAW_HN_ITEMS_DDL


class TestInitializeSchema:
    """Test suite for initialize_schema function."""

    def test_creates_raw_hn_items_table(self) -> None:
        """Verify initialize_schema creates the raw_hn_items table."""
        with duckdb.connect(":memory:") as connection:
            assert not table_exists(connection, RAW_HN_ITEMS_TABLE)

            initialize_schema(connection)

            assert table_exists(connection, RAW_HN_ITEMS_TABLE)

    def test_idempotent_execution(self) -> None:
        """Verify initialize_schema can be called multiple times safely."""
        with duckdb.connect(":memory:") as connection:
            initialize_schema(connection)
            initialize_schema(connection)
            initialize_schema(connection)

            assert table_exists(connection, RAW_HN_ITEMS_TABLE)

    def test_table_has_correct_column_count(self) -> None:
        """Verify created table has exactly three columns."""
        with duckdb.connect(":memory:") as connection:
            initialize_schema(connection)

            result = connection.execute(
                """
                SELECT COUNT(*)
                FROM information_schema.columns
                WHERE table_name = ?
                """,
                [RAW_HN_ITEMS_TABLE],
            ).fetchone()

            assert result is not None
            assert result[0] == 3


class TestTableSchema:
    """Test suite for verifying table schema structure."""

    def test_load_id_column_exists(self) -> None:
        """Verify load_id column is created."""
        with duckdb.connect(":memory:") as connection:
            initialize_schema(connection)

            result = connection.execute(
                """
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns
                WHERE table_name = ? AND column_name = 'load_id'
                """,
                [RAW_HN_ITEMS_TABLE],
            ).fetchone()

            assert result is not None
            assert result[0] == "load_id"
            assert result[2] == "NO"

    def test_ingested_at_column_exists(self) -> None:
        """Verify ingested_at column is created."""
        with duckdb.connect(":memory:") as connection:
            initialize_schema(connection)

            result = connection.execute(
                """
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns
                WHERE table_name = ? AND column_name = 'ingested_at'
                """,
                [RAW_HN_ITEMS_TABLE],
            ).fetchone()

            assert result is not None
            assert result[0] == "ingested_at"
            assert result[2] == "NO"

    def test_payload_column_exists(self) -> None:
        """Verify payload column is created."""
        with duckdb.connect(":memory:") as connection:
            initialize_schema(connection)

            result = connection.execute(
                """
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns
                WHERE table_name = ? AND column_name = 'payload'
                """,
                [RAW_HN_ITEMS_TABLE],
            ).fetchone()

            assert result is not None
            assert result[0] == "payload"
            assert result[2] == "NO"


class TestTableExistsHelper:
    """Test suite for table_exists helper function."""

    def test_returns_false_for_nonexistent_table(self) -> None:
        """Verify table_exists returns False when table does not exist."""
        with duckdb.connect(":memory:") as connection:
            assert not table_exists(connection, "nonexistent_table")

    def test_returns_true_for_existing_table(self) -> None:
        """Verify table_exists returns True when table exists."""
        with duckdb.connect(":memory:") as connection:
            connection.execute("CREATE TABLE test_table (id INTEGER)")

            assert table_exists(connection, "test_table")

    def test_case_sensitive_table_name(self) -> None:
        """Verify table_exists is case-sensitive for table names."""
        with duckdb.connect(":memory:") as connection:
            connection.execute("CREATE TABLE test_table (id INTEGER)")

            assert table_exists(connection, "test_table")
            assert not table_exists(connection, "TEST_TABLE")


class TestManagerSchemaIntegration:
    """Test suite for schema initialization via DuckDBManager."""

    def test_manager_initializes_schema_on_connection(self) -> None:
        """Verify DuckDBManager initializes schema when entering context."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "test.duckdb"

            with DuckDBManager(database_path=str(db_path)) as manager:
                connection = manager.get_connection()
                assert table_exists(connection, RAW_HN_ITEMS_TABLE)

    def test_schema_persists_across_connections(self) -> None:
        """Verify schema remains after closing and reopening connection."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "test.duckdb"

            with DuckDBManager(database_path=str(db_path)):
                pass

            with DuckDBManager(database_path=str(db_path)) as manager:
                connection = manager.get_connection()
                assert table_exists(connection, RAW_HN_ITEMS_TABLE)


class TestDataInsertionContract:
    """Test suite verifying the table accepts valid Bronze layer data."""

    def test_accepts_valid_insert(self) -> None:
        """Verify table accepts correctly typed INSERT statements."""
        with duckdb.connect(":memory:") as connection:
            initialize_schema(connection)

            connection.execute(
                """
                INSERT INTO raw_hn_items (load_id, ingested_at, payload)
                VALUES (
                    'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11'::UUID,
                    '2024-01-15 10:30:00+00'::TIMESTAMPTZ,
                    '{"id": 123, "type": "story"}'::JSON
                )
                """
            )

            result = connection.execute("SELECT COUNT(*) FROM raw_hn_items").fetchone()
            assert result is not None
            assert result[0] == 1

    def test_rejects_null_load_id(self) -> None:
        """Verify table rejects NULL load_id values."""
        with duckdb.connect(":memory:") as connection:
            initialize_schema(connection)

            try:
                connection.execute(
                    """
                    INSERT INTO raw_hn_items (load_id, ingested_at, payload)
                    VALUES (
                        NULL,
                        '2024-01-15 10:30:00+00'::TIMESTAMPTZ,
                        '{"id": 123}'::JSON
                    )
                    """
                )
                assert False, "Expected constraint violation"
            except duckdb.ConstraintException:
                pass

    def test_rejects_null_ingested_at(self) -> None:
        """Verify table rejects NULL ingested_at values."""
        with duckdb.connect(":memory:") as connection:
            initialize_schema(connection)

            try:
                connection.execute(
                    """
                    INSERT INTO raw_hn_items (load_id, ingested_at, payload)
                    VALUES (
                        'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11'::UUID,
                        NULL,
                        '{"id": 123}'::JSON
                    )
                    """
                )
                assert False, "Expected constraint violation"
            except duckdb.ConstraintException:
                pass

    def test_rejects_null_payload(self) -> None:
        """Verify table rejects NULL payload values."""
        with duckdb.connect(":memory:") as connection:
            initialize_schema(connection)

            try:
                connection.execute(
                    """
                    INSERT INTO raw_hn_items (load_id, ingested_at, payload)
                    VALUES (
                        'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11'::UUID,
                        '2024-01-15 10:30:00+00'::TIMESTAMPTZ,
                        NULL
                    )
                    """
                )
                assert False, "Expected constraint violation"
            except duckdb.ConstraintException:
                pass

    def test_json_payload_queryable(self) -> None:
        """Verify JSON payload can be queried with json_extract."""
        with duckdb.connect(":memory:") as connection:
            initialize_schema(connection)

            connection.execute(
                """
                INSERT INTO raw_hn_items (load_id, ingested_at, payload)
                VALUES (
                    'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11'::UUID,
                    '2024-01-15 10:30:00+00'::TIMESTAMPTZ,
                    '{"id": 8863, "type": "story", "title": "Test Title"}'::JSON
                )
                """
            )

            result = connection.execute(
                """
                SELECT
                    payload->>'id' AS item_id,
                    payload->>'type' AS item_type,
                    payload->>'title' AS title
                FROM raw_hn_items
                """
            ).fetchone()

            assert result is not None
            assert result[0] == "8863"
            assert result[1] == "story"
            assert result[2] == "Test Title"
