"""Integration tests for read-path access verification.

This module verifies that data written to the Bronze layer can be correctly
read back using DuckDB's JSON extraction syntax. It tests the Single-Writer/
Multiple-Reader (SWMR) behavior and confirms payload fidelity.
"""

import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import duckdb

from techpulse.storage.schema import RAW_HN_ITEMS_TABLE
from techpulse.storage.store import DuckDBStore


class TestSingleWriterMultipleReader:
    """Test suite for read access after writer commits."""

    def test_read_connection_after_writer_closes(self) -> None:
        """Verify a read-only connection can query after writer commits and closes."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "swmr_test.duckdb"

            with DuckDBStore(database_path=str(db_path)) as store:
                load_id = uuid4()
                items = [{"id": 123, "type": "story", "title": "Test Story"}]
                store.insert_items(load_id, items)

            reader_connection = duckdb.connect(str(db_path), read_only=True)
            try:
                result = reader_connection.execute(
                    f"SELECT COUNT(*) FROM {RAW_HN_ITEMS_TABLE}"
                ).fetchone()

                assert result is not None
                assert result[0] == 1
            finally:
                reader_connection.close()

    def test_multiple_readers_concurrent(self) -> None:
        """Verify multiple read-only connections can query simultaneously."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "multi_reader_test.duckdb"

            with DuckDBStore(database_path=str(db_path)) as store:
                load_id = uuid4()
                items = [{"id": i, "type": "story"} for i in range(10)]
                store.insert_items(load_id, items)

            reader_1 = duckdb.connect(str(db_path), read_only=True)
            reader_2 = duckdb.connect(str(db_path), read_only=True)

            try:
                result_1 = reader_1.execute(
                    f"SELECT COUNT(*) FROM {RAW_HN_ITEMS_TABLE}"
                ).fetchone()
                result_2 = reader_2.execute(
                    f"SELECT COUNT(*) FROM {RAW_HN_ITEMS_TABLE}"
                ).fetchone()

                assert result_1 is not None
                assert result_2 is not None
                assert result_1[0] == 10
                assert result_2[0] == 10
            finally:
                reader_1.close()
                reader_2.close()

    def test_new_reader_sees_committed_data(self) -> None:
        """Verify new reader connection sees data after writer commits."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "commit_visibility_test.duckdb"

            with DuckDBStore(database_path=str(db_path)) as store:
                store.insert_items(uuid4(), [{"id": 1}])

            reader = duckdb.connect(str(db_path), read_only=True)
            try:
                result = reader.execute(
                    f"SELECT COUNT(*) FROM {RAW_HN_ITEMS_TABLE}"
                ).fetchone()
                assert result is not None
                assert result[0] == 1
            finally:
                reader.close()


class TestJSONExtraction:
    """Test suite for JSON extraction query patterns."""

    def test_json_extract_with_arrow_operator(self) -> None:
        """Verify JSON extraction using ->> operator."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "json_extract_test.duckdb"

            with DuckDBStore(database_path=str(db_path)) as store:
                load_id = uuid4()
                items = [
                    {
                        "id": 8863,
                        "type": "story",
                        "by": "dhouston",
                        "title": "My YC app: Dropbox",
                        "score": 111,
                        "time": 1175714200,
                    }
                ]
                store.insert_items(load_id, items)

            reader = duckdb.connect(str(db_path), read_only=True)
            try:
                result = reader.execute(
                    f"""
                    SELECT
                        payload->>'id' AS item_id,
                        payload->>'type' AS item_type,
                        payload->>'by' AS author,
                        payload->>'title' AS title,
                        payload->>'score' AS score
                    FROM {RAW_HN_ITEMS_TABLE}
                    """
                ).fetchone()

                assert result is not None
                assert result[0] == "8863"
                assert result[1] == "story"
                assert result[2] == "dhouston"
                assert result[3] == "My YC app: Dropbox"
                assert result[4] == "111"
            finally:
                reader.close()

    def test_json_extract_nested_objects(self) -> None:
        """Verify nested JSON object extraction using -> and ->> operators."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "nested_json_test.duckdb"

            with DuckDBStore(database_path=str(db_path)) as store:
                load_id = uuid4()
                items = [
                    {
                        "id": 123,
                        "metadata": {
                            "source": "hn_api",
                            "version": "v0",
                            "tags": ["tech", "startup"],
                        },
                    }
                ]
                store.insert_items(load_id, items)

            reader = duckdb.connect(str(db_path), read_only=True)
            try:
                result = reader.execute(
                    f"""
                    SELECT
                        payload->'metadata'->>'source' AS source,
                        payload->'metadata'->>'version' AS version
                    FROM {RAW_HN_ITEMS_TABLE}
                    """
                ).fetchone()

                assert result is not None
                assert result[0] == "hn_api"
                assert result[1] == "v0"
            finally:
                reader.close()

    def test_json_extract_array_elements(self) -> None:
        """Verify JSON array access and length functions."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "array_json_test.duckdb"

            with DuckDBStore(database_path=str(db_path)) as store:
                load_id = uuid4()
                items = [{"id": 123, "kids": [456, 789, 101112, 131415]}]
                store.insert_items(load_id, items)

            reader = duckdb.connect(str(db_path), read_only=True)
            try:
                result = reader.execute(
                    f"""
                    SELECT
                        json_array_length(payload->'kids') AS kids_count,
                        payload->'kids'->>0 AS first_kid,
                        payload->'kids'->>3 AS fourth_kid
                    FROM {RAW_HN_ITEMS_TABLE}
                    """
                ).fetchone()

                assert result is not None
                assert result[0] == 4
                assert result[1] == "456"
                assert result[2] == "131415"
            finally:
                reader.close()

    def test_json_filtering_in_where_clause(self) -> None:
        """Verify JSON fields can be used in WHERE clause filters."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "json_filter_test.duckdb"

            with DuckDBStore(database_path=str(db_path)) as store:
                load_id = uuid4()
                items = [
                    {"id": 1, "type": "story", "score": 100},
                    {"id": 2, "type": "comment", "score": 50},
                    {"id": 3, "type": "story", "score": 200},
                    {"id": 4, "type": "job", "score": 0},
                ]
                store.insert_items(load_id, items)

            reader = duckdb.connect(str(db_path), read_only=True)
            try:
                result = reader.execute(
                    f"""
                    SELECT payload->>'id' AS item_id
                    FROM {RAW_HN_ITEMS_TABLE}
                    WHERE payload->>'type' = 'story'
                    ORDER BY CAST(payload->>'score' AS INTEGER) DESC
                    """
                ).fetchall()

                assert len(result) == 2
                assert result[0][0] == "3"
                assert result[1][0] == "1"
            finally:
                reader.close()


class TestTimestampVerification:
    """Test suite for UTC timestamp verification."""

    def test_ingested_at_has_timezone_info(self) -> None:
        """Verify ingested_at timestamps include timezone information."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "tz_info_test.duckdb"

            with DuckDBStore(database_path=str(db_path)) as store:
                store.insert_items(uuid4(), [{"id": 123}])

            reader = duckdb.connect(str(db_path), read_only=True)
            try:
                result = reader.execute(
                    f"SELECT ingested_at FROM {RAW_HN_ITEMS_TABLE}"
                ).fetchone()

                assert result is not None
                timestamp = result[0]
                assert timestamp.tzinfo is not None
            finally:
                reader.close()

    def test_ingested_at_is_recent(self) -> None:
        """Verify ingested_at timestamp is within expected time range."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "recent_ts_test.duckdb"

            before_insert = datetime.now(timezone.utc)

            with DuckDBStore(database_path=str(db_path)) as store:
                store.insert_items(uuid4(), [{"id": 123}])

            after_insert = datetime.now(timezone.utc)

            reader = duckdb.connect(str(db_path), read_only=True)
            try:
                result = reader.execute(
                    f"""
                    SELECT ingested_at AT TIME ZONE 'UTC'
                    FROM {RAW_HN_ITEMS_TABLE}
                    """
                ).fetchone()

                assert result is not None
                timestamp = result[0].replace(tzinfo=timezone.utc)

                assert before_insert <= timestamp <= after_insert
            finally:
                reader.close()

    def test_batch_items_share_timestamp(self) -> None:
        """Verify all items in a batch have identical ingested_at values."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "batch_ts_test.duckdb"

            with DuckDBStore(database_path=str(db_path)) as store:
                items = [{"id": i} for i in range(100)]
                store.insert_items(uuid4(), items)

            reader = duckdb.connect(str(db_path), read_only=True)
            try:
                result = reader.execute(
                    f"""
                    SELECT COUNT(DISTINCT ingested_at)
                    FROM {RAW_HN_ITEMS_TABLE}
                    """
                ).fetchone()

                assert result is not None
                assert result[0] == 1
            finally:
                reader.close()


