{{
  config(
    materialized='table'
  )
}}

select
    cast(generate_series as date) as month
from generate_series(
    date '2011-06-01',
    date_trunc('month', current_date),
    interval '1 month'
)
