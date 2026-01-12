# Orchestration and Ingestion

## Purpose

Define Dagster assets, schedules, and resources that orchestrate ingestion of
Hacker News Who is Hiring data into the Bronze storage layer.

## Module Structure

- `techpulse.data.assets` defines partitioned assets for ingestion.
- `techpulse.data.resources` provides Dagster resources for external clients.
- `techpulse.data.schedules` defines jobs and schedules.
- `techpulse.data.definitions` wires assets, jobs, schedules, and resources.

## Partitioning and Scheduling

### Partition Definition

- Monthly partitions with `start_date` of `2011-04-01` and timezone `UTC`.
- Partition keys are in `YYYY-MM-DD` format and represent a month.

### Jobs and Schedules

- `who_is_hiring_ingestion_job`
  - Asset selection: `who_is_hiring_thread_id`, `raw_hn_items`.
  - Tags: `dagster/max_runtime` 3600, `dagster/priority` "1".
- `who_is_hiring_monthly_schedule`
  - Runs on the 2nd of every month at 00:00 UTC.
  - Built from the partitioned job.
- `who_is_hiring_backfill_job`
  - Same asset selection.
  - Tags include `dagster/concurrency_key` "hn_api" and
    `dagster/max_concurrent_backfill_partitions` "5".

## Dagster Resources

### `HackerNewsClientResource`

- Wraps `HackerNewsClient` for dependency injection into assets.
- Exposes `get_client()` context manager.
- Configurable fields:
  - `base_url` (default `https://hacker-news.firebaseio.com/v0`)
  - `connect_timeout` (default 10.0 seconds)
  - `read_timeout` (default 30.0 seconds)

### `DuckDBStoreResource`

- Wraps `DuckDBStore` for dependency injection into assets.
- Exposes `get_store()` context manager.
- Configurable field:
  - `database_path` (optional path to DuckDB file)

## Assets

### `who_is_hiring_thread_id`

Find the Hacker News thread ID for the Who is Hiring post for a given partition
month.

#### Key Logic

- Parses partition key to year and month.
- Rejects future partitions by raising `dagster.Failure` with
  `allow_retries=False`.
- Uses `HackerNewsClient.get_user("whoishiring")` to list submissions.
- Scans submissions for a story title matching a month and year via regex:
  `"Who is hiring? (Month YYYY)"` with optional "Ask HN:" prefix and variants.
- Returns the matching item ID.

#### Data Contract

- Input: partition key from Dagster context.
- Output: `int` thread ID.
- Failure states:
  - Future partition. Failure metadata includes `skipped=True` and reason.
  - Thread not found. Failure metadata includes `skipped=True` and reason.

#### Error Handling

- Missing user or item data results in a skipped `Failure` without retries.
- Network or API errors from `HackerNewsClient` propagate.

### `raw_hn_items`

Ingest all items in the thread comment tree into DuckDB.

#### Key Logic

- Skips execution if upstream `who_is_hiring_thread_id` is `None` by raising
  `dagster.Failure` with `allow_retries=False`.
- Generates a `load_id` UUID for the ingestion batch.
- Performs breadth-first traversal of the thread comment tree.
- Fetches each item via `HackerNewsClient.get_item`.
- Inserts records in batches of 100 using `DuckDBStore.insert_items`.
- Creates tombstone records for deleted or inaccessible items.

#### Data Contract

- Input: `who_is_hiring_thread_id` from upstream asset.
- Output: none. Side effect is persisted rows in DuckDB.
- Output metadata includes item count, tombstone count, load ID, duration.

#### Tombstone Record Shape

Tombstones are dictionaries with null content fields and flags:

- `deleted`: `True`
- `dead`: `False`
- `is_tombstone`: `True`

All other fields are present with `None` or empty list values.

#### Error Handling

- Upstream missing thread ID causes a skipped `Failure` with metadata.
- Client and storage exceptions propagate and can trigger Dagster retries
  per the asset retry policy.

## Orchestration Definitions

`techpulse.data.definitions` builds a Dagster `Definitions` object that
registers:

- Assets: `who_is_hiring_thread_id`, `raw_hn_items`.
- Jobs: `who_is_hiring_ingestion_job`, `who_is_hiring_backfill_job`.
- Schedule: `who_is_hiring_monthly_schedule`.
- Resources: `hn_client`, `duckdb`.
