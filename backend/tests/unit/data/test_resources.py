"""Unit tests for Dagster resource definitions.

This module tests the HackerNewsClientResource and DuckDBStoreResource
classes, demonstrating mock injection patterns for asset testing.
"""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch
from uuid import uuid4

from dagster import Definitions

from techpulse.data.resources import DuckDBStoreResource, HackerNewsClientResource
from techpulse.source.hn.client import (
    DEFAULT_BASE_URL,
    DEFAULT_CONNECT_TIMEOUT,
    DEFAULT_READ_TIMEOUT,
    HackerNewsClient,
)
from techpulse.source.hn.models import HNItem, HNItemType, HNUser
from techpulse.storage.store import DuckDBStore


class TestHackerNewsClientResourceConfiguration:
    """Test suite for HackerNewsClientResource configuration."""

    def test_default_configuration(self) -> None:
        """Verify resource uses default values when not specified."""
        resource = HackerNewsClientResource()

        assert resource.base_url == DEFAULT_BASE_URL
        assert resource.connect_timeout == DEFAULT_CONNECT_TIMEOUT
        assert resource.read_timeout == DEFAULT_READ_TIMEOUT

    def test_custom_base_url(self) -> None:
        """Verify resource accepts custom base_url."""
        custom_url = "https://custom-api.example.com/v1"
        resource = HackerNewsClientResource(base_url=custom_url)

        assert resource.base_url == custom_url

    def test_custom_timeouts(self) -> None:
        """Verify resource accepts custom timeout values."""
        resource = HackerNewsClientResource(
            connect_timeout=5.0,
            read_timeout=60.0,
        )

        assert resource.connect_timeout == 5.0
        assert resource.read_timeout == 60.0

    def test_full_custom_configuration(self) -> None:
        """Verify resource accepts all custom configuration values."""
        resource = HackerNewsClientResource(
            base_url="https://test.example.com",
            connect_timeout=15.0,
            read_timeout=45.0,
        )

        assert resource.base_url == "https://test.example.com"
        assert resource.connect_timeout == 15.0
        assert resource.read_timeout == 45.0


class TestHackerNewsClientResourceContextManager:
    """Test suite for HackerNewsClientResource context manager behavior."""

    def test_get_client_returns_context_manager(self) -> None:
        """Verify get_client returns a context manager."""
        resource = HackerNewsClientResource()

        with patch.object(HackerNewsClient, "__enter__") as mock_enter:
            with patch.object(HackerNewsClient, "__exit__") as mock_exit:
                mock_client = MagicMock(spec=HackerNewsClient)
                mock_enter.return_value = mock_client
                mock_exit.return_value = None

                with resource.get_client() as client:
                    assert client is not None

                mock_enter.assert_called_once()
                mock_exit.assert_called_once()

    def test_get_client_passes_configuration(self) -> None:
        """Verify get_client passes configuration to underlying client."""
        custom_url = "https://custom.example.com"
        resource = HackerNewsClientResource(
            base_url=custom_url,
            connect_timeout=20.0,
            read_timeout=40.0,
        )

        with patch("techpulse.data.resources.HackerNewsClient") as mock_client_class:
            mock_instance = MagicMock()
            mock_client_class.return_value.__enter__ = MagicMock(
                return_value=mock_instance
            )
            mock_client_class.return_value.__exit__ = MagicMock(return_value=None)

            with resource.get_client():
                pass

            mock_client_class.assert_called_once_with(
                base_url=custom_url,
                connect_timeout=20.0,
                read_timeout=40.0,
            )


class TestDuckDBStoreResourceConfiguration:
    """Test suite for DuckDBStoreResource configuration."""

    def test_default_configuration(self) -> None:
        """Verify resource uses None as default database_path."""
        resource = DuckDBStoreResource()

        assert resource.database_path is None

    def test_custom_database_path(self) -> None:
        """Verify resource accepts custom database_path."""
        custom_path = "/tmp/test.duckdb"
        resource = DuckDBStoreResource(database_path=custom_path)

        assert resource.database_path == custom_path


