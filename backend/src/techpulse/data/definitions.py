# pylint: disable=import-error
"""Dagster asset definitions for TechPulse data pipelines."""

from dagster import Definitions

from techpulse.data.assets import raw_hn_items, who_is_hiring_thread_id
from techpulse.data.resources import DuckDBStoreResource, HackerNewsClientResource
from techpulse.data.schedules import (
    who_is_hiring_backfill_job,
    who_is_hiring_ingestion_job,
    who_is_hiring_monthly_schedule,
)

defs = Definitions(
    assets=[who_is_hiring_thread_id, raw_hn_items],
    jobs=[who_is_hiring_ingestion_job, who_is_hiring_backfill_job],
    schedules=[who_is_hiring_monthly_schedule],
    resources={
        "hn_client": HackerNewsClientResource(),
        "duckdb": DuckDBStoreResource(),
    },
)
