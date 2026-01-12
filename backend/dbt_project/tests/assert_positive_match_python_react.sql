-- Validates that text containing "Python and React" matches both entities.
-- Test FAILS if either python or react is not matched.

with test_input as (
    select 'We use Python and React for our stack' as test_text
),

taxonomy as (
    select tech_key, regex_pattern
    from {{ ref('tech_taxonomy') }}
    where tech_key in ('python', 'react')
),

matches as (
    select
        t.tech_key,
        regexp_matches(i.test_text, t.regex_pattern, 'i') as is_matched
    from test_input i
    cross join taxonomy t
),

expected_matches as (
    select 'python' as tech_key
    union all
    select 'react' as tech_key
),

missing_matches as (
    select e.tech_key
    from expected_matches e
    left join matches m on e.tech_key = m.tech_key and m.is_matched = true
    where m.tech_key is null
)

select * from missing_matches
