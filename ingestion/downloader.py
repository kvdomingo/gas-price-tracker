import hashlib
import logging
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy.orm import Session

from .http_client import polite_download
from .scraper import PublicationLink

logger = logging.getLogger(__name__)

_CHUNK = 8192


def _content_hash(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(_CHUNK), b""):
            h.update(chunk)
    return h.hexdigest()


def is_already_ingested(db: Session, url: str) -> bool:
    from storage.models import SourceDocuments

    return (
        db.query(SourceDocuments).filter(SourceDocuments.url == url).first() is not None
    )


def download_publication(
    db: Session,
    pub: PublicationLink,
    storage_path: str,
) -> str | None:
    """Download a publication PDF and register it. Returns the document ID or None on failure."""
    from storage.models import SourceDocuments

    dest_dir = Path(storage_path)
    dest_dir.mkdir(parents=True, exist_ok=True)
    filename = pub.url.rstrip("/").split("/")[-1]
    dest_path = dest_dir / filename

    try:
        polite_download(pub.url, str(dest_path))
        content_hash = _content_hash(dest_path)

        doc = SourceDocuments(
            url=pub.url,
            local_path=str(dest_path),
            content_hash=content_hash,
            status="downloaded",
            downloaded_at=datetime.now(UTC),
            publication_date=pub.publication_date,
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)
        return str(doc.id)

    except Exception as exc:
        logger.error("Download failed for %s: %s", pub.url, exc)
        existing = (
            db.query(SourceDocuments).filter(SourceDocuments.url == pub.url).first()
        )
        if existing:
            existing.status = "download_failed"
            db.commit()
        else:
            doc = SourceDocuments(
                url=pub.url,
                status="download_failed",
                downloaded_at=datetime.now(UTC),
            )
            db.add(doc)
            db.commit()
        return None