class TestPayloadFidelity:
    """Test suite for payload byte-for-byte fidelity verification."""

    def test_simple_payload_roundtrip(self) -> None:
        """Verify simple JSON payload is stored and retrieved intact."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "simple_fidelity_test.duckdb"

            original_item = {
                "id": 8863,
                "type": "story",
                "by": "dhouston",
                "title": "My YC app: Dropbox",
                "score": 111,
                "time": 1175714200,
                "descendants": 71,
            }

            with DuckDBStore(database_path=str(db_path)) as store:
                store.insert_items(uuid4(), [original_item])

            reader = duckdb.connect(str(db_path), read_only=True)
            try:
                result = reader.execute(
                    f"SELECT payload FROM {RAW_HN_ITEMS_TABLE}"
                ).fetchone()

                assert result is not None
                retrieved_payload = json.loads(str(result[0]))

                assert retrieved_payload == original_item
            finally:
                reader.close()

    def test_complex_nested_payload_roundtrip(self) -> None:
        """Verify complex nested JSON payload is stored and retrieved intact."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "nested_fidelity_test.duckdb"

            original_item = {
                "id": 123,
                "type": "story",
                "metadata": {
                    "source": "hn_api",
                    "fetch_config": {
                        "timeout": 30,
                        "retries": 3,
                    },
                },
                "tags": ["tech", "startup", "yc"],
                "stats": {
                    "views": 1000,
                    "shares": [
                        {"platform": "twitter", "count": 50},
                        {"platform": "linkedin", "count": 25},
                    ],
                },
            }

            with DuckDBStore(database_path=str(db_path)) as store:
                store.insert_items(uuid4(), [original_item])

            reader = duckdb.connect(str(db_path), read_only=True)
            try:
                result = reader.execute(
                    f"SELECT payload FROM {RAW_HN_ITEMS_TABLE}"
                ).fetchone()

                assert result is not None
                retrieved_payload = json.loads(str(result[0]))

                assert retrieved_payload == original_item
            finally:
                reader.close()

    def test_unicode_payload_fidelity(self) -> None:
        """Verify Unicode characters are preserved in payload roundtrip."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "unicode_fidelity_test.duckdb"

            original_item = {
                "id": 123,
                "title": "Hello 世界 🚀 Привет мир",
                "text": "日本語テキスト with émojis 🎉🎊",
            }

            with DuckDBStore(database_path=str(db_path)) as store:
                store.insert_items(uuid4(), [original_item])

            reader = duckdb.connect(str(db_path), read_only=True)
            try:
                result = reader.execute(
                    f"SELECT payload FROM {RAW_HN_ITEMS_TABLE}"
                ).fetchone()

                assert result is not None
                retrieved_payload = json.loads(str(result[0]))

                assert retrieved_payload == original_item
                assert retrieved_payload["title"] == "Hello 世界 🚀 Привет мир"
            finally:
                reader.close()

    def test_null_values_preserved(self) -> None:
        """Verify null values within JSON are preserved."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "null_fidelity_test.duckdb"

            original_item = {
                "id": 123,
                "type": "story",
                "url": None,
                "text": None,
                "parent": None,
            }

            with DuckDBStore(database_path=str(db_path)) as store:
                store.insert_items(uuid4(), [original_item])

            reader = duckdb.connect(str(db_path), read_only=True)
            try:
                result = reader.execute(
                    f"SELECT payload FROM {RAW_HN_ITEMS_TABLE}"
                ).fetchone()

                assert result is not None
                retrieved_payload = json.loads(str(result[0]))

                assert retrieved_payload == original_item
                assert retrieved_payload["url"] is None
                assert retrieved_payload["text"] is None
            finally:
                reader.close()

    def test_numeric_precision_preserved(self) -> None:
        """Verify numeric values maintain precision in roundtrip."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "numeric_fidelity_test.duckdb"

            original_item = {
                "id": 123,
                "score": 999999,
                "time": 1700000000,
                "float_val": 3.14159265359,
                "large_int": 9007199254740991,
            }

            with DuckDBStore(database_path=str(db_path)) as store:
                store.insert_items(uuid4(), [original_item])

            reader = duckdb.connect(str(db_path), read_only=True)
            try:
                result = reader.execute(
                    f"SELECT payload FROM {RAW_HN_ITEMS_TABLE}"
                ).fetchone()

                assert result is not None
                retrieved_payload = json.loads(str(result[0]))

                assert retrieved_payload["score"] == 999999
                assert retrieved_payload["time"] == 1700000000
                assert retrieved_payload["large_int"] == 9007199254740991
            finally:
                reader.close()

    def test_multiple_items_fidelity(self) -> None:
        """Verify fidelity is maintained across multiple items in batch."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "multi_fidelity_test.duckdb"

            original_items = [
                {"id": 1, "type": "story", "title": "First"},
                {"id": 2, "type": "comment", "parent": 1},
                {"id": 3, "type": "job", "url": "https://example.com"},
            ]

            with DuckDBStore(database_path=str(db_path)) as store:
                store.insert_items(uuid4(), original_items)

            reader = duckdb.connect(str(db_path), read_only=True)
            try:
                result = reader.execute(
                    f"""
                    SELECT payload
                    FROM {RAW_HN_ITEMS_TABLE}
                    ORDER BY CAST(payload->>'id' AS INTEGER)
                    """
                ).fetchall()

                assert len(result) == 3

                for index, row in enumerate(result):
                    retrieved_payload = json.loads(str(row[0]))
                    assert retrieved_payload == original_items[index]
            finally:
                reader.close()
