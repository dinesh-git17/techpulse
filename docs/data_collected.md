# Data Collected in TechPulse

## Purpose
This document describes the data that is currently present in the seeded TechPulse database. It helps a reader understand what tables are populated, what those tables represent, and what questions the data can and cannot answer based on the data that exists today.

## Data Overview
The current dataset is sourced from Hacker News items ingested by the TechPulse pipelines. The raw payloads include standard Hacker News fields such as id, by, time, text, type, and parent, and are transformed into job posting records and technology trend aggregates.

Time coverage observed in the seeded database:
- Raw ingestion timestamps: 2026-01-12 to 2026-01-14
- Job posting timestamps: 2025-10-01 to 2025-12-30
- Monthly trend series: 2011-06 to 2026-01 (includes months with zero counts)

## Bronze Layer Data
Tables present:
- `raw_hn_items` (1752 rows)

What it represents:
- Raw Hacker News items stored as JSON payloads with minimal metadata.

Key characteristics:
- Immutable, append-only ingestion keyed by `load_id` and `ingested_at`
- `payload` retains original HN fields and HTML-encoded text

High-level columns:
- `load_id` (UUID): ingestion batch identifier
- `ingested_at` (timestamp with time zone): ingestion time
- `payload` (JSON): raw Hacker News item

## Silver Layer Data
Tables present:
- `stg_job_postings` (1660 rows)
- `tech_taxonomy` (20 rows)
- `dim_technologies` (20 rows)
- `job_technology_bridge` (1933 rows)
- `util_month_spine` (176 rows)

What it represents:
- `stg_job_postings` extracts job posts from raw items with cleaned text fields and posting timestamps.
- `tech_taxonomy` is the reference list of technologies and regex patterns used for matching.
- `dim_technologies` is a simplified technology dimension keyed by `tech_key`.
- `job_technology_bridge` links job postings to matched technologies.
- `util_month_spine` provides a complete list of months used for trend calculations.

High-level columns:
- `stg_job_postings`: id, author, posted_at, text, full_text, parent_id, load_id, ingested_at
- `tech_taxonomy`: tech_key, display_name, category, regex_pattern
- `dim_technologies`: tech_key, tech_name
- `job_technology_bridge`: job_id, tech_key, tech_category, job_posted_at, matched_at
- `util_month_spine`: month

## Gold Layer Data
Tables present:
- `mart_monthly_trends` (3520 rows)

What it represents:
- Monthly technology trend metrics derived from job postings and the month spine.

Available metrics:
- `mention_count`: number of job postings mentioning a technology in a month
- `total_jobs`: number of job postings in a month
- `pct_share`: `mention_count` divided by `total_jobs`
- `mom_growth_pct`: month over month change in `pct_share`
- `yoy_growth_pct`: year over year change in `pct_share`

High-level columns:
- `month`, `tech_key`, `tech_name`, `mention_count`, `total_jobs`, `pct_share`, `mom_growth_pct`, `yoy_growth_pct`

## Relationships & Flow
- Raw Hacker News items in `raw_hn_items` are transformed into job postings in `stg_job_postings`.
- `stg_job_postings.id` links to `job_technology_bridge.job_id` for technology matches.
- `job_technology_bridge.tech_key` maps to `dim_technologies.tech_key` and `tech_taxonomy.tech_key`.
- `util_month_spine.month` provides the full month series for `mart_monthly_trends`.
- `mart_monthly_trends` aggregates job postings by `month` and `tech_key` with technology labels from `dim_technologies`.

## Example Data Shapes
Representative row shapes with abbreviated values:

```text
raw_hn_items
- load_id: 751867cc-90ea-41a7-bfb9-4fbf5c59aa30
- ingested_at: 2026-01-12T11:01:01-05:00
- payload: {"id": 12345, "by": "...", "time": 1704067200, "text": "...", "type": "comment", "parent": 99999}

stg_job_postings
- id: 45439212
- author: "devinbhushan"
- posted_at: 2025-10-01T11:51:33-04:00
- text: "Squint | Onsite, San Francisco | ..."
- full_text: "Squint | Onsite, San Francisco | ..."
- parent_id: 45438503
- load_id: d3cadfbc-9623-4242-8664-b65f73beb978
- ingested_at: 2026-01-14T13:51:58-05:00

tech_taxonomy
- tech_key: "python"
- display_name: "Python"
- category: "Language"
- regex_pattern: "\\b(python|python3|py3)\\b"

dim_technologies
- tech_key: "javascript"
- tech_name: "JavaScript"

job_technology_bridge
- job_id: 45805590
- tech_key: "python"
- tech_category: "Language"
- job_posted_at: 2025-11-03T18:10:09-05:00
- matched_at: 2026-01-14T13:54:20-05:00

util_month_spine
- month: 2011-06-01

mart_monthly_trends
- month: 2011-07-01
- tech_key: "node"
- tech_name: "Node.js"
- mention_count: 0
- total_jobs: 0
- pct_share: 0.0
- mom_growth_pct: null
- yoy_growth_pct: null
```

## Current Limitations
- Coverage is limited to the Hacker News items currently seeded in `raw_hn_items`, which span a short ingestion window in January 2026.
- Job postings are limited to those extracted from ingested items, with posting times currently covering October to December 2025.
- Technology coverage is restricted to the 20 entries in `tech_taxonomy`, so technologies outside this list are not represented in `job_technology_bridge` or `mart_monthly_trends`.
- Monthly trend series includes months with zero counts, so the presence of a month does not imply activity or data availability.
- The data cannot answer questions about sources beyond Hacker News or job postings outside the ingested threads.
