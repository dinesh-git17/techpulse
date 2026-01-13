"""Read-only database session management for the API layer.

This module provides the DatabaseSessionManager class for managing
read-only connections to the DuckDB warehouse. It yields thread-safe
cursors for API endpoints through FastAPI's dependency injection.
"""

from collections.abc import Generator
from pathlib import Path
from typing import Optional

import duckdb
import structlog

from techpulse.api.exceptions.domain import DatabaseConnectionError

logger = structlog.get_logger(__name__)


class DatabaseSessionManager:
    """Manage read-only database sessions for API requests.

    This class handles the lifecycle of a read-only DuckDB connection,
    providing thread-safe cursors to API endpoints. The connection is
    opened once at application startup and closed at shutdown.

    The read-only constraint is enforced at the connection level,
    preventing any accidental mutations to the Gold layer data.

    Attributes:
        database_path: The resolved path to the DuckDB database file.

    Example:
        >>> manager = DatabaseSessionManager(Path("data/techpulse.duckdb"))
        >>> manager.connect()
        >>> cursor = manager.get_cursor()
        >>> result = cursor.execute("SELECT 1").fetchone()
        >>> manager.close()
    """

    def __init__(self, database_path: Path) -> None:
        """Initialize the session manager with database path.

        Args:
            database_path: Path to the DuckDB database file.
        """
        self.database_path = database_path
        self._connection: Optional[duckdb.DuckDBPyConnection] = None
        self._log = logger.bind(
            component="DatabaseSessionManager",
            database_path=str(database_path),
        )

    def connect(self) -> None:
        """Establish a read-only connection to the database.

        Opens a connection with read_only=True to prevent any write
        operations. Validates the connection by executing a simple query.

        Raises:
            DatabaseConnectionError: If the database file does not exist
                or the connection cannot be established.
        """
        if self._connection is not None:
            self._log.warning("connection_already_open")
            return

        if not self.database_path.exists():
            raise DatabaseConnectionError(
                path=str(self.database_path),
                reason="Database file does not exist",
            )

        try:
            self._connection = duckdb.connect(
                str(self.database_path),
                read_only=True,
            )
            self._connection.execute("SELECT 1")
            self._log.info("database_connection_established", read_only=True)
        except duckdb.IOException as error:
            raise DatabaseConnectionError(
                path=str(self.database_path),
                reason=str(error),
            ) from error
        except duckdb.Error as error:
            raise DatabaseConnectionError(
                path=str(self.database_path),
                reason=f"Database error: {error}",
            ) from error

    def close(self) -> None:
        """Close the database connection.

        Safely closes the connection if one is open. This method is
        idempotent and can be called multiple times without error.
        """
        if self._connection is not None:
            self._connection.close()
            self._connection = None
            self._log.info("database_connection_closed")

    def get_cursor(self) -> duckdb.DuckDBPyConnection:
        """Return a cursor from the read-only connection.

        DuckDB cursors from a read-only connection are thread-safe for
        concurrent read operations. Each API request should obtain its
        own cursor through the get_db_cursor dependency.

        Returns:
            A cursor for executing read-only queries.

        Raises:
            DatabaseConnectionError: If no connection has been established.
        """
        if self._connection is None:
            raise DatabaseConnectionError(
                path=str(self.database_path),
                reason="No active database connection",
            )
        return self._connection.cursor()

    def is_connected(self) -> bool:
        """Check if a database connection is active.

        Returns:
            True if connected, False otherwise.
        """
        return self._connection is not None

    def health_check(self) -> bool:
        """Verify database connectivity with a simple query.

        Executes SELECT 1 to confirm the connection is responsive.

        Returns:
            True if the health check passes, False otherwise.
        """
        if self._connection is None:
            return False
        try:
            self._connection.execute("SELECT 1").fetchone()
            return True
        except duckdb.Error:
            return False


_session_manager: Optional[DatabaseSessionManager] = None


def init_session_manager(database_path: Path) -> DatabaseSessionManager:
    """Initialize the global session manager.

    Creates and connects a DatabaseSessionManager instance. This should
    be called once during application startup.

    Args:
        database_path: Path to the DuckDB database file.

    Returns:
        The initialized and connected session manager.

    Raises:
        DatabaseConnectionError: If connection fails.
    """
    global _session_manager
    _session_manager = DatabaseSessionManager(database_path)
    _session_manager.connect()
    return _session_manager


def close_session_manager() -> None:
    """Close and clear the global session manager.

    Safely closes the database connection and clears the global
    reference. This should be called during application shutdown.
    """
    global _session_manager
    if _session_manager is not None:
        _session_manager.close()
        _session_manager = None


def get_session_manager() -> DatabaseSessionManager:
    """Retrieve the global session manager instance.

    Returns:
        The active session manager.

    Raises:
        DatabaseConnectionError: If the session manager has not been
            initialized.
    """
    if _session_manager is None:
        raise DatabaseConnectionError(
            path="unknown",
            reason="Session manager not initialized",
        )
    return _session_manager


def get_db_cursor() -> Generator[duckdb.DuckDBPyConnection, None, None]:
    """FastAPI dependency that yields a database cursor.

    Provides a thread-safe cursor for the request duration and ensures
    proper cleanup after the request completes.

    Yields:
        A DuckDB cursor for executing read-only queries.

    Raises:
        DatabaseConnectionError: If the session manager is not initialized
            or no connection is available.

    Example:
        >>> @app.get("/items")
        >>> def get_items(cursor: DuckDBPyConnection = Depends(get_db_cursor)):
        ...     return cursor.execute("SELECT * FROM items").fetchall()
    """
    manager = get_session_manager()
    cursor = manager.get_cursor()
    try:
        yield cursor
    finally:
        cursor.close()
