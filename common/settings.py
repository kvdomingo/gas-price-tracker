from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import PostgresDsn
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PYTHON_ENV: Literal["development", "production"] = "development"
    BASE_DIR: Path = Path(__file__).resolve().parent.parent
    DATABASE_URL: PostgresDsn
    AUTH_ENABLED: bool = False
    API_KEYS: list[str] = []


@lru_cache
def _get_settings() -> Settings:
    return Settings()  # ty:ignore[missing-argument]


settings = _get_settings()
