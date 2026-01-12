"""Dagster resource definitions for TechPulse data pipelines.

This module provides ConfigurableResource wrappers for the HackerNewsClient
and DuckDBStore classes, enabling dependency injection and testability
within Dagster assets.
"""

from contextlib import contextmanager
from typing import Generator, Optional

from dagster import ConfigurableResource

from techpulse.source.hn.client import (
    DEFAULT_BASE_URL,
    DEFAULT_CONNECT_TIMEOUT,
    DEFAULT_READ_TIMEOUT,
    HackerNewsClient,
)
from techpulse.storage.store import DuckDBStore


class HackerNewsClientResource(ConfigurableResource):  # type: ignore[type-arg]
    """Dagster resource wrapping the HackerNewsClient for dependency injection.

    This resource enables Dagster assets to receive a configured HackerNewsClient
    instance through Dagster's resource injection mechanism. The underlying client
    must be used as a context manager via the get_client() method.

    Attributes:
        base_url: Base URL for the HN API. Defaults to official Firebase endpoint.
        connect_timeout: Connection timeout in seconds.
        read_timeout: Read timeout in seconds.

    Example:
        >>> @asset
        ... def my_asset(hn_client: HackerNewsClientResource):
        ...     with hn_client.get_client() as client:
        ...         item = client.get_item(8863)
    """

    base_url: str = DEFAULT_BASE_URL
    connect_timeout: float = DEFAULT_CONNECT_TIMEOUT
    read_timeout: float = DEFAULT_READ_TIMEOUT

    @contextmanager
    def get_client(self) -> Generator[HackerNewsClient, None, None]:
        """Yield a configured HackerNewsClient instance.

        The client is automatically closed when the context manager exits.
        This method must be used within a with statement.

        Yields:
            HackerNewsClient: A configured and connected client instance.

        Example:
            >>> with resource.get_client() as client:
            ...     user = client.get_user("whoishiring")
        """
        with HackerNewsClient(
            base_url=self.base_url,
            connect_timeout=self.connect_timeout,
            read_timeout=self.read_timeout,
        ) as client:
            yield client


class DuckDBStoreResource(ConfigurableResource):  # type: ignore[type-arg]
    """Dagster resource wrapping the DuckDBStore for dependency injection.

    This resource enables Dagster assets to receive a configured DuckDBStore
    instance through Dagster's resource injection mechanism. The underlying store
    must be used as a context manager via the get_store() method.

    Attributes:
        database_path: Optional explicit path to the database file.
                      If None, uses environment variable or default path.

    Example:
        >>> @asset
        ... def my_asset(duckdb: DuckDBStoreResource):
        ...     with duckdb.get_store() as store:
        ...         count = store.insert_items(load_id, items)
    """

    database_path: Optional[str] = None

    @contextmanager
    def get_store(self) -> Generator[DuckDBStore, None, None]:
        """Yield a configured DuckDBStore instance.

        The store connection is automatically closed when the context manager exits.
        This method must be used within a with statement.

        Yields:
            DuckDBStore: A configured and connected store instance.

        Example:
            >>> with resource.get_store() as store:
            ...     store.insert_items(uuid4(), items)
        """
        with DuckDBStore(database_path=self.database_path) as store:
            yield store
