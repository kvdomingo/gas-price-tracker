import json
import logging
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from .gemini_client import PriceRecord, extract_from_image, extract_from_text
from .ocr_extractor import extract_text_via_ocr
from .pdf_detector import is_digital_pdf
from .text_extractor import extract_text_from_pdf

logger = logging.getLogger(__name__)

_PRICE_MIN = 10.0
_PRICE_MAX = 500.0


def _get_cached_result(db: Session, content_hash: str) -> list[PriceRecord] | None:
    from storage.models import RawExtractionResults, SourceDocuments

    doc = (
        db.query(SourceDocuments)
        .filter(SourceDocuments.content_hash == content_hash)
        .filter(SourceDocuments.status == "extracted")
        .first()
    )
    if doc is None:
        return None

    result = (
        db.query(RawExtractionResults)
        .filter(RawExtractionResults.source_document_id == doc.id)
        .order_by(RawExtractionResults.extracted_at.desc())
        .first()
    )
    if result is None or not result.raw_output:
        return None

    try:
        raw = json.loads(result.raw_output)
        return [
            PriceRecord(
                fuel_type=r["fuel_type"],
                price_php_per_liter=float(r["price_php_per_liter"]),
                location_string=r["location_string"],
                effective_date=r["effective_date"],
            )
            for r in raw
        ]
    except Exception:
        return None


def _write_raw_output(db: Session, doc_id: str, records: list[PriceRecord]) -> None:
    from storage.models import RawExtractionResults

    serializable = [
        {
            "fuel_type": r.fuel_type,
            "price_php_per_liter": r.price_php_per_liter,
            "location_string": r.location_string,
            "effective_date": r.effective_date.isoformat(),
        }
        for r in records
    ]
    result = RawExtractionResults(
        source_document_id=doc_id,
        raw_output=json.dumps(serializable),
        extracted_at=datetime.now(UTC),
    )
    db.add(result)
    db.commit()


def _validate(
    records: list[PriceRecord],
) -> tuple[list[PriceRecord], list[PriceRecord]]:
    valid, invalid = [], []
    for r in records:
        if _PRICE_MIN <= r.price_php_per_liter <= _PRICE_MAX:
            valid.append(r)
        else:
            logger.warning(
                "Price out of range: %s %s %.2f",
                r.fuel_type,
                r.location_string,
                r.price_php_per_liter,
            )
            invalid.append(r)
    return valid, invalid


def extract_document(
    db: Session, doc_id: str, pdf_path: str, content_hash: str
) -> list[PriceRecord]:
    from storage.models import SourceDocuments

    cached = _get_cached_result(db, content_hash)
    if cached is not None:
        logger.info("Using cached extraction for %s", pdf_path)
        return cached

    try:
        if is_digital_pdf(pdf_path):
            text = extract_text_from_pdf(pdf_path)
            if text.strip():
                records = extract_from_text(text)
            else:
                ocr_texts, images = extract_text_via_ocr(pdf_path)
                records = _extract_via_ocr_or_vision(ocr_texts, images)
        else:
            ocr_texts, images = extract_text_via_ocr(pdf_path)
            records = _extract_via_ocr_or_vision(ocr_texts, images)

        _write_raw_output(db, doc_id, records)
        valid, invalid = _validate(records)

        doc = db.query(SourceDocuments).filter(SourceDocuments.id == doc_id).first()
        if doc:
            doc.status = "validation_error" if invalid and not valid else "extracted"
            db.commit()

        return valid

    except Exception as exc:
        logger.error("Extraction failed for %s: %s", pdf_path, exc)
        doc = db.query(SourceDocuments).filter(SourceDocuments.id == doc_id).first()
        if doc:
            doc.status = "extraction_failed"
            db.commit()
        return []


def _extract_via_ocr_or_vision(ocr_texts: list[str], images: list) -> list[PriceRecord]:
    all_records: list[PriceRecord] = []
    for text, image in zip(ocr_texts, images):
        if text.strip():
            all_records.extend(extract_from_text(text))
        else:
            all_records.extend(extract_from_image(image))
    return all_records
