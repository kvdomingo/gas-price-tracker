"""Integration tests for the extraction pipeline using fixture PDFs with mocked Gemini."""

from datetime import date
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

FIXTURES_DIR = Path(__file__).parent / "fixtures" / "pdfs"


@pytest.fixture()
def mock_gemini_records():
    from extraction.gemini_client import PriceRecord

    return [
        PriceRecord(
            fuel_type="diesel",
            price_php_per_liter=62.5,
            location_string="Makati City",
            effective_date=date(2024, 1, 5),
        ),
        PriceRecord(
            fuel_type="gasoline",
            price_php_per_liter=75.0,
            location_string="City of Manila",
            effective_date=date(2024, 1, 5),
        ),
    ]


@pytest.mark.skipif(
    not any(FIXTURES_DIR.glob("*.pdf")),
    reason="No PDF fixtures available — add PDFs to tests/fixtures/pdfs/",
)
class TestExtractionPipelineWithFixtures:
    def test_digital_pdf_extraction(self, mock_gemini_records, tmp_path):
        from extraction.pipeline import extract_document

        pdf_path = next(FIXTURES_DIR.glob("digital_*.pdf"), None)
        if pdf_path is None:
            pytest.skip("No digital PDF fixture found")

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        with patch(
            "extraction.pipeline.extract_from_text", return_value=mock_gemini_records
        ):
            records = extract_document(mock_db, "test-id", str(pdf_path), "abc123")
            assert len(records) > 0
            assert all(10 <= r.price_php_per_liter <= 500 for r in records)

    def test_scanned_pdf_extraction(self, mock_gemini_records, tmp_path):
        from extraction.pipeline import extract_document

        pdf_path = next(FIXTURES_DIR.glob("scanned_*.pdf"), None)
        if pdf_path is None:
            pytest.skip("No scanned PDF fixture found")

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        with patch(
            "extraction.pipeline.extract_from_image", return_value=mock_gemini_records
        ):
            records = extract_document(mock_db, "test-id", str(pdf_path), "def456")
            assert len(records) > 0

    def test_price_validation_filters_outliers(self, tmp_path):
        from extraction.gemini_client import PriceRecord
        from extraction.pipeline import extract_document

        pdf_path = next(FIXTURES_DIR.glob("*.pdf"), None)
        if pdf_path is None:
            pytest.skip("No PDF fixture found")

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        outlier_records = [
            PriceRecord(
                fuel_type="diesel",
                price_php_per_liter=9999.0,  # Out of range
                location_string="Makati City",
                effective_date=date(2024, 1, 5),
            ),
        ]

        with patch(
            "extraction.pipeline.extract_from_text", return_value=outlier_records
        ):
            records = extract_document(mock_db, "test-id", str(pdf_path), "ghi789")
            assert len(records) == 0
