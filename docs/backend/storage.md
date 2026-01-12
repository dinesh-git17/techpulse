# Storage

## Purpose

Persist raw Hacker News data in a DuckDB Bronze layer with transactional batch
inserts, schema initialization, and structured error reporting.

## Module Structure

- `techpulse.storage.schema` defines Bronze table DDL and schema helpers.
- `techpulse.storage.manager` manages database lifecycle and connections.
- `techpulse.storage.store` provides batch insert and query operations.
- `techpulse.storage.exceptions` defines storage error types.

## Schema

### `raw_hn_items`

Append-only table storing raw JSON payloads with ingestion metadata.

Columns:

- `load_id` UUID, not null
- `ingested_at` TIMESTAMPTZ, not null
- `payload` JSON, not null

`initialize_schema` executes idempotent DDL to ensure the table exists.

## DuckDBManager

### Responsibilities

- Resolve database path from:
  1. Explicit `database_path` argument
  2. `TECHPULSE_DB_PATH` environment variable
  3. Default `backend/data/techpulse.duckdb`
- Create parent directories for the database file.
- Establish DuckDB connections with exponential backoff retry on lock errors.
- Initialize the Bronze schema on connection entry.

### Control Flow

- Use as a context manager.
- On `__enter__`, ensure directories, connect, and call `initialize_schema`.
- On `__exit__`, close the active connection.

### Error Handling

- Raises `StorageConnectionError` on directory creation failure or connection
  failures after retries.
- Raises `RuntimeError` if `get_connection` is called outside of context manager.

## DuckDBStore

### Responsibilities

- Insert batches of raw item dictionaries into `raw_hn_items`.
- Serialize payloads as JSON and generate ingestion timestamps in UTC.
- Wrap inserts in a single transaction for atomicity.

### Data Contract

`insert_items(load_id, items)`:

- Inputs:
  - `load_id`: UUID identifying a single ingestion batch.
  - `items`: list of dictionaries to store as JSON.
- Output: integer count of inserted rows.
- Side effects: writes rows to `raw_hn_items`.

### Control Flow

- Validates each item by JSON serialization.
- Executes `BEGIN TRANSACTION`, inserts each payload, and `COMMIT`s.
- Returns inserted row count, or 0 if the batch is empty.

### Error Handling

- `InvalidPayloadError` for JSON serialization failures or JSON rejection by
  DuckDB.
- `TransactionError` for database failures during insert or commit.
- `RuntimeError` if called outside of a context manager.

## Storage Exceptions

- `StorageError`: base class for all storage failures.
- `StorageConnectionError`: database connection or filesystem failures.
- `InvalidPayloadError`: invalid JSON payloads.
- `TransactionError`: transaction failures with rollback.
