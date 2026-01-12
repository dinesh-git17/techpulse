"""Unit tests for DuckDB data store."""

import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import pytest

from techpulse.storage.exceptions import InvalidPayloadError
from techpulse.storage.schema import RAW_HN_ITEMS_TABLE
from techpulse.storage.store import DuckDBStore


class TestStoreInitialization:
    """Test suite for DuckDBStore initialization."""

    def test_store_creates_manager(self) -> None:
        """Verify store creates an internal DuckDBManager."""
        store = DuckDBStore()
        assert store.manager is not None

    def test_store_accepts_database_path(self) -> None:
        """Verify store passes database_path to manager."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "test.duckdb"
            store = DuckDBStore(database_path=str(db_path))
            assert store.manager.database_path == db_path.resolve()


class TestContextManager:
    """Test suite for context manager protocol."""

    def test_context_manager_opens_connection(self) -> None:
        """Verify store opens database connection on context entry."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "test.duckdb"
            with DuckDBStore(database_path=str(db_path)) as store:
                assert store.manager._connection is not None

    def test_context_manager_closes_connection(self) -> None:
        """Verify store closes database connection on context exit."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "test.duckdb"
            store = DuckDBStore(database_path=str(db_path))
            with store:
                pass
            assert store.manager._connection is None

    def test_insert_outside_context_raises_error(self) -> None:
        """Verify RuntimeError when insert_items called outside context."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "test.duckdb"
            store = DuckDBStore(database_path=str(db_path))
            with pytest.raises(RuntimeError) as exc_info:
                store.insert_items(uuid4(), [{"id": 1}])
            assert "context manager" in str(exc_info.value)


class TestInsertItems:
    """Test suite for insert_items method."""

    def test_inserts_single_item(self) -> None:
        """Verify single item is inserted correctly."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "test.duckdb"
            with DuckDBStore(database_path=str(db_path)) as store:
                load_id = uuid4()
                items = [{"id": 123, "type": "story", "title": "Test"}]

                count = store.insert_items(load_id, items)

                assert count == 1
                assert store.get_item_count() == 1

    def test_inserts_multiple_items(self) -> None:
        """Verify multiple items are inserted correctly."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "test.duckdb"
            with DuckDBStore(database_path=str(db_path)) as store:
                load_id = uuid4()
                items = [
                    {"id": 1, "type": "story"},
                    {"id": 2, "type": "comment"},
                    {"id": 3, "type": "job"},
                ]

                count = store.insert_items(load_id, items)

                assert count == 3
                assert store.get_item_count() == 3

    def test_empty_batch_returns_zero(self) -> None:
        """Verify empty item list returns zero without error."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "test.duckdb"
            with DuckDBStore(database_path=str(db_path)) as store:
                load_id = uuid4()

                count = store.insert_items(load_id, [])

                assert count == 0
                assert store.get_item_count() == 0

    def test_preserves_load_id(self) -> None:
        """Verify load_id is correctly stored in inserted rows."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "test.duckdb"
            with DuckDBStore(database_path=str(db_path)) as store:
                load_id = uuid4()
                items = [{"id": 123}]

                store.insert_items(load_id, items)

                connection = store.manager.get_connection()
                result = connection.execute(
                    f"SELECT load_id FROM {RAW_HN_ITEMS_TABLE}"
                ).fetchone()

                assert result is not None
                assert str(result[0]) == str(load_id)

    def test_generates_utc_timestamp(self) -> None:
        """Verify ingested_at timestamp is generated with timezone info."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "test.duckdb"
            with DuckDBStore(database_path=str(db_path)) as store:
                load_id = uuid4()
                items = [{"id": 123}]

                before_insert = datetime.now(timezone.utc)
                store.insert_items(load_id, items)
                after_insert = datetime.now(timezone.utc)

                connection = store.manager.get_connection()
                result = connection.execute(
                    f"SELECT ingested_at AT TIME ZONE 'UTC' FROM {RAW_HN_ITEMS_TABLE}"
                ).fetchone()

                assert result is not None
                timestamp = result[0]
                timestamp_utc = timestamp.replace(tzinfo=timezone.utc)
                assert before_insert <= timestamp_utc <= after_insert

    def test_preserves_json_payload(self) -> None:
        """Verify JSON payload is stored intact."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "test.duckdb"
            with DuckDBStore(database_path=str(db_path)) as store:
                load_id = uuid4()
                original_item = {
                    "id": 8863,
                    "type": "story",
                    "title": "My YC app: Dropbox",
                    "score": 111,
                    "by": "dhouston",
                }

                store.insert_items(load_id, [original_item])

                connection = store.manager.get_connection()
                result = connection.execute(
                    f"""
                    SELECT
                        payload->>'id' AS item_id,
                        payload->>'type' AS item_type,
                        payload->>'title' AS title,
                        payload->>'score' AS score,
                        payload->>'by' AS author
                    FROM {RAW_HN_ITEMS_TABLE}
                    """
                ).fetchone()

                assert result is not None
                assert result[0] == "8863"
                assert result[1] == "story"
                assert result[2] == "My YC app: Dropbox"
                assert result[3] == "111"
                assert result[4] == "dhouston"


