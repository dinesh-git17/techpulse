"""Dagster schedule and job definitions for TechPulse ingestion pipeline.

This module defines the scheduling configuration for the Who is Hiring
data pipeline, including monthly schedules and backfill job configuration.
"""

from dagster import (
    AssetSelection,
    build_schedule_from_partitioned_job,
    define_asset_job,
)

from techpulse.data.assets import raw_hn_items, who_is_hiring_thread_id

BACKFILL_MAX_CONCURRENT_PARTITIONS = 5

SCHEDULE_CRON = "0 0 2 * *"

who_is_hiring_assets = AssetSelection.assets(
    who_is_hiring_thread_id,
    raw_hn_items,
)

who_is_hiring_ingestion_job = define_asset_job(
    name="who_is_hiring_ingestion_job",
    selection=who_is_hiring_assets,
    description="Ingest Who is Hiring thread and comments for a partition month.",
    tags={
        "dagster/max_runtime": 3600,
        "dagster/priority": "1",
    },
)

who_is_hiring_monthly_schedule = build_schedule_from_partitioned_job(
    job=who_is_hiring_ingestion_job,
    description="Run Who is Hiring ingestion on the 2nd of every month at 00:00 UTC.",
    hour_of_day=0,
    minute_of_hour=0,
    day_of_month=2,
)

who_is_hiring_backfill_job = define_asset_job(
    name="who_is_hiring_backfill_job",
    selection=who_is_hiring_assets,
    description="Backfill job for Who is Hiring data with concurrency controls.",
    tags={
        "dagster/max_runtime": 7200,
        "dagster/concurrency_key": "hn_api",
        "dagster/max_concurrent_backfill_partitions": str(
            BACKFILL_MAX_CONCURRENT_PARTITIONS
        ),
    },
)
