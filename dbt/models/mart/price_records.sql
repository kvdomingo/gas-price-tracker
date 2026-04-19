{{
    config(
        materialized='incremental',
        unique_key=['effective_date', 'psgc_code', 'fuel_type'],
        on_schema_change='fail',
        indexes=[
            {'columns': ['effective_date'], 'type': 'btree'},
            {'columns': ['psgc_code'], 'type': 'btree'},
            {'columns': ['fuel_type'], 'type': 'btree'},
        ]
    )
}}

with resolved as (
    select * from {{ ref('int_price_records_resolved') }}
    where price_in_range = true
),

final as (
    select
        {{ dbt_utils.generate_surrogate_key(['effective_date', 'psgc_code', 'fuel_type']) }} as id, -- noqa: LT02,LT05
        effective_date,
        psgc_code,
        fuel_type,
        price_php_per_liter,
        source_document_id,
        location_string as raw_location,
        now() as ingested_at
    from resolved
)

select * from final

{% if is_incremental() %}
    where (effective_date, psgc_code, fuel_type) not in (
        select
            t.effective_date,
            t.psgc_code,
            t.fuel_type
        from {{ this }} as t
    )
{% endif %}
