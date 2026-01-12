"""Dagster asset definitions for TechPulse ingestion pipeline.

This module defines the partitioned assets for the Who is Hiring data pipeline.
Assets use monthly partitioning to enable historical backfills and incremental
updates.
"""

import re
from collections import deque
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID, uuid4

import structlog
from dagster import (
    AssetExecutionContext,
    AssetIn,
    Backoff,
    MonthlyPartitionsDefinition,
    RetryPolicy,
    asset,
)

from techpulse.data.resources import DuckDBStoreResource, HackerNewsClientResource
from techpulse.source.hn.client import HackerNewsClient
from techpulse.source.hn.models import HNItem, HNItemType
from techpulse.storage.store import DuckDBStore

logger = structlog.get_logger(__name__)

WHOISHIRING_USERNAME = "whoishiring"

PARTITION_START_DATE = "2011-04-01"

MONTH_NAMES = [
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
]

WHO_IS_HIRING_PATTERN = re.compile(
    r"(?:Ask\s+HN:\s+)?Who(?:'s|\s+is)\s+hiring\??\s*\((\w+)\s+(\d{4})\)",
    re.IGNORECASE,
)

BATCH_SIZE = 100

RETRY_MAX_ATTEMPTS = 3
RETRY_DELAY_SECONDS = 300

ingestion_retry_policy = RetryPolicy(
    max_retries=RETRY_MAX_ATTEMPTS,
    delay=RETRY_DELAY_SECONDS,
    backoff=Backoff.LINEAR,
)

who_is_hiring_partitions = MonthlyPartitionsDefinition(
    start_date=PARTITION_START_DATE,
    timezone="UTC",
)


def _parse_partition_key(partition_key: str) -> tuple[int, int]:
    """Parse a partition key into year and month components.

    Args:
        partition_key: The partition key in YYYY-MM-DD format.

    Returns:
        tuple[int, int]: A tuple of (year, month).

    Raises:
        ValueError: If the partition key format is invalid.
    """
    partition_date = datetime.strptime(partition_key, "%Y-%m-%d")
    return partition_date.year, partition_date.month


def _month_name_to_number(month_name: str) -> Optional[int]:
    """Convert a month name to its numeric value.

    Args:
        month_name: The month name (e.g., "January", "February").

    Returns:
        Optional[int]: The month number (1-12), or None if not recognized.
    """
    month_name_normalized = month_name.strip().title()
    if month_name_normalized in MONTH_NAMES:
        return MONTH_NAMES.index(month_name_normalized) + 1
    return None


def _extract_month_year_from_title(title: str) -> Optional[tuple[int, int]]:
    """Extract month and year from a Who is Hiring thread title.

    Handles various title formats:
    - "Ask HN: Who is hiring? (November 2023)"
    - "Ask HN: Who's hiring? (November 2023)"
    - "Who is hiring? (November 2023)"

    Args:
        title: The thread title to parse.

    Returns:
        Optional[tuple[int, int]]: A tuple of (year, month) if matched, None otherwise.
    """
    match = WHO_IS_HIRING_PATTERN.search(title)
    if not match:
        return None

    month_name = match.group(1)
    year_str = match.group(2)

    month_number = _month_name_to_number(month_name)
    if month_number is None:
        return None

    try:
        year = int(year_str)
    except ValueError:
        return None

    return year, month_number


def _is_future_partition(target_year: int, target_month: int) -> bool:
    """Check if the target month is in the future.

    Args:
        target_year: The target year.
        target_month: The target month (1-12).

    Returns:
        bool: True if the partition is in the future.
    """
    now = datetime.now(timezone.utc)
    current_year = now.year
    current_month = now.month

    if target_year > current_year:
        return True
    if target_year == current_year and target_month > current_month:
        return True
    return False


def _find_thread_id_for_month(
    client: HackerNewsClient,
    target_year: int,
    target_month: int,
    log: structlog.stdlib.BoundLogger,
) -> Optional[int]:
    """Search the whoishiring user's submissions for the target month's thread.

    Args:
        client: The HackerNews API client.
        target_year: The year to search for.
        target_month: The month to search for (1-12).
        log: Bound logger for structured logging.

    Returns:
        Optional[int]: The thread ID if found, None otherwise.
    """
    user = client.get_user(WHOISHIRING_USERNAME)
    if user is None:
        log.error("whoishiring_user_not_found")
        return None

    log.info(
        "searching_user_submissions",
        username=WHOISHIRING_USERNAME,
        submission_count=len(user.submitted),
        target_year=target_year,
        target_month=target_month,
    )

    for item_id in user.submitted:
        item = client.get_item(item_id)
        if item is None:
            continue

        if item.type != HNItemType.STORY:
            continue

        if item.title is None:
            continue

        extracted = _extract_month_year_from_title(item.title)
        if extracted is None:
            continue

        extracted_year, extracted_month = extracted

        if extracted_year == target_year and extracted_month == target_month:
            log.info(
                "thread_found",
                item_id=item.id,
                title=item.title,
                target_year=target_year,
                target_month=target_month,
            )
            return item.id

    log.warning(
        "thread_not_found",
        target_year=target_year,
        target_month=target_month,
    )
    return None


