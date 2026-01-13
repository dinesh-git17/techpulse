# Manual Testing Record

This document records the outcomes of manual validation exercises performed against the TechPulse data platform. It serves as a permanent engineering record for phase sign-off and audit purposes.

---

## 1. Purpose of This Document

Manual testing validates end-to-end system behavior that automated unit and integration tests cannot fully cover. This includes:

- Cross-layer data integrity from ingestion to analytical output
- Idempotency guarantees under repeated execution
- Graceful failure behavior when dependencies are missing
- Business logic correctness in entity resolution and aggregation

This document is referenced during phase completion reviews and serves as evidence of validation discipline for internal audits and external due diligence.

---

## 2. Testing Scope

### Phases Covered

- **Phase 1:** Data Ingestion (Dagster assets, HN API integration, Bronze layer)
- **Phase 2:** Data Transformation (dbt models, Silver/Gold layers, entity resolution)
- **Phase 3.1:** API Backend (FastAPI endpoints, Redis caching, observability)

### Explicitly Not Covered

- Frontend visualization (Phase 3.2)
- Production scheduling and alerting
- Performance benchmarking under load
- Multi-user concurrency scenarios

---

## 3. Systems and Components Tested

### Ingestion Layer

| Component                 | Description                                                         |
| ------------------------- | ------------------------------------------------------------------- |
| `who_is_hiring_thread_id` | Dagster asset that resolves monthly thread IDs from HN API          |
| `raw_hn_items`            | Dagster asset that traverses thread comments and persists to Bronze |
| `HackerNewsClient`        | HTTP client for Firebase HN API                                     |
| `DuckDBStore`             | Bronze layer persistence with append-only semantics                 |

### Transformation Layer

| Component               | Description                                                   |
| ----------------------- | ------------------------------------------------------------- |
| `stg_job_postings`      | Silver model: parses JSON, cleans HTML, deduplicates          |
| `tech_taxonomy`         | Seed: reference data for technology classification            |
| `job_technology_bridge` | Bridge model: regex-based entity resolution                   |
| `mart_monthly_trends`   | Gold model: aggregated technology trend metrics               |
| `util_month_spine`      | Utility model: continuous calendar spine from 2011 to present |

### Data Quality Layer

| Component        | Description                                          |
| ---------------- | ---------------------------------------------------- |
| dbt schema tests | Not-null, unique, accepted values constraints        |
| dbt custom tests | False positive guards, growth calculation invariants |

### API Layer

| Component              | Description                                                  |
| ---------------------- | ------------------------------------------------------------ |
| `/health`              | Health check endpoint reporting DB and cache status          |
| `/api/v1/technologies` | Taxonomy discovery endpoint returning sorted technology list |
| `/api/v1/trends`       | Time-series trend data with caching and validation           |
| `/metrics`             | Prometheus metrics endpoint for observability                |
| `CacheService`         | Redis cache-aside implementation with key canonicalization   |
| `RequestMiddleware`    | Correlation ID injection and structured logging              |

---

## 4. Test Execution Summary

All tests were executed locally on macOS using CLI tools. The test environment used an isolated DuckDB instance at `test_data/techpulse.duckdb` to avoid contaminating development data.

### Execution Method

```
# Ingestion
dagster asset materialize --select '<asset>' --partition <date> -m techpulse.data.definitions

# Transformation
dbt build --target dev

# Validation
dbt test --target dev

# API Server
TECHPULSE_DB_PATH=./test_data/techpulse.duckdb \
TECHPULSE_REDIS_URL=redis://localhost:6379/0 \
TECHPULSE_LOG_JSON_FORMAT=true \
uvicorn techpulse.api.main:app --app-dir backend/src --port 8000

# API Validation
curl -s http://localhost:8000/health
curl -s http://localhost:8000/api/v1/technologies
curl -s "http://localhost:8000/api/v1/trends?tech_ids=python&start_date=2023-01-01&end_date=2023-12-01"
```

### Test Data

| Partition  | Items Ingested | Comments (non-deleted) |
| ---------- | -------------- | ---------------------- |
| 2023-01-01 | 569            | 535                    |
| 2023-02-01 | 623            | 593                    |
| 2023-03-01 | 675            | 642                    |
| 2023-11-01 | 667            | 625                    |

---

## 5. Results and Observations

### Scenario Outcomes

#### Phase 1-2: Data Pipeline

