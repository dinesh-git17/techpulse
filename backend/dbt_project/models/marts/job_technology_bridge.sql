{{
    config(
        materialized='table'
    )
}}

select distinct
    job.id as job_id,
    tech.tech_key,
    tech.category as tech_category,
    job.posted_at as job_posted_at,
    current_timestamp as matched_at
from {{ ref('stg_job_postings') }} as job
cross join {{ ref('tech_taxonomy') }} as tech
where regexp_matches(job.full_text, tech.regex_pattern, 'i')
