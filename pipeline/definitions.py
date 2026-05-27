from dagster import Definitions, load_assets_from_package_module

from pipeline import assets
from pipeline.resources import RESOURCE_REGISTRY
from pipeline.sensors import files_sensor

defs = Definitions(
    assets=[*load_assets_from_package_module(assets)],
    jobs=[],
    schedules=[],
    sensors=[files_sensor],
    resources=RESOURCE_REGISTRY,
)
