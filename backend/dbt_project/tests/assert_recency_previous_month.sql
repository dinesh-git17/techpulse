-- Validates that the previous complete month has job posting data.
-- Detects data staleness where the ingestion pipeline may have stopped.
-- Test FAILS if previous complete month has zero total_jobs across all technologies.
--
-- Example: If today is 2026-01-15, previous complete month is 2025-12-01.
-- The test checks that at least one row for 2025-12-01 has total_jobs > 0.

{{
  config(
    severity='warn'
  )
}}

with previous_month as (
    select
        cast(date_trunc('month', current_date) - interval '1 month' as date) as month
),

previous_month_data as (
    select
        m.month,
        max(t.total_jobs) as max_total_jobs
    from previous_month m
    left join {{ ref('mart_monthly_trends') }} t
        on m.month = t.month
    group by m.month
)

select
    month,
    max_total_jobs
from previous_month_data
where max_total_jobs is null or max_total_jobs = 0
