# pylint: disable=import-error
"""Dagster asset definitions for TechPulse data pipelines."""

from dagster import Definitions

from techpulse.data.assets import who_is_hiring_thread_id
from techpulse.data.resources import DuckDBStoreResource, HackerNewsClientResource

defs = Definitions(
    assets=[who_is_hiring_thread_id],
    resources={
        "hn_client": HackerNewsClientResource(),
        "duckdb": DuckDBStoreResource(),
    },
)
