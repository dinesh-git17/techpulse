{{
  config(
    materialized='table'
  )
}}

select
    tech_key,
    display_name as tech_name
from {{ ref('tech_taxonomy') }}
