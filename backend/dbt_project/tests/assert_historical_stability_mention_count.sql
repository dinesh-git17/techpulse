-- Validates that mention_count in mart_monthly_trends matches the source aggregation
-- from job_technology_bridge. Ensures no data loss or inflation in the mart.
--
-- This test validates internal consistency between the mart and its source.
-- For true cross-run drift detection (detecting if historical values change between
-- pipeline runs), a snapshot mechanism would be required.
--
-- Test FAILS if any (month, tech_key) combination has a mention_count that differs
-- from the source count by more than 1% (relative) or more than 1 (absolute for small counts).

with source_counts as (
    select
        cast(date_trunc('month', job_posted_at) as date) as month,
        tech_key,
        count(distinct job_id) as source_mention_count
    from {{ ref('job_technology_bridge') }}
    group by 1, 2
),

mart_counts as (
    select
        month,
        tech_key,
        mention_count as mart_mention_count
    from {{ ref('mart_monthly_trends') }}
    where mention_count > 0
),

comparison as (
    select
        coalesce(m.month, s.month) as month,
        coalesce(m.tech_key, s.tech_key) as tech_key,
        coalesce(s.source_mention_count, 0) as source_count,
        coalesce(m.mart_mention_count, 0) as mart_count,
        abs(coalesce(m.mart_mention_count, 0) - coalesce(s.source_mention_count, 0)) as abs_diff,
        case
            when coalesce(s.source_mention_count, 0) = 0 then null
            else abs(coalesce(m.mart_mention_count, 0) - s.source_mention_count)
                 * 100.0 / s.source_mention_count
        end as pct_diff
    from mart_counts m
    full outer join source_counts s
        on m.month = s.month
        and m.tech_key = s.tech_key
)

select
    month,
    tech_key,
    source_count,
    mart_count,
    abs_diff,
    pct_diff
from comparison
where
    abs_diff > 1
    or (pct_diff is not null and pct_diff > 1.0)
