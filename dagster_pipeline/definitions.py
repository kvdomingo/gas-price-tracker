from dagster import Definitions
from dagster_dbt import DbtCliResource

from .codegen_assets import sqlalchemy_models
from .dbt_assets import gas_price_tracker_dbt_assets
from .extraction_assets import extracted_price_records
from .ingestion_assets import doe_publications
from .resources import DBT_PROJECT_DIR
from .schedules import weekly_ingestion_schedule

defs = Definitions(
    assets=[
        doe_publications,
        extracted_price_records,
        gas_price_tracker_dbt_assets,
        sqlalchemy_models,
    ],
    schedules=[weekly_ingestion_schedule],
    resources={
        "dbt": DbtCliResource(project_dir=str(DBT_PROJECT_DIR)),
    },
)
