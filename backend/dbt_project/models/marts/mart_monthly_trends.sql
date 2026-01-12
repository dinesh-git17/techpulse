{{
  config(
    materialized='table'
  )
}}

with dense_grid as (
    select
        spine.month,
        tech.tech_key,
        tech.tech_name
    from {{ ref('util_month_spine') }} as spine
    cross join {{ ref('dim_technologies') }} as tech
),

monthly_mentions as (
    select
        cast(date_trunc('month', job_posted_at) as date) as month,
        tech_key,
        count(distinct job_id) as mention_count
    from {{ ref('job_technology_bridge') }}
    group by 1, 2
),

monthly_totals as (
    select
        cast(date_trunc('month', posted_at) as date) as month,
        count(distinct id) as total_jobs
    from {{ ref('stg_job_postings') }}
    group by 1
),

base_metrics as (
    select
        grid.month,
        grid.tech_key,
        grid.tech_name,
        coalesce(mentions.mention_count, 0) as mention_count,
        coalesce(totals.total_jobs, 0) as total_jobs,
        case
            when coalesce(totals.total_jobs, 0) = 0 then 0.0
            else cast(coalesce(mentions.mention_count, 0) as double) / totals.total_jobs
        end as pct_share
    from dense_grid as grid
    left join monthly_mentions as mentions
        on grid.month = mentions.month
        and grid.tech_key = mentions.tech_key
    left join monthly_totals as totals
        on grid.month = totals.month
),

with_lagged_shares as (
    select
        *,
        lag(pct_share, 1) over (partition by tech_key order by month) as prev_month_share,
        lag(pct_share, 12) over (partition by tech_key order by month) as prev_year_share
    from base_metrics
)

select
    month,
    tech_key,
    tech_name,
    mention_count,
    total_jobs,
    pct_share,
    case
        when prev_month_share is null or prev_month_share = 0 then null
        else ((pct_share - prev_month_share) / prev_month_share) * 100
    end as mom_growth_pct,
    case
        when prev_year_share is null or prev_year_share = 0 then null
        else ((pct_share - prev_year_share) / prev_year_share) * 100
    end as yoy_growth_pct
from with_lagged_shares
