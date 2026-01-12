"""Dagster asset definitions for TechPulse ingestion pipeline.

This module defines the partitioned assets for the Who is Hiring data pipeline.
Assets use monthly partitioning to enable historical backfills and incremental
updates.
"""

import re
from datetime import datetime, timezone
from typing import Optional

import structlog
from dagster import (
    AssetExecutionContext,
    MonthlyPartitionsDefinition,
    asset,
)

from techpulse.data.resources import HackerNewsClientResource
from techpulse.source.hn.client import HackerNewsClient
from techpulse.source.hn.models import HNItemType

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

    if thread_id is None:
        skip_message = (
            f"Could not find Who is Hiring thread for "
            f"{MONTH_NAMES[target_month - 1]} {target_year}."
        )
        log.warning("thread_not_found_skip", reason=skip_message)
        context.log.warning(skip_message)
        return None

    log.info(
        "asset_execution_complete",
        thread_id=thread_id,
        target_year=target_year,
        target_month=target_month,
    )

    context.add_output_metadata(
        metadata={
            "thread_id": thread_id,
            "target_year": target_year,
            "target_month": target_month,
            "target_month_name": MONTH_NAMES[target_month - 1],
            "partition_key": partition_key,
        }
    )

    return thread_id