@asset(
    partitions_def=who_is_hiring_partitions,
    retry_policy=ingestion_retry_policy,
    description="Find the HN thread ID for the Who is Hiring post for a given month.",
)
def who_is_hiring_thread_id(
    context: AssetExecutionContext,
    hn_client: HackerNewsClientResource,
) -> Optional[int]:
    """Find the Who is Hiring thread ID for the partition month.

    This asset queries the whoishiring user's submission history to locate
    the thread ID corresponding to the partition's month. It uses regex
    pattern matching to handle title variations across historical threads.

    Args:
        context: Dagster execution context providing partition information.
        hn_client: The HackerNews API client resource.

    Returns:
        Optional[int]: The thread ID if found, None if skipped.
    """
    partition_key = context.partition_key
    log = logger.bind(
        asset="who_is_hiring_thread_id",
        partition_key=partition_key,
    )

    log.info("asset_execution_start", partition_key=partition_key)

    start_time = datetime.now(timezone.utc)

    target_year, target_month = _parse_partition_key(partition_key)

    if _is_future_partition(target_year, target_month):
        month_name = MONTH_NAMES[target_month - 1]
        skip_message = (
            f"Partition {partition_key} is in the future. "
            f"Thread for {month_name} {target_year} does not exist yet."
        )
        log.info("skipping_future_partition", reason=skip_message)
        context.log.info(skip_message)
        return None

    with hn_client.get_client() as client:
        thread_id = _find_thread_id_for_month(
            client=client,
            target_year=target_year,
            target_month=target_month,
            log=log,
        )

    end_time = datetime.now(timezone.utc)
    duration_seconds = (end_time - start_time).total_seconds()

    if thread_id is None:
        skip_message = (
            f"Could not find Who is Hiring thread for "
            f"{MONTH_NAMES[target_month - 1]} {target_year}."
        )
        log.warning("thread_not_found_skip", reason=skip_message)
        context.log.warning(skip_message)
        context.add_output_metadata(
            metadata={
                "duration_seconds": duration_seconds,
                "skipped": True,
                "skip_reason": "Thread not found",
            }
        )
        return None

    log.info(
        "asset_execution_complete",
        thread_id=thread_id,
        target_year=target_year,
        target_month=target_month,
        duration_seconds=duration_seconds,
    )

    context.add_output_metadata(
        metadata={
            "thread_id": thread_id,
            "target_year": target_year,
            "target_month": target_month,
            "target_month_name": MONTH_NAMES[target_month - 1],
            "partition_key": partition_key,
            "duration_seconds": duration_seconds,
        }
    )

    return thread_id


def _create_tombstone_record(item_id: int) -> dict[str, object]:
    """Create a tombstone record for a deleted or inaccessible item.

    Tombstone records preserve the item ID for lineage tracking while
    indicating that the actual content was unavailable at ingestion time.

    Args:
        item_id: The ID of the deleted or inaccessible item.

    Returns:
        dict[str, object]: A tombstone record with null content fields.
    """
    return {
        "id": item_id,
        "type": None,
        "by": None,
        "time": None,
        "text": None,
        "title": None,
        "url": None,
        "kids": [],
        "parent": None,
        "score": None,
        "descendants": None,
        "deleted": True,
        "dead": False,
        "is_tombstone": True,
    }


def _item_to_dict(item: HNItem) -> dict[str, object]:
    """Convert an HNItem to a dictionary for storage.

    Args:
        item: The HNItem to convert.

    Returns:
        dict[str, object]: Dictionary representation of the item.
    """
    return {
        "id": item.id,
        "type": item.type.value,
        "by": item.by,
        "time": item.time.isoformat() if item.time else None,
        "text": item.text,
        "title": item.title,
        "url": item.url,
        "kids": item.kids,
        "parent": item.parent,
        "score": item.score,
        "descendants": item.descendants,
        "deleted": item.deleted,
        "dead": item.dead,
        "is_tombstone": False,
    }


