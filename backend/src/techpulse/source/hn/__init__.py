"""Hacker News API client for TechPulse data ingestion.

This module provides a production-grade client for interacting with the
Hacker News Firebase API. It exports the client class, data models, and
exception types needed for robust HN data extraction.

Example:
    >>> from techpulse.source.hn import HackerNewsClient, HNItemType
    >>> with HackerNewsClient() as client:
    ...     item = client.get_item(8863)
    ...     if item and item.type == HNItemType.STORY:
    ...         print(item.title)
"""

from techpulse.source.hn.client import HackerNewsClient
from techpulse.source.hn.errors import (
    HackerNewsAPIError,
    HackerNewsDataError,
    HackerNewsError,
    HackerNewsMaxRetriesError,
    HackerNewsNetworkError,
)
from techpulse.source.hn.models import HNItem, HNItemType, HNUser

__all__ = [
    "HackerNewsClient",
    "HackerNewsError",
    "HackerNewsNetworkError",
    "HackerNewsAPIError",
    "HackerNewsDataError",
    "HackerNewsMaxRetriesError",
    "HNItem",
    "HNItemType",
    "HNUser",
]
