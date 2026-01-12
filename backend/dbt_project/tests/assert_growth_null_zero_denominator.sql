-- Validates that growth metrics are NULL when the denominator (previous period share) is 0.
-- A transition from 0% share to any positive share is mathematically undefined.
-- Test FAILS if any row has non-NULL growth when previous period share was 0.

with lagged_data as (
    select
        month,
        tech_key,
        pct_share,
        mom_growth_pct,
        yoy_growth_pct,
        lag(pct_share, 1) over (partition by tech_key order by month) as prev_month_share,
        lag(pct_share, 12) over (partition by tech_key order by month) as prev_year_share
    from {{ ref('mart_monthly_trends') }}
)

select
    month,
    tech_key,
    prev_month_share,
    mom_growth_pct,
    prev_year_share,
    yoy_growth_pct
from lagged_data
where
    (prev_month_share = 0 and mom_growth_pct is not null)
    or (prev_year_share = 0 and yoy_growth_pct is not null)