def _traverse_and_ingest_comments(
    client: HackerNewsClient,
    store: DuckDBStore,
    thread_id: int,
    load_id: UUID,
    log: structlog.stdlib.BoundLogger,
) -> tuple[int, int]:
    """Traverse the comment tree and ingest all items into DuckDB.

    Uses breadth-first traversal to walk the entire comment tree starting
    from the thread root. Items are batched and flushed to storage in
    groups of BATCH_SIZE to manage memory usage.

    Args:
        client: The HackerNews API client.
        store: The DuckDB storage instance.
        thread_id: The root thread ID to start traversal from.
        load_id: Unique identifier for this ingestion batch.
        log: Bound logger for structured logging.

    Returns:
        tuple[int, int]: A tuple of (total_item_count, tombstone_count).
    """
    item_queue: deque[int] = deque([thread_id])
    visited_ids: set[int] = set()
    batch_buffer: list[dict[str, object]] = []

    total_item_count = 0
    tombstone_count = 0
    total_saved_count = 0

    log.info(
        "traversal_start",
        thread_id=thread_id,
        load_id=str(load_id),
    )

    while item_queue:
        current_item_id = item_queue.popleft()

        if current_item_id in visited_ids:
            continue

        visited_ids.add(current_item_id)

        item = client.get_item(current_item_id)

        if item is None:
            tombstone_record = _create_tombstone_record(current_item_id)
            batch_buffer.append(tombstone_record)
            tombstone_count += 1
            total_item_count += 1

            log.debug(
                "tombstone_created",
                item_id=current_item_id,
                tombstone_count=tombstone_count,
            )
        else:
            item_record = _item_to_dict(item)
            batch_buffer.append(item_record)
            total_item_count += 1

            for child_id in item.kids:
                if child_id not in visited_ids:
                    item_queue.append(child_id)

        if len(batch_buffer) >= BATCH_SIZE:
            saved_count = store.insert_items(load_id, batch_buffer)
            total_saved_count += saved_count
            log.debug(
                "batch_flushed",
                batch_size=saved_count,
                total_saved=total_saved_count,
                queue_depth=len(item_queue),
            )
            batch_buffer = []

    if batch_buffer:
        saved_count = store.insert_items(load_id, batch_buffer)
        total_saved_count += saved_count
        log.debug(
            "final_batch_flushed",
            batch_size=saved_count,
            total_saved=total_saved_count,
        )

    log.info(
        "traversal_complete",
        total_item_count=total_item_count,
        tombstone_count=tombstone_count,
        total_saved=total_saved_count,
        visited_count=len(visited_ids),
    )

    return total_item_count, tombstone_count


@asset(
    partitions_def=who_is_hiring_partitions,
    ins={"who_is_hiring_thread_id": AssetIn(key="who_is_hiring_thread_id")},
    retry_policy=ingestion_retry_policy,
    description="Ingest all comments from a Who is Hiring thread.",
)
def raw_hn_items(
    context: AssetExecutionContext,
    hn_client: HackerNewsClientResource,
    duckdb: DuckDBStoreResource,
    who_is_hiring_thread_id: Optional[int],
) -> None:
    """Ingest all items from a Who is Hiring thread into DuckDB.

    This asset recursively traverses the comment tree for a given thread,
    fetching all comments and their nested replies. Items are batched and
    persisted to the Bronze layer. Deleted or inaccessible items are stored
    as tombstone records to preserve lineage.

    Args:
        context: Dagster execution context providing partition information.
        hn_client: The HackerNews API client resource.
        duckdb: The DuckDB storage resource.
        who_is_hiring_thread_id: The thread ID from upstream asset, or None if skipped.

    Returns:
        None: This asset has side effects (data written to DuckDB).
    """
    partition_key = context.partition_key
    log = logger.bind(
        asset="raw_hn_items",
        partition_key=partition_key,
    )

    log.info("asset_execution_start", partition_key=partition_key)

    if who_is_hiring_thread_id is None:
        skip_message = (
            f"Skipping partition {partition_key}: upstream thread ID is None."
        )
        log.info("skipping_no_thread_id", reason=skip_message)
        context.log.info(skip_message)
        context.add_output_metadata(
            metadata={
                "item_count": 0,
                "tombstone_count": 0,
                "skipped": True,
                "skip_reason": "No upstream thread ID",
            }
        )
        return

    load_id = uuid4()

    log.info(
        "ingestion_start",
        thread_id=who_is_hiring_thread_id,
        load_id=str(load_id),
    )

    start_time = datetime.now(timezone.utc)

    with hn_client.get_client() as client, duckdb.get_store() as store:
        item_count, tombstone_count = _traverse_and_ingest_comments(
            client=client,
            store=store,
            thread_id=who_is_hiring_thread_id,
            load_id=load_id,
            log=log,
        )

    end_time = datetime.now(timezone.utc)
    duration_seconds = (end_time - start_time).total_seconds()

    log.info(
        "asset_execution_complete",
        thread_id=who_is_hiring_thread_id,
        item_count=item_count,
        tombstone_count=tombstone_count,
        duration_seconds=duration_seconds,
        load_id=str(load_id),
    )

    context.add_output_metadata(
        metadata={
            "item_count": item_count,
            "tombstone_count": tombstone_count,
            "duration_seconds": duration_seconds,
            "thread_id": who_is_hiring_thread_id,
            "load_id": str(load_id),
            "partition_key": partition_key,
        }
    )
