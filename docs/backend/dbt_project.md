# dbt Project Configuration

## Purpose

Define dbt configuration for interacting with the DuckDB database produced by
ingestion. These files are configuration only and are not referenced by the
Python backend runtime.

## `dbt_project.yml`

- Project name: `dbt_project`
- Version: `1.0.0`
- Profile: `techpulse`
- Paths:
  - models: `models`
  - seeds: `seeds`
  - tests: `tests`
  - snapshots: `snapshots`
- Clean targets: `target`, `dbt_packages`

## `profiles.yml`

Defines a single target profile `techpulse` with a `dev` output:

- Adapter: `duckdb`
- Path: `DBT_DUCKDB_PATH` environment variable, default `techpulse.duckdb`
- Threads: 4
- Target: `dev`
