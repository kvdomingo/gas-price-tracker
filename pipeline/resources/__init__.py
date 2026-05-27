from enum import StrEnum

from dagster_dbt import DbtCliResource

from common.settings import settings

from .dbt import dbt_project
from .postgres import PostgresResource


class Resource(StrEnum):
    DBT = "dbt"
    POSTGRES = "postgres"


class IOManager(StrEnum):
    pass


RESOURCE_REGISTRY = {
    Resource.DBT.value: DbtCliResource(project_dir=str(dbt_project.project_dir)),
    Resource.POSTGRES.value: PostgresResource(
        connection_url=settings.DATABASE_URL.encoded_string()
    ),
}
