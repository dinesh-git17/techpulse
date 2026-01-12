"""Unit tests for DuckDB database manager."""

import os
import tempfile
from pathlib import Path
from unittest import mock

import pytest

from techpulse.storage.exceptions import StorageConnectionError
from techpulse.storage.manager import (
    DATABASE_PATH_ENV_VAR,
    DEFAULT_DATABASE_PATH,
    DuckDBManager,
)


class TestManagerInitialization:
    """Test suite for DuckDBManager initialization."""

    def test_default_database_path(self) -> None:
        """Verify manager uses default path when no override provided."""
        with mock.patch.dict(os.environ, {}, clear=True):
            os.environ.pop(DATABASE_PATH_ENV_VAR, None)
            manager = DuckDBManager()
            expected_path = Path(DEFAULT_DATABASE_PATH).resolve()
            assert manager.database_path == expected_path

    def test_explicit_path_overrides_default(self) -> None:
        """Verify explicit path takes precedence over default."""
        explicit_path = "/custom/path/test.duckdb"
        manager = DuckDBManager(database_path=explicit_path)
        assert manager.database_path == Path(explicit_path).resolve()

    def test_env_var_overrides_default(self) -> None:
        """Verify environment variable takes precedence over default."""
        env_path = "/env/path/test.duckdb"
        with mock.patch.dict(os.environ, {DATABASE_PATH_ENV_VAR: env_path}):
            manager = DuckDBManager()
            assert manager.database_path == Path(env_path).resolve()

    def test_explicit_path_overrides_env_var(self) -> None:
        """Verify explicit path takes precedence over environment variable."""
        explicit_path = "/explicit/path/test.duckdb"
        env_path = "/env/path/test.duckdb"
        with mock.patch.dict(os.environ, {DATABASE_PATH_ENV_VAR: env_path}):
            manager = DuckDBManager(database_path=explicit_path)
            assert manager.database_path == Path(explicit_path).resolve()

    def test_relative_path_is_resolved_to_absolute(self) -> None:
        """Verify relative paths are converted to absolute paths."""
        relative_path = "data/test.duckdb"
        manager = DuckDBManager(database_path=relative_path)
        assert manager.database_path.is_absolute()
        assert manager.database_path == Path(relative_path).resolve()


class TestContextManager:
    """Test suite for context manager protocol."""

    def test_context_manager_creates_connection(self) -> None:
        """Verify database connection is created on context entry."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "test.duckdb"
            with DuckDBManager(database_path=str(db_path)) as manager:
                assert manager._connection is not None

    def test_context_manager_closes_connection(self) -> None:
        """Verify database connection is closed on context exit."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "test.duckdb"
            manager = DuckDBManager(database_path=str(db_path))
            with manager:
                pass
            assert manager._connection is None

    def test_get_connection_returns_active_connection(self) -> None:
        """Verify get_connection returns the active connection."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "test.duckdb"
            with DuckDBManager(database_path=str(db_path)) as manager:
                connection = manager.get_connection()
                assert connection is not None
                result = connection.execute("SELECT 1 AS value").fetchone()
                assert result is not None
                assert result[0] == 1

    def test_get_connection_outside_context_raises_error(self) -> None:
        """Verify RuntimeError when get_connection called outside context."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "test.duckdb"
            manager = DuckDBManager(database_path=str(db_path))
            with pytest.raises(RuntimeError) as exc_info:
                manager.get_connection()
            assert "context manager" in str(exc_info.value)


class TestDirectoryCreation:
    """Test suite for parent directory creation."""

    def test_creates_parent_directory_if_missing(self) -> None:
        """Verify parent directories are created when they do not exist."""
        with tempfile.TemporaryDirectory() as temp_dir:
            nested_path = Path(temp_dir) / "level1" / "level2" / "test.duckdb"
            assert not nested_path.parent.exists()

            with DuckDBManager(database_path=str(nested_path)) as manager:
                assert nested_path.parent.exists()
                assert manager.database_path == nested_path.resolve()

    def test_handles_existing_parent_directory(self) -> None:
        """Verify no error when parent directory already exists."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "test.duckdb"
            assert db_path.parent.exists()

            with DuckDBManager(database_path=str(db_path)) as manager:
                assert manager._connection is not None


class TestDatabaseCreation:
    """Test suite for database file creation."""

    def test_creates_database_file_if_missing(self) -> None:
        """Verify database file is created when it does not exist."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "new_database.duckdb"
            assert not db_path.exists()

            with DuckDBManager(database_path=str(db_path)):
                pass

            assert db_path.exists()

    def test_opens_existing_database_file(self) -> None:
        """Verify existing database file is opened without error."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "existing.duckdb"

            with DuckDBManager(database_path=str(db_path)) as manager:
                connection = manager.get_connection()
                connection.execute("CREATE TABLE test_table (id INTEGER)")

            with DuckDBManager(database_path=str(db_path)) as manager:
                connection = manager.get_connection()
                result = connection.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                ).fetchall()
                table_names = [row[0] for row in result]
                assert "test_table" in table_names


class TestConnectionOperations:
    """Test suite for database connection operations."""

    def test_execute_query(self) -> None:
        """Verify SQL queries can be executed through the connection."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "test.duckdb"
            with DuckDBManager(database_path=str(db_path)) as manager:
                connection = manager.get_connection()
                connection.execute("CREATE TABLE items (id INTEGER, name VARCHAR)")
                connection.execute("INSERT INTO items VALUES (1, 'test')")
                result = connection.execute(
                    "SELECT * FROM items WHERE id = 1"
                ).fetchone()
                assert result is not None
                assert result[0] == 1
                assert result[1] == "test"


class TestErrorHandling:
    """Test suite for error handling scenarios."""

    def test_raises_storage_connection_error_on_permission_denied(self) -> None:
        """Verify StorageConnectionError raised when directory creation fails."""
        with mock.patch("pathlib.Path.mkdir") as mock_mkdir:
            mock_mkdir.side_effect = PermissionError("Permission denied")
            with mock.patch("pathlib.Path.exists", return_value=False):
                manager = DuckDBManager(database_path="/nonexistent/path/test.duckdb")
                with pytest.raises(StorageConnectionError) as exc_info:
                    manager._ensure_parent_directory_exists()
                assert "Permission denied" in exc_info.value.reason

    def test_storage_connection_error_includes_path(self) -> None:
        """Verify StorageConnectionError includes the database path."""
        test_path = "/test/path/database.duckdb"
        with mock.patch("pathlib.Path.mkdir") as mock_mkdir:
            mock_mkdir.side_effect = OSError("Filesystem error")
            with mock.patch("pathlib.Path.exists", return_value=False):
                manager = DuckDBManager(database_path=test_path)
                with pytest.raises(StorageConnectionError) as exc_info:
                    manager._ensure_parent_directory_exists()
                assert test_path in exc_info.value.path


class TestConstantExports:
    """Test suite for module constant exports."""

    def test_default_database_path_constant(self) -> None:
        """Verify DEFAULT_DATABASE_PATH is defined correctly."""
        assert DEFAULT_DATABASE_PATH == "backend/data/techpulse.duckdb"

    def test_env_var_name_constant(self) -> None:
        """Verify DATABASE_PATH_ENV_VAR is defined correctly."""
        assert DATABASE_PATH_ENV_VAR == "TECHPULSE_DB_PATH"
