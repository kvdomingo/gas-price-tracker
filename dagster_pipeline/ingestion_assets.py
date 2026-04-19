import logging
import os

from dagster import AssetExecutionContext, WeeklyPartitionsDefinition, asset
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from ingestion.downloader import download_publication, is_already_ingested
from ingestion.robots import is_path_allowed
from ingestion.scraper import DOE_BASE_URL, DOE_LISTING_PATH, discover_publications

logger = logging.getLogger(__name__)

weekly_partitions = WeeklyPartitionsDefinition(start_date="2020-12-01")


@asset(
    partitions_def=weekly_partitions,
    group_name="ingestion",
)
def doe_publications(context: AssetExecutionContext) -> list[str]:
    """Discover and download new DOE fuel price PDF publications."""
    if not is_path_allowed(DOE_BASE_URL, DOE_LISTING_PATH):
        context.log.warning("DOE listing path disallowed by robots.txt — aborting run")
        return []

    engine = create_engine(os.environ["DATABASE_URL"])
    Session = sessionmaker(bind=engine)

    publications = discover_publications()
    context.log.info("Discovered %d publications", len(publications))

    storage_path = os.environ.get("PDF_STORAGE_PATH", "/app/data/pdfs")
    downloaded_ids: list[str] = []

    with Session() as db:
        for pub in publications:
            if is_already_ingested(db, pub.url):
                context.log.debug("Already ingested: %s", pub.url)
                continue
            doc_id = download_publication(db, pub, storage_path)
            if doc_id:
                downloaded_ids.append(doc_id)

    context.log.info("Downloaded %d new publications", len(downloaded_ids))
    return downloaded_ids