| Scenario | Description                                    | Outcome |
| -------- | ---------------------------------------------- | ------- |
| 1        | Infrastructure initialization and seed loading | Pass    |
| 2        | Single month ingestion and transformation      | Pass    |
| 3        | Historical backfill (3 months)                 | Pass    |
| 4        | Idempotency under re-ingestion                 | Pass    |
| 5        | Taxonomy false positive rejection              | Pass    |
| 6        | Graceful failure on missing dependency         | Pass    |

#### Phase 3.1: API Backend

| Scenario | Description                                                   | Outcome |
| -------- | ------------------------------------------------------------- | ------- |
| 1        | Cold start pipeline execution (end-to-end data flow)          | Pass    |
| 2        | Pipeline idempotency (no duplicates on re-run)                | Pass    |
| 3        | Service health and dependency check                           | Pass    |
| 4        | Taxonomy discovery (static data)                              | Pass    |
| 5        | Trend data retrieval (API matches DB ground truth)            | Pass    |
| 6        | Input validation and guardrails (422 on invalid input)        | Pass    |
| 7        | Cache-aside behavior (hit/miss with sub-20ms cache hits)      | Pass    |
| 8        | Cache key canonicalization (parameter order independence)     | Pass    |
| 9        | Structured logging verification (JSON format with request_id) | Pass    |
| 10       | Metrics exposure (Prometheus counters)                        | Pass    |
| 11       | Dependency failure mode (graceful degradation without Redis)  | Pass    |

### Layer Validation

| Layer  | Validation                                             | Outcome                    |
| ------ | ------------------------------------------------------ | -------------------------- |
| Bronze | Row count greater than zero                            | Pass (3202 rows)           |
| Silver | No HTML tags in text column                            | Pass (0 violations)        |
| Silver | No duplicate primary keys                              | Pass (0 duplicates)        |
| Gold   | pct_share equals mention_count divided by total_jobs   | Pass                       |
| API    | `/trends` response matches `mart_monthly_trends` query | Pass (Python: 79 mentions) |
| API    | `/technologies` returns sorted taxonomy                | Pass (20 technologies)     |
| API    | Cache key count equals 1 for equivalent queries        | Pass                       |

### Data Invariants

| Invariant             | Description                                  | Outcome             |
| --------------------- | -------------------------------------------- | ------------------- |
| Time Conservation     | Silver posted_at matches Bronze payload time | Pass (0 mismatches) |
| Referential Integrity | All tech_keys in Gold exist in taxonomy      | Pass (0 orphans)    |
| Spine Completeness    | Python row exists for all 176 months         | Pass                |
| Metric Bounds         | pct_share between 0.0 and 1.0                | Pass (0 violations) |

### Defects Discovered and Resolved

Two defects were identified during Phase 1-2 Scenario 2 execution and resolved before proceeding:

1. **Timestamp Parsing Mismatch**

   - Symptom: `stg_job_postings` failed with conversion error
   - Root Cause: Pydantic serializes datetime as ISO 8601 strings; model expected Unix bigint
   - Resolution: Changed `to_timestamp(cast(...as bigint))` to `cast(...as timestamp with time zone)`

2. **Deleted Comments Causing Null Violations**
   - Symptom: 41 rows failed not_null tests on author and text columns
   - Root Cause: Deleted HN comments have null content but were not filtered
   - Resolution: Added `deleted = false` predicate to source CTE

One defect was identified during Phase 3.1 Scenario 7 and resolved before proceeding:

3. **Missing Cache Decorator on Trends Endpoint**
   - Symptom: Redis cache remained empty after `/trends` requests; no cache hits observed
   - Root Cause: The `@cached` decorator was implemented but not applied to the `get_trends` route handler
   - Resolution: Applied `@cached` decorator with canonicalized key generation to `/trends` endpoint

### Edge Cases Validated

