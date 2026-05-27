from urllib.parse import urlencode

import dagster as dg
from pydantic import HttpUrl
from scrapling.fetchers import FetcherSession

from common.settings import settings
from pipeline.partitions import files_partitions_def


@dg.sensor()
def files_sensor(context: dg.SensorEvaluationContext):
    with FetcherSession(impersonate="chrome") as session:
        url = HttpUrl.build(
            scheme="https",
            host=settings.DOE_LISTING_BASE_URL,
            path=settings.DOE_LISTING_BASE_PATH,
            query=urlencode(settings.DOE_LISTING_BASE_PARAMS),
        )
        context.log.info(f"Fetching {url}...")
        page = session.get(url.encoded_string())
        link_elements = page.css("div.ex1").css(
            f'a[href^="https://{settings.DOE_PDF_BASE_URL}"]'
        )
        links: list[str] = [el.attrib.get("href") for el in link_elements]
        context.log.info(f"Discovered {len(links)} links")

    prefix = HttpUrl.build(
        scheme="https",
        host=settings.DOE_PDF_BASE_URL,
        path=settings.DOE_PDF_BASE_PATH,
    ).encoded_string()
    partitions = []
    for link in links:
        partition = link.replace(prefix, "").lstrip("/")
        if (
            files_partitions_def.name is not None
            and not context.instance.has_dynamic_partition(
                files_partitions_def.name, partition
            )
        ):
            partitions.append(partition)

    context.log.info(f"Adding {len(partitions)} new partitions...")
    return dg.SensorResult(
        dynamic_partitions_requests=[
            files_partitions_def.build_add_request(partitions)
        ],
    )