class TestTransactionBehavior:
    """Test suite for transaction atomicity."""

    def test_all_items_share_same_timestamp(self) -> None:
        """Verify all items in a batch have identical ingested_at."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "test.duckdb"
            with DuckDBStore(database_path=str(db_path)) as store:
                load_id = uuid4()
                items = [{"id": i} for i in range(100)]

                store.insert_items(load_id, items)

                connection = store.manager.get_connection()
                result = connection.execute(
                    f"SELECT DISTINCT ingested_at FROM {RAW_HN_ITEMS_TABLE}"
                ).fetchall()

                assert len(result) == 1

    def test_all_items_share_same_load_id(self) -> None:
        """Verify all items in a batch have identical load_id."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "test.duckdb"
            with DuckDBStore(database_path=str(db_path)) as store:
                load_id = uuid4()
                items = [{"id": i} for i in range(50)]

                store.insert_items(load_id, items)

                connection = store.manager.get_connection()
                result = connection.execute(
                    f"SELECT DISTINCT load_id FROM {RAW_HN_ITEMS_TABLE}"
                ).fetchall()

                assert len(result) == 1
                assert str(result[0][0]) == str(load_id)


class TestInvalidPayloadHandling:
    """Test suite for invalid payload error handling."""

    def test_rejects_non_serializable_object(self) -> None:
        """Verify InvalidPayloadError raised for non-JSON-serializable items."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "test.duckdb"
            with DuckDBStore(database_path=str(db_path)) as store:
                load_id = uuid4()
                items = [{"id": 1, "callback": lambda x: x}]

                with pytest.raises(InvalidPayloadError) as exc_info:
                    store.insert_items(load_id, items)

                assert exc_info.value.payload_index == 0
                assert "serialize" in exc_info.value.reason.lower()

    def test_reports_correct_index_for_invalid_item(self) -> None:
        """Verify InvalidPayloadError includes correct item index."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "test.duckdb"
            with DuckDBStore(database_path=str(db_path)) as store:
                load_id = uuid4()
                items = [
                    {"id": 1},
                    {"id": 2},
                    {"id": 3, "bad": object()},
                    {"id": 4},
                ]

                with pytest.raises(InvalidPayloadError) as exc_info:
                    store.insert_items(load_id, items)

                assert exc_info.value.payload_index == 2

    def test_rollback_on_invalid_payload(self) -> None:
        """Verify no items are inserted when one fails validation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "test.duckdb"
            with DuckDBStore(database_path=str(db_path)) as store:
                load_id = uuid4()
                items = [
                    {"id": 1},
                    {"id": 2},
                    {"id": 3, "func": lambda: None},
                ]

                with pytest.raises(InvalidPayloadError):
                    store.insert_items(load_id, items)

                assert store.get_item_count() == 0


class TestMultipleBatches:
    """Test suite for multiple batch inserts."""

    def test_multiple_batches_with_different_load_ids(self) -> None:
        """Verify multiple batches can be inserted with different load_ids."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "test.duckdb"
            with DuckDBStore(database_path=str(db_path)) as store:
                load_id_1 = uuid4()
                load_id_2 = uuid4()

                store.insert_items(load_id_1, [{"id": 1}, {"id": 2}])
                store.insert_items(load_id_2, [{"id": 3}, {"id": 4}, {"id": 5}])

                assert store.get_item_count() == 5

                connection = store.manager.get_connection()
                result = connection.execute(
                    f"SELECT DISTINCT load_id FROM {RAW_HN_ITEMS_TABLE}"
                ).fetchall()

                assert len(result) == 2

    def test_duplicate_items_allowed(self) -> None:
        """Verify duplicate item IDs can be inserted (append-only)."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "test.duckdb"
            with DuckDBStore(database_path=str(db_path)) as store:
                load_id_1 = uuid4()
                load_id_2 = uuid4()

                store.insert_items(load_id_1, [{"id": 123, "score": 100}])
                store.insert_items(load_id_2, [{"id": 123, "score": 150}])

                assert store.get_item_count() == 2


class TestGetItemCount:
    """Test suite for get_item_count method."""

    def test_returns_zero_for_empty_table(self) -> None:
        """Verify get_item_count returns 0 for empty table."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "test.duckdb"
            with DuckDBStore(database_path=str(db_path)) as store:
                assert store.get_item_count() == 0

    def test_returns_correct_count_after_inserts(self) -> None:
        """Verify get_item_count returns correct count after inserts."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "test.duckdb"
            with DuckDBStore(database_path=str(db_path)) as store:
                store.insert_items(uuid4(), [{"id": i} for i in range(25)])

                assert store.get_item_count() == 25


class TestPerformance:
    """Test suite for performance requirements."""

    def test_insert_1000_items_within_timeout(self) -> None:
        """Verify 1000 items can be inserted within reasonable time."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "test.duckdb"
            with DuckDBStore(database_path=str(db_path)) as store:
                load_id = uuid4()
                items = [
                    {
                        "id": i,
                        "type": "story",
                        "title": f"Story number {i}",
                        "score": i * 10,
                        "by": f"user{i}",
                        "time": 1700000000 + i,
                        "descendants": i % 100,
                    }
                    for i in range(1000)
                ]

                start_time = time.perf_counter()
                count = store.insert_items(load_id, items)
                elapsed_time = time.perf_counter() - start_time

                assert count == 1000
                assert store.get_item_count() == 1000
                assert elapsed_time < 10.0  # Should complete well under 10 seconds


