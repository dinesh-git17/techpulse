-- Validates that common English text does not trigger false positive for Go.
-- Test FAILS if the go pattern matches "I go to the store".

with test_input as (
    select 'I go to the store' as test_text
),

taxonomy as (
    select tech_key, regex_pattern
    from {{ ref('tech_taxonomy') }}
    where tech_key = 'go'
),

false_positives as (
    select t.tech_key
    from test_input i
    cross join taxonomy t
    where regexp_matches(i.test_text, t.regex_pattern, 'i')
)

select * from false_positives
