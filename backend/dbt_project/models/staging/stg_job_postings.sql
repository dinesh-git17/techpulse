{{
    config(
        materialized='table'
    )
}}

with source as (

    select
        load_id,
        ingested_at,
        payload
    from {{ source('hacker_news', 'raw_hn_items') }}
    where payload->>'type' = 'comment'
      and cast(payload->>'deleted' as boolean) = false

),

parsed as (

    select
        cast(payload->>'id' as integer) as id,
        cast(payload->>'by' as varchar) as author,
        cast(payload->>'time' as timestamp with time zone) as posted_at,
        {{ clean_html("payload->>'text'") }} as text,
        cast(payload->>'parent' as integer) as parent_id,
        load_id,
        ingested_at
    from source

)

select
    id,
    author,
    posted_at,
    text,
    coalesce(text, '') as full_text,
    parent_id,
    load_id,
    ingested_at
from parsed
qualify row_number() over (
    partition by id
    order by ingested_at desc
) = 1
