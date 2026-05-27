from dagster import Definitions

from pipeline.codegen_assets import sqlalchemy_models
from pipeline.dbt_assets import gas_price_tracker_dbt_assets
from pipeline.extraction_assets import extracted_price_records
from pipeline.ingestion_assets import doe_publications
from pipeline.resources import RESOURCE_REGISTRY

defs = Definitions(
    assets=[
        doe_publications,
        extracted_price_records,
        gas_price_tracker_dbt_assets,
        sqlalchemy_models,
    ],
    jobs=[],
    schedules=[],
    sensors=[],
    resources=RESOURCE_REGISTRY,
)
