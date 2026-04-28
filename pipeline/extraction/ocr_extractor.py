from PIL import Image
from pdf2image import convert_from_path
import pytesseract


def render_pdf_to_images(pdf_path: str, dpi: int = 300) -> list[Image.Image]:
    return convert_from_path(pdf_path, dpi=dpi)


def ocr_page(image: Image.Image) -> str:
    return pytesseract.image_to_string(image, lang="eng")


def extract_text_via_ocr(pdf_path: str) -> tuple[list[str], list[Image.Image]]:
    """Returns (ocr_texts, page_images). ocr_texts[i] may be empty if OCR failed."""
    images = render_pdf_to_images(pdf_path)
    texts = [ocr_page(img) for img in images]
    return texts, images