class TestDuckDBStoreResourceContextManager:
    """Test suite for DuckDBStoreResource context manager behavior."""

    def test_get_store_returns_context_manager(self) -> None:
        """Verify get_store returns a context manager."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = str(Path(temp_dir) / "test.duckdb")
            resource = DuckDBStoreResource(database_path=db_path)

            with resource.get_store() as store:
                assert store is not None
                assert isinstance(store, DuckDBStore)

    def test_get_store_passes_database_path(self) -> None:
        """Verify get_store passes database_path to underlying store."""
        custom_path = "/tmp/custom_test.duckdb"
        resource = DuckDBStoreResource(database_path=custom_path)

        with patch("techpulse.data.resources.DuckDBStore") as mock_store_class:
            mock_instance = MagicMock()
            mock_store_class.return_value.__enter__ = MagicMock(
                return_value=mock_instance
            )
            mock_store_class.return_value.__exit__ = MagicMock(return_value=None)

            with resource.get_store():
                pass

            mock_store_class.assert_called_once_with(database_path=custom_path)

    def test_get_store_with_none_path(self) -> None:
        """Verify get_store handles None database_path correctly."""
        resource = DuckDBStoreResource(database_path=None)

        with patch("techpulse.data.resources.DuckDBStore") as mock_store_class:
            mock_instance = MagicMock()
            mock_store_class.return_value.__enter__ = MagicMock(
                return_value=mock_instance
            )
            mock_store_class.return_value.__exit__ = MagicMock(return_value=None)

            with resource.get_store():
                pass

            mock_store_class.assert_called_once_with(database_path=None)


class TestMockInjectionPattern:
    """Test suite demonstrating mock injection for Dagster assets.

    These tests demonstrate how to inject mock dependencies when testing
    asset logic without actual API calls or database connections.

    The pattern shown here uses patch to replace the underlying client/store
    classes, allowing the real resource wrappers to be used while mocking
    the actual I/O operations.
    """

    def test_mock_hn_client_via_patch(self) -> None:
        """Demonstrate mocking HackerNewsClient via patch for asset testing."""
        mock_user = HNUser(
            id="whoishiring",
            created=1234567890,
            karma=500,
            about=None,
            submitted=[1, 2, 3],
        )

        with patch("techpulse.data.resources.HackerNewsClient") as mock_client_class:
            mock_client = MagicMock(spec=HackerNewsClient)
            mock_client.get_user.return_value = mock_user
            mock_client_class.return_value.__enter__ = MagicMock(
                return_value=mock_client
            )
            mock_client_class.return_value.__exit__ = MagicMock(return_value=None)

            resource = HackerNewsClientResource()

            with resource.get_client() as client:
                user = client.get_user("whoishiring")

            assert user is not None
            assert user.karma == 500
            mock_client.get_user.assert_called_once_with("whoishiring")

    def test_mock_duckdb_store_via_patch(self) -> None:
        """Demonstrate mocking DuckDBStore via patch for asset testing."""
        with patch("techpulse.data.resources.DuckDBStore") as mock_store_class:
            mock_store = MagicMock(spec=DuckDBStore)
            mock_store.insert_items.return_value = 2
            mock_store_class.return_value.__enter__ = MagicMock(return_value=mock_store)
            mock_store_class.return_value.__exit__ = MagicMock(return_value=None)

            resource = DuckDBStoreResource()
            load_id = uuid4()
            items = [{"id": 1, "type": "story"}, {"id": 2, "type": "comment"}]

            with resource.get_store() as store:
                count = store.insert_items(load_id, items)

            assert count == 2
            mock_store.insert_items.assert_called_once()

    def test_mock_both_resources_via_patch(self) -> None:
        """Demonstrate mocking both resources via patch for complex asset logic."""
        mock_item = HNItem(
            id=8863,
            type=HNItemType.STORY,
            by="dhouston",
            time=1175714200,
            url="http://www.getdropbox.com/u/2/screencast.html",
            score=111,
            title="My YC app: Dropbox",
            descendants=71,
        )

        with patch("techpulse.data.resources.HackerNewsClient") as mock_client_class:
            with patch("techpulse.data.resources.DuckDBStore") as mock_store_class:
                mock_client = MagicMock(spec=HackerNewsClient)
                mock_client.get_item.return_value = mock_item
                mock_client_class.return_value.__enter__ = MagicMock(
                    return_value=mock_client
                )
                mock_client_class.return_value.__exit__ = MagicMock(return_value=None)

                mock_store = MagicMock(spec=DuckDBStore)
                mock_store.insert_items.return_value = 1
                mock_store_class.return_value.__enter__ = MagicMock(
                    return_value=mock_store
                )
                mock_store_class.return_value.__exit__ = MagicMock(return_value=None)

                hn_resource = HackerNewsClientResource()
                db_resource = DuckDBStoreResource()

                with hn_resource.get_client() as client:
                    item = client.get_item(8863)

                assert item is not None

                item_data = {
                    "id": item.id,
                    "type": item.type.value,
                    "title": item.title,
                }

                with db_resource.get_store() as store:
                    count = store.insert_items(uuid4(), [item_data])

                assert count == 1
                mock_client.get_item.assert_called_once_with(8863)
                mock_store.insert_items.assert_called_once()

    def test_asset_function_with_mock_resources(self) -> None:
        """Demonstrate testing asset function logic with mock resources.

        This pattern tests the asset function directly by creating resources
        with patched underlying implementations.
        """

        def fetch_user_karma_logic(hn_client: HackerNewsClientResource) -> int:
            """Asset logic: fetch karma for whoishiring user."""
            with hn_client.get_client() as client:
                user = client.get_user("whoishiring")
                if user is None:
                    return 0
                return user.karma

        mock_user = HNUser(
            id="whoishiring",
            created=1234567890,
            karma=750,
            about=None,
            submitted=[],
        )

        with patch("techpulse.data.resources.HackerNewsClient") as mock_client_class:
            mock_client = MagicMock(spec=HackerNewsClient)
            mock_client.get_user.return_value = mock_user
            mock_client_class.return_value.__enter__ = MagicMock(
                return_value=mock_client
            )
            mock_client_class.return_value.__exit__ = MagicMock(return_value=None)

            resource = HackerNewsClientResource()
            result = fetch_user_karma_logic(resource)

            assert result == 750

    def test_asset_function_handles_none_response(self) -> None:
        """Verify asset logic handles None responses correctly."""

        def fetch_user_karma_logic(hn_client: HackerNewsClientResource) -> int:
            """Asset logic: fetch karma for whoishiring user."""
            with hn_client.get_client() as client:
                user = client.get_user("nonexistent")
                if user is None:
                    return 0
                return user.karma

        with patch("techpulse.data.resources.HackerNewsClient") as mock_client_class:
            mock_client = MagicMock(spec=HackerNewsClient)
            mock_client.get_user.return_value = None
            mock_client_class.return_value.__enter__ = MagicMock(
                return_value=mock_client
            )
            mock_client_class.return_value.__exit__ = MagicMock(return_value=None)

            resource = HackerNewsClientResource()
            result = fetch_user_karma_logic(resource)

            assert result == 0


class TestResourceIntegrationWithDefinitions:
    """Test suite for resource integration with Dagster Definitions."""

    def test_definitions_with_resources(self) -> None:
        """Verify Definitions object correctly binds resources."""
        hn_resource = HackerNewsClientResource()
        db_resource = DuckDBStoreResource()

        defs = Definitions(
            assets=[],
            resources={
                "hn_client": hn_resource,
                "duckdb": db_resource,
            },
        )

        repository = defs.get_repository_def()
        assert repository is not None

    def test_definitions_with_configured_resources(self) -> None:
        """Verify Definitions accepts configured resources."""
        hn_resource = HackerNewsClientResource(
            base_url="https://test.example.com",
            connect_timeout=5.0,
        )
        db_resource = DuckDBStoreResource(database_path="/tmp/test.duckdb")

        defs = Definitions(
            assets=[],
            resources={
                "hn_client": hn_resource,
                "duckdb": db_resource,
            },
        )

        repository = defs.get_repository_def()
        assert repository is not None


class TestRealResourceUsage:
    """Test suite for real resource usage (non-mocked) with isolated environment."""

    def test_duckdb_store_resource_real_usage(self) -> None:
        """Verify DuckDBStoreResource works with actual DuckDB instance."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = str(Path(temp_dir) / "test.duckdb")
            resource = DuckDBStoreResource(database_path=db_path)

            with resource.get_store() as store:
                load_id = uuid4()
                items = [{"id": 123, "type": "story", "title": "Test"}]

                count = store.insert_items(load_id, items)

                assert count == 1
                assert store.get_item_count() == 1

    def test_duckdb_store_resource_multiple_batches(self) -> None:
        """Verify resource supports multiple batch operations."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = str(Path(temp_dir) / "test.duckdb")
            resource = DuckDBStoreResource(database_path=db_path)

            with resource.get_store() as store:
                store.insert_items(uuid4(), [{"id": 1}])
                store.insert_items(uuid4(), [{"id": 2}, {"id": 3}])

                assert store.get_item_count() == 3
