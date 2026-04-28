from functools import lru_cache
from pathlib import Path

from pydantic import PostgresDsn, field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    BASE_DIR: Path = Path(__file__).resolve().parent.parent
    DATABASE_URL: PostgresDsn
    AUTH_ENABLED: bool = False
    API_KEYS: list[str] = []

    @field_validator("DATABASE_URL", mode="before")
    def validate_database_url_async(cls, v: str) -> str:
        return v.replace("postgresql://", "postgresql+asyncpg://")


@lru_cache
def _get_settings() -> Settings:
    return Settings()  # ty:ignore[missing-argument]


settings = _get_settings()
