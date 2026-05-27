from dagster_aws.s3 import S3Resource
from enum import StrEnum

from dagster_dbt import DbtCliResource

from common.settings import settings

from .dbt import dbt_project
from .postgres import PostgresResource


class Resource(StrEnum):
    DBT = "dbt"
    POSTGRES = "postgres"
    MINIO = "minio"


class IOManager(StrEnum):
    pass


RESOURCE_REGISTRY = {
    Resource.DBT.value: DbtCliResource(project_dir=str(dbt_project.project_dir)),
    Resource.POSTGRES.value: PostgresResource(
        connection_url=settings.DATABASE_URL.encoded_string()
    ),
    Resource.MINIO.value: S3Resource(
        endpoint_url=settings.MINIO_ENDPOINT_URL.encoded_string(),
        aws_access_key_id=settings.MINIO_ACCESS_KEY.get_secret_value(),
        aws_secret_access_key=settings.MINIO_SECRET_KEY.get_secret_value(),
    ),
}
