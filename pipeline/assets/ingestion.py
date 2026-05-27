from typing import cast

import dagster as dg
from curl_cffi import AsyncSession
from dagster_aws.s3 import S3Resource
from pydantic import HttpUrl

from common.settings import settings
from pipeline.partitions import files_partitions_def


@dg.asset(partitions_def=files_partitions_def)
async def fuel_prices__raw(context: dg.AssetExecutionContext, minio: S3Resource):
    url = HttpUrl.build(
        scheme="https",
        host=settings.DOE_PDF_BASE_URL,
        path=f"{settings.DOE_PDF_BASE_PATH}/{context.partition_key}",
    )
    async with AsyncSession() as session:
        context.log.info(f"Fetching URL {url}...")
        session = cast(AsyncSession, session)
        cast(
            AsyncSession,
            await session.get(url.encoded_string(), stream=True, impersonate="chrome"),
        )
