import pdfplumber


def is_digital_pdf(pdf_path: str, min_text_chars: int = 50) -> bool:
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text() or ""
            if len(text.strip()) >= min_text_chars:
                return True
    return False
