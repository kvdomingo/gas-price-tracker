from typing import Literal

from sqlalchemy.orm import Session

DocumentStatus = Literal[
    "downloaded",
    "extracted",
    "extraction_failed",
    "download_failed",
    "validation_error",
]


def update_document_status(db: Session, doc_id: str, status: DocumentStatus) -> None:
    from storage.models import SourceDocuments  # type: ignore[attr-defined]

    doc = db.query(SourceDocuments).filter(SourceDocuments.id == doc_id).first()
    if doc:
        doc.status = status
        db.commit()
