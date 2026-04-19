with staged as (
    select * from {{ ref('stg_extraction_results') }}
),

boundaries as (
    select * from {{ ref('psgc_boundaries') }}
),

-- Build a flat lookup: each alternative name variant maps to a psgc_code
boundary_names as (
    select
        psgc_code,
        lower(trim(name)) as lookup_name
    from boundaries

    union all

    select
        b.psgc_code,
        lower(trim(alt.name)) as lookup_name
    from boundaries as b,
        unnest(string_to_array(b.alternative_names, ',')) as alt (name)
    where
        b.alternative_names is not null
        and b.alternative_names != ''
),

resolved as (
    select
        s.id as extraction_result_id,
        s.source_document_id,
        s.effective_date,
        s.fuel_type,
        s.price_php_per_liter,
        s.location_string,
        s.extracted_at,
        bn.psgc_code
    from staged as s
    left join boundary_names as bn
        on lower(trim(s.location_string)) = bn.lookup_name
),

validated as (
    select
        *,
        price_php_per_liter between 10 and 500 as price_in_range
    from resolved
)

select * from validated