class TestComplexPayloads:
    """Test suite for complex JSON payload handling."""

    def test_handles_nested_objects(self) -> None:
        """Verify nested JSON objects are preserved."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "test.duckdb"
            with DuckDBStore(database_path=str(db_path)) as store:
                load_id = uuid4()
                items = [
                    {
                        "id": 123,
                        "metadata": {
                            "source": "hn",
                            "tags": ["tech", "startup"],
                        },
                    }
                ]

                store.insert_items(load_id, items)

                connection = store.manager.get_connection()
                result = connection.execute(
                    f"""
                    SELECT payload->'metadata'->>'source' AS source
                    FROM {RAW_HN_ITEMS_TABLE}
                    """
                ).fetchone()

                assert result is not None
                assert result[0] == "hn"

    def test_handles_arrays(self) -> None:
        """Verify JSON arrays are preserved."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "test.duckdb"
            with DuckDBStore(database_path=str(db_path)) as store:
                load_id = uuid4()
                items = [{"id": 123, "kids": [456, 789, 101112]}]

                store.insert_items(load_id, items)

                connection = store.manager.get_connection()
                result = connection.execute(
                    f"""
                    SELECT json_array_length(payload->'kids') AS kids_count
                    FROM {RAW_HN_ITEMS_TABLE}
                    """
                ).fetchone()

                assert result is not None
                assert result[0] == 3

    def test_handles_unicode(self) -> None:
        """Verify Unicode characters are preserved."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "test.duckdb"
            with DuckDBStore(database_path=str(db_path)) as store:
                load_id = uuid4()
                unicode_title = "Hello 世界 🚀"
                items = [{"id": 123, "title": unicode_title}]

                store.insert_items(load_id, items)

                connection = store.manager.get_connection()
                result = connection.execute(
                    f"""
                    SELECT payload->>'title' AS title
                    FROM {RAW_HN_ITEMS_TABLE}
                    """
                ).fetchone()

                assert result is not None
                assert result[0] == unicode_title

    def test_handles_null_values_in_payload(self) -> None:
        """Verify null values within JSON are preserved."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "test.duckdb"
            with DuckDBStore(database_path=str(db_path)) as store:
                load_id = uuid4()
                items = [{"id": 123, "url": None, "text": None}]

                store.insert_items(load_id, items)

                connection = store.manager.get_connection()
                result = connection.execute(
                    f"""
                    SELECT
                        payload->>'url' AS url,
                        payload->>'text' AS text
                    FROM {RAW_HN_ITEMS_TABLE}
                    """
                ).fetchone()

                assert result is not None
                assert result[0] is None
                assert result[1] is None
