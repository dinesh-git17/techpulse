-- Validates that "JavaScript" does not trigger a false positive for Java.
-- Test FAILS if the java pattern matches "JavaScript developer".

with test_input as (
    select 'JavaScript developer' as test_text
),

taxonomy as (
    select tech_key, regex_pattern
    from {{ ref('tech_taxonomy') }}
    where tech_key = 'java'
),

false_positives as (
    select t.tech_key
    from test_input i
    cross join taxonomy t
    where regexp_matches(i.test_text, t.regex_pattern, 'i')
)

select * from false_positives
