# Backend Overview

## Scope

The backend is a Python service focused on ingesting Hacker News data and
persisting it in a DuckDB Bronze layer. The only HTTP surface is a FastAPI
health endpoint. Orchestration is implemented with Dagster assets, schedules,
and resources.

## Module Structure

- `techpulse/api` provides the FastAPI application entry point.
- `techpulse/data` defines Dagster assets, schedules, and resources for ingestion.
- `techpulse/source/hn` implements the Hacker News API client and data models.
- `techpulse/storage` implements DuckDB connection management and persistence.
- `backend/dbt_project` defines dbt configuration for DuckDB analytics.

## Responsibility Boundaries

### API

Provides a health endpoint only. It does not orchestrate ingestion or expose
backend data.

### Data Orchestration

Owns ingestion flow definitions, scheduling, and Dagster resource wiring. It
coordinates Hacker News data extraction and persistence through the storage
layer.

### Source Connector

Implements a synchronous Hacker News client with retry and validation. It is the
only external integration point used by ingestion.

### Storage

Owns DuckDB database lifecycle, schema initialization, and batch inserts into
the Bronze layer.

### Analytics Configuration

Provides dbt configuration files for DuckDB, without runtime integration in the
Python codebase.

## High-Level Data Flow

1. Dagster executes the monthly `who_is_hiring_thread_id` asset to locate the
   Who is Hiring thread ID for the partition month.
2. Dagster executes the `raw_hn_items` asset to traverse the thread comment tree
   and ingest all items into DuckDB in batch transactions.
3. The DuckDB store writes raw JSON payloads into the `raw_hn_items` table,
   annotating each row with `load_id` and `ingested_at`.

## External Integration Points

- Hacker News Firebase API via `HackerNewsClient`.
- DuckDB file storage at a configurable filesystem path.
- Dagster for orchestration and scheduling.
- dbt for analytics configuration against the DuckDB file.
