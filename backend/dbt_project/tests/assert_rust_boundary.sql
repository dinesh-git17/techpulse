-- Validates word boundary handling for Rust.
-- "Rust programming" MUST match rust.
-- "rusty nail" must NOT match rust.
-- Test FAILS if either condition is violated.

with test_cases as (
    select 'Rust programming' as test_text, true as should_match
    union all
    select 'rusty nail' as test_text, false as should_match
),

taxonomy as (
    select tech_key, regex_pattern
    from {{ ref('tech_taxonomy') }}
    where tech_key = 'rust'
),

results as (
    select
        tc.test_text,
        tc.should_match,
        regexp_matches(tc.test_text, t.regex_pattern, 'i') as did_match
    from test_cases tc
    cross join taxonomy t
),

failures as (
    select
        test_text,
        should_match,
        did_match
    from results
    where should_match != did_match
)

select * from failures
