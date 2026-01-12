"""DuckDB database lifecycle and connection management.

This module provides the DuckDBManager class for handling database file creation,
connection establishment, and safe resource cleanup. It implements retry logic
with exponential backoff for lock acquisition failures.
"""

import os
import time
from pathlib import Path
from types import TracebackType
from typing import Optional, Self

import duckdb
import structlog

from techpulse.storage.exceptions import StorageConnectionError
from techpulse.storage.schema import initialize_schema

logger = structlog.get_logger(__name__)

DEFAULT_DATABASE_PATH = "backend/data/techpulse.duckdb"
DATABASE_PATH_ENV_VAR = "TECHPULSE_DB_PATH"
MAX_CONNECTION_RETRIES = 5
INITIAL_RETRY_DELAY_SECONDS = 0.5
MAX_RETRY_DELAY_SECONDS = 16.0


class DuckDBManager:
    """Manage DuckDB database lifecycle and connections.

    This class handles the creation, connection, and safe closing of the
    persistent DuckDB database file. It reads the database path from the
    TECHPULSE_DB_PATH environment variable, falling back to a default path
    when not set.

    The manager implements retry logic with exponential backoff for lock
    acquisition failures, which can occur when another process holds the
    write lock.

    Attributes:
        database_path: The resolved path to the DuckDB database file.

    Example:
        >>> with DuckDBManager() as manager:
        ...     connection = manager.get_connection()
        ...     result = connection.execute("SELECT 1").fetchone()
    """

    def __init__(self, database_path: Optional[str] = None) -> None:
        """Initialize the DuckDB manager.

        The database path is resolved in the following order:
        1. Explicit database_path parameter (if provided)
        2. TECHPULSE_DB_PATH environment variable (if set)
        3. Default path: backend/data/techpulse.duckdb

        Args:
            database_path: Optional explicit path to the database file.
                          Overrides environment variable and default.
        """
        self.database_path = self._resolve_database_path(database_path)
        self._connection: Optional[duckdb.DuckDBPyConnection] = None
        self._log = logger.bind(
            component="DuckDBManager",
            database_path=str(self.database_path),
        )

    def _resolve_database_path(self, explicit_path: Optional[str]) -> Path:
        """Resolve the database file path from configuration sources.

        Args:
            explicit_path: An explicitly provided path, or None.

        Returns:
            Path: The resolved absolute path to the database file.
        """
        if explicit_path is not None:
            return Path(explicit_path).resolve()

        env_path = os.environ.get(DATABASE_PATH_ENV_VAR)
        if env_path is not None:
            return Path(env_path).resolve()

        return Path(DEFAULT_DATABASE_PATH).resolve()

    def _ensure_parent_directory_exists(self) -> None:
        """Create parent directories for the database file if they do not exist.

        Raises:
            StorageConnectionError: If directory creation fails due to
                permission errors or other filesystem issues.
        """
        parent_directory = self.database_path.parent
        if parent_directory.exists():
            return

        try:
            parent_directory.mkdir(parents=True, exist_ok=True)
            self._log.debug(
                "parent_directory_created",
                directory=str(parent_directory),
            )
        except OSError as error:
            raise StorageConnectionError(
                path=str(self.database_path),
                reason=f"Failed to create parent directory: {error}",
            ) from error

    def _attempt_connection(self) -> duckdb.DuckDBPyConnection:
        """Attempt to establish a connection to the database.

        Returns:
            duckdb.DuckDBPyConnection: An active database connection.

        Raises:
            duckdb.IOException: If the database file is locked or inaccessible.
        """
        return duckdb.connect(str(self.database_path))

    def _connect_with_retry(self) -> duckdb.DuckDBPyConnection:
        """Establish a database connection with exponential backoff retry.

        Implements retry logic for transient lock acquisition failures.
        Each retry doubles the wait time up to a maximum delay.

        Returns:
            duckdb.DuckDBPyConnection: An active database connection.

        Raises:
            StorageConnectionError: If connection cannot be established
                after exhausting all retry attempts.
        """
        last_exception: Optional[Exception] = None
        retry_delay = INITIAL_RETRY_DELAY_SECONDS

        for attempt in range(1, MAX_CONNECTION_RETRIES + 1):
            try:
                connection = self._attempt_connection()
                if attempt > 1:
                    self._log.info(
                        "connection_established_after_retry",
                        attempt=attempt,
                    )
                return connection
            except duckdb.IOException as error:
                last_exception = error
                error_message = str(error).lower()

                is_lock_error = "lock" in error_message or "busy" in error_message
                if not is_lock_error:
                    raise StorageConnectionError(
                        path=str(self.database_path),
                        reason=str(error),
                    ) from error

                if attempt < MAX_CONNECTION_RETRIES:
                    self._log.warning(
                        "connection_retry",
                        attempt=attempt,
                        max_attempts=MAX_CONNECTION_RETRIES,
                        retry_delay_seconds=retry_delay,
                        error=str(error),
                    )
                    time.sleep(retry_delay)
                    retry_delay = min(retry_delay * 2, MAX_RETRY_DELAY_SECONDS)
            except Exception as error:
                raise StorageConnectionError(
                    path=str(self.database_path),
                    reason=str(error),
                ) from error

        raise StorageConnectionError(
            path=str(self.database_path),
            reason=f"Failed after {MAX_CONNECTION_RETRIES} attempts. "
            f"Last error: {last_exception}",
        )

    def __enter__(self) -> Self:
        """Enter the context manager and establish database connection.

        Creates parent directories if needed, establishes a connection
        to the database file with retry logic for lock conflicts, and
        initializes the Bronze layer schema.

        Returns:
            Self: The manager instance with an active database connection.

        Raises:
            StorageConnectionError: If the connection cannot be established
                or schema initialization fails.
        """
        self._ensure_parent_directory_exists()
        self._connection = self._connect_with_retry()
        try:
            initialize_schema(self._connection)
        except Exception:
            self._connection.close()
            self._connection = None
            raise
        self._log.debug("database_connection_established")
        return self

    def __exit__(
        self,
        exc_type: Optional[type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> None:
        """Exit the context manager and close the database connection.

        Args:
            exc_type: Exception type if an exception was raised.
            exc_val: Exception value if an exception was raised.
            exc_tb: Exception traceback if an exception was raised.
        """
        if self._connection is not None:
            self._connection.close()
            self._connection = None
            self._log.debug("database_connection_closed")

    def get_connection(self) -> duckdb.DuckDBPyConnection:
        """Return the active database connection.

        Returns:
            duckdb.DuckDBPyConnection: The active database connection.

        Raises:
            RuntimeError: If called outside of a context manager.
        """
        if self._connection is None:
            raise RuntimeError(
                "DuckDBManager must be used as a context manager. "
                "Use 'with DuckDBManager() as manager:'"
            )
        return self._connection
