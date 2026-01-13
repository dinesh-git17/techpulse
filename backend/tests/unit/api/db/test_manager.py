"""Unit tests for DatabaseSessionManager and related functions."""

import tempfile
from pathlib import Path
from typing import Generator
from unittest.mock import MagicMock, patch

import duckdb
import pytest

from techpulse.api.db import manager as manager_module
from techpulse.api.db.manager import (
    DatabaseSessionManager,
    close_session_manager,
    get_db_cursor,
    get_session_manager,
    init_session_manager,
)
from techpulse.api.exceptions.domain import DatabaseConnectionError


@pytest.fixture
def temp_db_path() -> Generator[Path, None, None]:
    """Create a temporary DuckDB database for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = Path(temp_dir) / "test.duckdb"
        conn = duckdb.connect(str(db_path))
        conn.execute("CREATE TABLE test_table (id INTEGER)")
        conn.close()
        yield db_path


@pytest.fixture
def nonexistent_db_path() -> Path:
    """Return a path to a nonexistent database file."""
    return Path("/nonexistent/path/to/database.duckdb")


@pytest.fixture(autouse=True)
def reset_global_manager() -> Generator[None, None, None]:
    """Reset the global session manager before and after each test."""
    manager_module._session_manager = None
    yield
    manager_module._session_manager = None


class TestDatabaseSessionManager:
    """Test suite for DatabaseSessionManager class."""

    def test_init_sets_database_path(self, temp_db_path: Path) -> None:
        """Verify manager initializes with correct database path."""
        manager = DatabaseSessionManager(temp_db_path)
        assert manager.database_path == temp_db_path

    def test_init_connection_is_none(self, temp_db_path: Path) -> None:
        """Verify connection is None before connect is called."""
        manager = DatabaseSessionManager(temp_db_path)
        assert manager._connection is None

    def test_connect_establishes_connection(self, temp_db_path: Path) -> None:
        """Verify connect establishes a database connection."""
        manager = DatabaseSessionManager(temp_db_path)
        manager.connect()
        try:
            assert manager._connection is not None
            assert manager.is_connected()
        finally:
            manager.close()

    def test_connect_uses_read_only_mode(self, temp_db_path: Path) -> None:
        """Verify connection is opened in read-only mode."""
        manager = DatabaseSessionManager(temp_db_path)
        manager.connect()
        try:
            with pytest.raises(duckdb.InvalidInputException):
                manager._connection.execute(  # type: ignore[union-attr]
                    "INSERT INTO test_table VALUES (1)"
                )
        finally:
            manager.close()

    def test_connect_raises_on_missing_file(self, nonexistent_db_path: Path) -> None:
        """Verify connect raises DatabaseConnectionError for missing file."""
        manager = DatabaseSessionManager(nonexistent_db_path)
        with pytest.raises(DatabaseConnectionError) as exc_info:
            manager.connect()
        assert "does not exist" in str(exc_info.value)
        assert str(nonexistent_db_path) in exc_info.value.path

    def test_connect_warns_if_already_connected(self, temp_db_path: Path) -> None:
        """Verify connect logs warning when called on open connection."""
        manager = DatabaseSessionManager(temp_db_path)
        manager.connect()
        try:
            manager.connect()
            assert manager.is_connected()
        finally:
            manager.close()

    def test_close_closes_connection(self, temp_db_path: Path) -> None:
        """Verify close properly closes the connection."""
        manager = DatabaseSessionManager(temp_db_path)
        manager.connect()
        manager.close()
        assert manager._connection is None
        assert not manager.is_connected()

    def test_close_is_idempotent(self, temp_db_path: Path) -> None:
        """Verify close can be called multiple times safely."""
        manager = DatabaseSessionManager(temp_db_path)
        manager.close()
        manager.close()
        assert not manager.is_connected()

    def test_get_cursor_returns_cursor(self, temp_db_path: Path) -> None:
        """Verify get_cursor returns a valid cursor."""
        manager = DatabaseSessionManager(temp_db_path)
        manager.connect()
        try:
            cursor = manager.get_cursor()
            result = cursor.execute("SELECT 1").fetchone()
            assert result == (1,)
            cursor.close()
        finally:
            manager.close()

    def test_get_cursor_raises_when_not_connected(self, temp_db_path: Path) -> None:
        """Verify get_cursor raises DatabaseConnectionError if not connected."""
        manager = DatabaseSessionManager(temp_db_path)
        with pytest.raises(DatabaseConnectionError) as exc_info:
            manager.get_cursor()
        assert "No active database connection" in str(exc_info.value)

    def test_is_connected_returns_false_initially(self, temp_db_path: Path) -> None:
        """Verify is_connected returns False before connect."""
        manager = DatabaseSessionManager(temp_db_path)
        assert not manager.is_connected()

    def test_is_connected_returns_true_after_connect(self, temp_db_path: Path) -> None:
        """Verify is_connected returns True after connect."""
        manager = DatabaseSessionManager(temp_db_path)
        manager.connect()
        try:
            assert manager.is_connected()
        finally:
            manager.close()

    def test_health_check_returns_true_when_healthy(self, temp_db_path: Path) -> None:
        """Verify health_check returns True for healthy connection."""
        manager = DatabaseSessionManager(temp_db_path)
        manager.connect()
        try:
            assert manager.health_check()
        finally:
            manager.close()

    def test_health_check_returns_false_when_not_connected(
        self, temp_db_path: Path
    ) -> None:
        """Verify health_check returns False when not connected."""
        manager = DatabaseSessionManager(temp_db_path)
        assert not manager.health_check()

    def test_health_check_returns_false_on_closed_connection(
        self, temp_db_path: Path
    ) -> None:
        """Verify health_check returns False when internal connection is closed."""
        manager = DatabaseSessionManager(temp_db_path)
        manager.connect()
        try:
            assert manager._connection is not None
            manager._connection.close()
            assert not manager.health_check()
        finally:
            manager._connection = None


class TestGlobalSessionManagerFunctions:
    """Test suite for global session manager functions."""

    def test_init_session_manager_creates_and_connects(
        self, temp_db_path: Path
    ) -> None:
        """Verify init_session_manager creates a connected manager."""
        manager = init_session_manager(temp_db_path)
        try:
            assert manager.is_connected()
            assert manager_module._session_manager is manager
        finally:
            close_session_manager()

    def test_init_session_manager_raises_on_connection_failure(
        self, nonexistent_db_path: Path
    ) -> None:
        """Verify init_session_manager raises on connection failure."""
        with pytest.raises(DatabaseConnectionError):
            init_session_manager(nonexistent_db_path)

    def test_close_session_manager_closes_and_clears(self, temp_db_path: Path) -> None:
        """Verify close_session_manager closes connection and clears global."""
        init_session_manager(temp_db_path)
        close_session_manager()
        assert manager_module._session_manager is None

    def test_close_session_manager_is_safe_when_not_initialized(self) -> None:
        """Verify close_session_manager is safe when manager is None."""
        close_session_manager()
        assert manager_module._session_manager is None

    def test_get_session_manager_returns_initialized_manager(
        self, temp_db_path: Path
    ) -> None:
        """Verify get_session_manager returns the global manager."""
        manager = init_session_manager(temp_db_path)
        try:
            retrieved = get_session_manager()
            assert retrieved is manager
        finally:
            close_session_manager()

    def test_get_session_manager_raises_when_not_initialized(self) -> None:
        """Verify get_session_manager raises when not initialized."""
        with pytest.raises(DatabaseConnectionError) as exc_info:
            get_session_manager()
        assert "not initialized" in str(exc_info.value)


class TestGetDbCursor:
    """Test suite for get_db_cursor FastAPI dependency."""

    def test_get_db_cursor_yields_cursor(self, temp_db_path: Path) -> None:
        """Verify get_db_cursor yields a working cursor."""
        init_session_manager(temp_db_path)
        try:
            cursor_gen = get_db_cursor()
            cursor = next(cursor_gen)
            result = cursor.execute("SELECT 1").fetchone()
            assert result == (1,)
            try:
                next(cursor_gen)
            except StopIteration:
                pass
        finally:
            close_session_manager()

    def test_get_db_cursor_closes_cursor_on_exit(self, temp_db_path: Path) -> None:
        """Verify get_db_cursor closes cursor after generator exhaustion."""
        init_session_manager(temp_db_path)
        try:
            cursor_gen = get_db_cursor()
            cursor = next(cursor_gen)
            cursor_mock = MagicMock(wraps=cursor)

            with patch.object(
                manager_module._session_manager,
                "get_cursor",
                return_value=cursor_mock,
            ):
                cursor_gen2 = get_db_cursor()
                next(cursor_gen2)
                try:
                    next(cursor_gen2)
                except StopIteration:
                    pass
                cursor_mock.close.assert_called_once()
        finally:
            close_session_manager()

    def test_get_db_cursor_raises_when_not_initialized(self) -> None:
        """Verify get_db_cursor raises when session manager not initialized."""
        cursor_gen = get_db_cursor()
        with pytest.raises(DatabaseConnectionError):
            next(cursor_gen)


class TestDatabaseConnectionErrorHandling:
    """Test suite for database connection error scenarios."""

    def test_ioerror_wrapped_in_connection_error(self, temp_db_path: Path) -> None:
        """Verify duckdb.IOException is wrapped in DatabaseConnectionError."""
        manager = DatabaseSessionManager(temp_db_path)

        with patch("duckdb.connect", side_effect=duckdb.IOException("IO error")):
            with pytest.raises(DatabaseConnectionError) as exc_info:
                manager._connection = None
                manager.database_path.touch()
                manager.connect()
            assert "IO error" in exc_info.value.reason

    def test_generic_duckdb_error_wrapped(self, temp_db_path: Path) -> None:
        """Verify generic duckdb.Error is wrapped in DatabaseConnectionError."""
        manager = DatabaseSessionManager(temp_db_path)

        with patch("duckdb.connect", side_effect=duckdb.Error("DB error")):
            with pytest.raises(DatabaseConnectionError) as exc_info:
                manager._connection = None
                manager.database_path.touch()
                manager.connect()
            assert "Database error" in exc_info.value.reason
