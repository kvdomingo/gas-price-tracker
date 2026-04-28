with source as (
    select * from {{ source('raw', 'raw_extraction_results') }}
),

records as (
    select
        id,
        source_document_id,
        extracted_at,
        jsonb_array_elements(raw_output::jsonb) as record
    from source
    where
        raw_output is not null
        and raw_output != '[]'
),

parsed as (
    select
        id,
        source_document_id,
        extracted_at,
        (record ->> 'price_php_per_liter')::numeric as price_php_per_liter,
        (record ->> 'effective_date')::date as effective_date,
        lower(trim(record ->> 'fuel_type')) as fuel_type,
        trim(record ->> 'location_string') as location_string
    from records
    where
        record ->> 'fuel_type' is not null
        and record ->> 'price_php_per_liter' is not null
        and record ->> 'location_string' is not null
        and record ->> 'effective_date' is not null
)

select * from parsed
