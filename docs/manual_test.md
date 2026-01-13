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

### Explicitly Not Covered

- API serving layer (Phase 3)
- Frontend visualization (Phase 4)
- Production scheduling and alerting
- Performance benchmarking under load
- Multi-user concurrency scenarios

---

## 3. Systems and Components Tested

### Ingestion Layer

| Component | Description |
|-----------|-------------|
| `who_is_hiring_thread_id` | Dagster asset that resolves monthly thread IDs from HN API |
| `raw_hn_items` | Dagster asset that traverses thread comments and persists to Bronze |
| `HackerNewsClient` | HTTP client for Firebase HN API |
| `DuckDBStore` | Bronze layer persistence with append-only semantics |

### Transformation Layer

| Component | Description |
|-----------|-------------|
| `stg_job_postings` | Silver model: parses JSON, cleans HTML, deduplicates |
| `tech_taxonomy` | Seed: reference data for technology classification |
| `job_technology_bridge` | Bridge model: regex-based entity resolution |
| `mart_monthly_trends` | Gold model: aggregated technology trend metrics |
| `util_month_spine` | Utility model: continuous calendar spine from 2011 to present |

### Data Quality Layer

| Component | Description |
|-----------|-------------|
| dbt schema tests | Not-null, unique, accepted values constraints |
| dbt custom tests | False positive guards, growth calculation invariants |

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
```

### Test Data

| Partition | Items Ingested | Comments (non-deleted) |
|-----------|----------------|------------------------|
| 2023-01-01 | 569 | 535 |
| 2023-02-01 | 623 | 593 |
| 2023-03-01 | 675 | 642 |
| 2023-11-01 | 667 | 625 |

---

## 5. Results and Observations

### Scenario Outcomes

| Scenario | Description | Outcome |
|----------|-------------|---------|
| 1 | Infrastructure initialization and seed loading | Pass |
| 2 | Single month ingestion and transformation | Pass |
| 3 | Historical backfill (3 months) | Pass |
| 4 | Idempotency under re-ingestion | Pass |
| 5 | Taxonomy false positive rejection | Pass |
| 6 | Graceful failure on missing dependency | Pass |

### Layer Validation

| Layer | Validation | Outcome |
|-------|------------|---------|
| Bronze | Row count greater than zero | Pass (3202 rows) |
| Silver | No HTML tags in text column | Pass (0 violations) |
| Silver | No duplicate primary keys | Pass (0 duplicates) |
| Gold | pct_share equals mention_count divided by total_jobs | Pass |

### Data Invariants

| Invariant | Description | Outcome |
|-----------|-------------|---------|
| Time Conservation | Silver posted_at matches Bronze payload time | Pass (0 mismatches) |
| Referential Integrity | All tech_keys in Gold exist in taxonomy | Pass (0 orphans) |
| Spine Completeness | Python row exists for all 176 months | Pass |
| Metric Bounds | pct_share between 0.0 and 1.0 | Pass (0 violations) |

### Defects Discovered and Resolved

Two defects were identified during Scenario 2 execution and resolved before proceeding:

1. **Timestamp Parsing Mismatch**
   - Symptom: `stg_job_postings` failed with conversion error
   - Root Cause: Pydantic serializes datetime as ISO 8601 strings; model expected Unix bigint
   - Resolution: Changed `to_timestamp(cast(...as bigint))` to `cast(...as timestamp with time zone)`

2. **Deleted Comments Causing Null Violations**
   - Symptom: 41 rows failed not_null tests on author and text columns
   - Root Cause: Deleted HN comments have null content but were not filtered
   - Resolution: Added `deleted = false` predicate to source CTE

### Edge Cases Validated

| Case | Input | Expected | Actual |
|------|-------|----------|--------|
| False positive: "Go" as English word | "I will Go to the store" | No match to Golang | No match (correct) |
| Re-ingestion idempotency | Same partition ingested twice | Silver count unchanged | 625 before, 625 after (correct) |
| Missing Bronze table | Renamed raw_hn_items | Clear error message | "Table with name raw_hn_items does not exist" (correct) |

---

## 6. Known Limitations and Follow-Ups

### Intentionally Deferred

| Item | Reason |
|------|--------|
| October 2023 data gap | Not required for validation; causes expected warning in recency test |
| Full historical backfill (2011-present) | Time-prohibitive for manual testing; will validate via sampling in production |
| API response latency testing | Out of scope for Phase 1-2 |

### Recommended Follow-Ups

| Item | Phase | Priority |
|------|-------|----------|
| Add integration test for timestamp format contract | Phase 2 hardening | Medium |
| Document deleted comment filtering in model docstring | Phase 2 hardening | Low |
| Validate mom_growth_pct calculation with continuous data | Phase 3 | Medium |

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

### Conditions for Progression

Phase 3 (API Serving) may proceed. The following conditions apply:

1. The two bug fixes must be merged to main before Phase 3 development begins
2. The recency test warning is expected until continuous ingestion is operational
3. Full historical backfill should be scheduled as a production task, not a Phase 3 blocker

---

## Appendix: Test Environment

| Property | Value |
|----------|-------|
| Execution Date | 2026-01-12 |
| Python Version | 3.12 |
| dbt Version | 1.11.2 |
| DuckDB Adapter | 1.10.0 |
| Dagster Version | Latest (via uv) |
| Test Database | test_data/techpulse.duckdb |
| Host Platform | macOS Darwin 25.2.0 |
