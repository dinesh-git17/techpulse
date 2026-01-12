"""DuckDB storage layer for TechPulse Bronze data persistence.

This module provides the storage infrastructure for persisting raw Hacker News
data into the Bronze layer using DuckDB. It exports the store and manager classes,
schema constants, and exception types needed for robust database operations.

Example:
    >>> from uuid import uuid4
    >>> from techpulse.storage import DuckDBStore, StorageConnectionError
    >>> try:
    ...     with DuckDBStore() as store:
    ...         items = [{"id": 123, "type": "story"}]
    ...         count = store.insert_items(uuid4(), items)
    ... except StorageConnectionError as err:
    ...     print(f"Connection failed: {err.reason}")
"""

from techpulse.storage.exceptions import (
    InvalidPayloadError,
    StorageConnectionError,
    StorageError,
    TransactionError,
)
from techpulse.storage.manager import DuckDBManager
from techpulse.storage.schema import RAW_HN_ITEMS_TABLE
from techpulse.storage.store import DuckDBStore

__all__ = [
    "DuckDBStore",
    "DuckDBManager",
    "RAW_HN_ITEMS_TABLE",
    "StorageError",
    "StorageConnectionError",
    "InvalidPayloadError",
    "TransactionError",
]
