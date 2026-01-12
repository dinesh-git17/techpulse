-- Validates that mom_growth_pct is NULL for the first month (2011-06-01)
-- and yoy_growth_pct is NULL for the first 12 months (no year-ago comparison).
-- Test FAILS if any row violates these conditions.

select
    month,
    tech_key,
    mom_growth_pct,
    yoy_growth_pct
from {{ ref('mart_monthly_trends') }}
where
    (month = date '2011-06-01' and mom_growth_pct is not null)
    or (month < date '2012-06-01' and yoy_growth_pct is not null)