| Case                                 | Input                                 | Expected                    | Actual                                                  |
| ------------------------------------ | ------------------------------------- | --------------------------- | ------------------------------------------------------- |
| False positive: "Go" as English word | "I will Go to the store"              | No match to Golang          | No match (correct)                                      |
| Re-ingestion idempotency             | Same partition ingested twice         | Silver count unchanged      | 625 before, 625 after (correct)                         |
| Missing Bronze table                 | Renamed raw_hn_items                  | Clear error message         | "Table with name raw_hn_items does not exist" (correct) |
| Missing query parameters             | GET /trends (no params)               | HTTP 422                    | HTTP 422 (correct)                                      |
| Invalid date format                  | start_date=invalid                    | HTTP 422                    | HTTP 422 (correct)                                      |
| Exceeding tech limit                 | 11 tech_ids requested                 | HTTP 422 with limit message | "Maximum 10 technologies allowed" (correct)             |
| Cache key order independence         | tech_ids=python,react vs react,python | Same cache key              | 1 key in Redis (correct)                                |
| Redis unavailable                    | Stop Redis container                  | Graceful fallback to DB     | HTTP 200 with data (correct)                            |

---

## 6. Known Limitations and Follow-Ups

### Intentionally Deferred

| Item                                    | Reason                                                                        |
| --------------------------------------- | ----------------------------------------------------------------------------- |
| October 2023 data gap                   | Not required for validation; causes expected warning in recency test          |
| Full historical backfill (2011-present) | Time-prohibitive for manual testing; will validate via sampling in production |
| Load testing and benchmarking           | Out of scope for functional validation; separate performance testing phase    |

### Recommended Follow-Ups

| Item                                                     | Phase             | Priority |
| -------------------------------------------------------- | ----------------- | -------- |
| Add integration test for timestamp format contract       | Phase 2 hardening | Medium   |
| Document deleted comment filtering in model docstring    | Phase 2 hardening | Low      |
| Validate mom_growth_pct calculation with continuous data | Phase 3.2         | Medium   |
| Add cache TTL configuration to environment variables     | Phase 3 hardening | Low      |
| Implement cache warming on startup for common queries    | Phase 4           | Low      |

---

## 7. Phase Readiness Assessment

### Phase 1: Data Ingestion

**Status: Complete**

All ingestion scenarios passed. The Dagster assets correctly fetch data from the Hacker News API, traverse comment trees, and persist payloads to the Bronze layer with append-only semantics. Re-ingestion does not corrupt downstream layers.

### Phase 2: Data Transformation

**Status: Complete**

All transformation scenarios passed after applying two bug fixes to the staging model. The dbt pipeline correctly:

- Parses and cleans raw JSON payloads
- Filters deleted content
- Resolves technology entities without false positives
- Aggregates monthly trend metrics
- Maintains referential integrity with the taxonomy seed
- Produces a complete calendar spine for time-series analysis

### Phase 3.1: API Backend

**Status: Complete**

All 11 API scenarios passed after applying one bug fix to enable Redis caching. The FastAPI backend correctly:

- Serves health checks with dependency status reporting
- Returns taxonomy data via `/technologies` endpoint
- Returns time-series trend data via `/trends` endpoint with exact match to Gold layer
- Validates input parameters and returns RFC 7807 error responses
- Implements cache-aside pattern with sub-20ms cache hits
- Canonicalizes cache keys to prevent fragmentation
- Emits structured JSON logs with correlation IDs
- Exposes Prometheus metrics for observability
- Degrades gracefully when Redis is unavailable (fail-open strategy)

### Conditions for Progression

Phase 3.2 (Frontend Development) may proceed. The following conditions apply:

1. All bug fixes (timestamp parsing, deleted comment filtering, cache decorator) must be merged to main
2. The recency test warning is expected until continuous ingestion is operational
3. Full historical backfill should be scheduled as a production task, not a Phase 3.2 blocker
4. Frontend team may generate API clients (e.g., TanStack Query) against the stable contract

---

## Appendix: Test Environment

### Phase 1-2 Environment (2026-01-12)

| Property        | Value                      |
| --------------- | -------------------------- |
| Execution Date  | 2026-01-12                 |
| Python Version  | 3.12                       |
| dbt Version     | 1.11.2                     |
| DuckDB Adapter  | 1.10.0                     |
| Dagster Version | Latest (via uv)            |
| Test Database   | test_data/techpulse.duckdb |
| Host Platform   | macOS Darwin 25.2.0        |

### Phase 3.1 Environment (2026-01-13)

| Property        | Value                      |
| --------------- | -------------------------- |
| Execution Date  | 2026-01-13                 |
| Python Version  | 3.12                       |
| FastAPI Version | Latest (via uv)            |
| Redis Version   | 7-alpine (Docker)          |
| Docker Runtime  | Colima                     |
| Test Database   | test_data/techpulse.duckdb |
| Host Platform   | macOS Darwin 25.2.0        |
