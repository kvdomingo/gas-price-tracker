import json
import logging
import os
import time
from dataclasses import dataclass
from datetime import date

from google import genai
from google.genai import types
from PIL import Image

logger = logging.getLogger(__name__)

_PROMPT = """
You are given content extracted from a Philippine Department of Energy (DOE) weekly retail fuel price publication.
Extract all price records and return them as a JSON array. Each object must have exactly these fields:
- fuel_type: string (e.g. "diesel", "gasoline", "kerosene", "lpg")
- price_php_per_liter: number (retail pump price in PHP per litre)
- location_string: string (city or municipality name as written in the document)
- effective_date: string (ISO 8601 date, e.g. "2024-01-05")

Return ONLY valid JSON. If you cannot extract records, return an empty array [].
"""

_MAX_RETRIES = 3


@dataclass
class PriceRecord:
    fuel_type: str
    price_php_per_liter: float
    location_string: str
    effective_date: date


def _get_client() -> genai.Client:
    return genai.Client(api_key=os.environ["GEMINI_API_KEY"])


def _parse_response(text: str) -> list[PriceRecord]:
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[-1].rsplit("```", 1)[0]
    records = json.loads(text)
    return [
        PriceRecord(
            fuel_type=r["fuel_type"],
            price_php_per_liter=float(r["price_php_per_liter"]),
            location_string=r["location_string"],
            effective_date=date.fromisoformat(r["effective_date"]),
        )
        for r in records
    ]


def extract_from_text(text: str) -> list[PriceRecord]:
    client = _get_client()
    for attempt in range(_MAX_RETRIES):
        try:
            response = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=[_PROMPT, text],
                config=types.GenerateContentConfig(
                    response_mime_type="application/json"
                ),
            )
            return _parse_response(response.text or "[]")
        except Exception as exc:
            if attempt == _MAX_RETRIES - 1:
                logger.error(
                    "Gemini text extraction failed after %d retries: %s",
                    _MAX_RETRIES,
                    exc,
                )
                raise
            time.sleep(2**attempt)
    return []


def extract_from_image(image: Image.Image) -> list[PriceRecord]:
    client = _get_client()
    for attempt in range(_MAX_RETRIES):
        try:
            response = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=[_PROMPT, image],
                config=types.GenerateContentConfig(
                    response_mime_type="application/json"
                ),
            )
            return _parse_response(response.text or "[]")
        except Exception as exc:
            if attempt == _MAX_RETRIES - 1:
                logger.error(
                    "Gemini image extraction failed after %d retries: %s",
                    _MAX_RETRIES,
                    exc,
                )
                raise
            time.sleep(2**attempt)
    return []
