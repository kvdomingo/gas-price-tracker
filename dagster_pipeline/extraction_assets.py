import logging
import os

from dagster import AssetExecutionContext, asset
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from extraction.pipeline import extract_document
from .ingestion_assets import doe_publications

logger = logging.getLogger(__name__)


@asset(deps=[doe_publications], group_name="extraction")
def extracted_price_records(context: AssetExecutionContext) -> None:
    """Extract structured price records from all newly downloaded PDFs."""
    engine = create_engine(os.environ["DATABASE_URL"])
    Session = sessionmaker(bind=engine)

    with Session() as db:
        from storage.models import SourceDocuments

        pending = (
            db.query(SourceDocuments)
            .filter(SourceDocuments.status == "downloaded")
            .all()
        )
        context.log.info("Extracting %d documents", len(pending))

        for doc in pending:
            if not doc.local_path or not doc.content_hash:
                context.log.warning(
                    "Skipping doc %s — missing local_path or content_hash", doc.id
                )
                continue
            records = extract_document(
                db, str(doc.id), doc.local_path, doc.content_hash
            )
            context.log.info(
                "Extracted %d records from %s", len(records), doc.local_path
            )
