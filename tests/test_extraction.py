from unittest.mock import MagicMock, patch


class TestPdfDetector:
    def test_digital_pdf_with_text_returns_true(self):
        from extraction.pdf_detector import is_digital_pdf

        mock_page = MagicMock()
        mock_page.extract_text.return_value = (
            "Retail Pump Prices NCR Effective January 2024" * 3
        )
        mock_pdf = MagicMock()
        mock_pdf.__enter__ = MagicMock(return_value=mock_pdf)
        mock_pdf.__exit__ = MagicMock(return_value=False)
        mock_pdf.pages = [mock_page]

        with patch("extraction.pdf_detector.pdfplumber.open", return_value=mock_pdf):
            assert is_digital_pdf("fake.pdf") is True

    def test_scanned_pdf_with_no_text_returns_false(self):
        from extraction.pdf_detector import is_digital_pdf

        mock_page = MagicMock()
        mock_page.extract_text.return_value = ""
        mock_pdf = MagicMock()
        mock_pdf.__enter__ = MagicMock(return_value=mock_pdf)
        mock_pdf.__exit__ = MagicMock(return_value=False)
        mock_pdf.pages = [mock_page]

        with patch("extraction.pdf_detector.pdfplumber.open", return_value=mock_pdf):
            assert is_digital_pdf("fake.pdf") is False


class TestTextExtractor:
    def test_extracts_text_from_pages(self):
        from extraction.text_extractor import extract_text_from_pdf

        mock_page1 = MagicMock()
        mock_page1.extract_text.return_value = "Page 1 content"
        mock_page2 = MagicMock()
        mock_page2.extract_text.return_value = "Page 2 content"
        mock_pdf = MagicMock()
        mock_pdf.__enter__ = MagicMock(return_value=mock_pdf)
        mock_pdf.__exit__ = MagicMock(return_value=False)
        mock_pdf.pages = [mock_page1, mock_page2]

        with patch("extraction.text_extractor.pdfplumber.open", return_value=mock_pdf):
            result = extract_text_from_pdf("fake.pdf")
            assert "Page 1 content" in result
            assert "Page 2 content" in result
