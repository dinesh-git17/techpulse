"""Bronze layer schema definitions and initialization.

This module defines the DDL for the raw_hn_items table and provides
functions to initialize the database schema. The schema follows the
append-only Bronze layer pattern where raw API responses are stored
as JSON blobs with ingestion metadata.
"""

import duckdb
import structlog

logger = structlog.get_logger(__name__)

RAW_HN_ITEMS_TABLE = "raw_hn_items"

RAW_HN_ITEMS_DDL = """
CREATE TABLE IF NOT EXISTS raw_hn_items (
    load_id UUID NOT NULL,
    ingested_at TIMESTAMPTZ NOT NULL,
    payload JSON NOT NULL
)
"""


def initialize_schema(connection: duckdb.DuckDBPyConnection) -> None:
    """Create Bronze layer tables if they do not exist.

    Executes idempotent DDL statements to ensure all required tables
    exist in the database. Safe to call multiple times.

    Args:
        connection: An active DuckDB database connection.

    Raises:
        duckdb.Error: If DDL execution fails due to database errors.
    """
    log = logger.bind(component="schema")
    log.debug("schema_initialization_start")

    connection.execute(RAW_HN_ITEMS_DDL)

    log.debug("schema_initialization_complete", table=RAW_HN_ITEMS_TABLE)


def table_exists(connection: duckdb.DuckDBPyConnection, table_name: str) -> bool:
    """Check if a table exists in the database.

    Args:
        connection: An active DuckDB database connection.
        table_name: The name of the table to check.

    Returns:
        bool: True if the table exists, False otherwise.
    """
    result = connection.execute(
        """
        SELECT COUNT(*)
        FROM information_schema.tables
        WHERE table_name = ?
        """,
        [table_name],
    ).fetchone()

    return result is not None and result[0] > 0
