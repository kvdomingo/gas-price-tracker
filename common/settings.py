from pathlib import Path
from typing import Literal

from pydantic import HttpUrl, PostgresDsn, SecretStr
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PYTHON_ENV: Literal["development", "production"] = "development"
    BASE_DIR: Path = Path(__file__).resolve().parent.parent
    DATABASE_URL: PostgresDsn
    AUTH_ENABLED: bool = False
    API_KEYS: list[str] = []

    DOE_LISTING_BASE_URL: str = "doe.gov.ph"
    DOE_LISTING_BASE_PATH: str = "articles/group/liquid-fuels"
    DOE_LISTING_BASE_PARAMS: dict[str, str] = {
        "maincat": "Retail Pump Prices",
        "subcategory": "NCR Pump Prices",
        "display_type": "Card",
    }
    DOE_PDF_BASE_URL: str = "prod-cms.doe.gov.ph"
    DOE_PDF_BASE_PATH: str = "documents/d"

    MINIO_ENDPOINT_URL: HttpUrl
    MINIO_ACCESS_KEY: SecretStr
    MINIO_SECRET_KEY: SecretStr
    MINIO_BUCKET: str


settings = Settings()  # ty:ignore[missing-argument]
