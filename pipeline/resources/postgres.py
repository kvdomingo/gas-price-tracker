from contextlib import asynccontextmanager, contextmanager
from typing import AsyncGenerator, Generator

from dagster import ConfigurableResource
from loguru import logger
from pydantic import Field
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import Session, sessionmaker

from common.settings import settings


class PostgresResource(ConfigurableResource):
    connection_url: str = Field(
        description="SQLAlchemy connection string for PostgreSQL"
    )

    @contextmanager
    def _get_session(self) -> Generator[Session, None, None]:
        engine = create_engine(
            self.connection_url.replace("postgresql://", "postgresql+psycopg2://"),
            echo=settings.PYTHON_ENV == "development",
        )
        session_maker = sessionmaker(bind=engine)
        session = None

        try:
            session = session_maker()
            yield session
        finally:
            if session is not None:
                session.close()
            engine.dispose()

    @asynccontextmanager
    async def _get_async_session(self) -> AsyncGenerator[AsyncSession, None]:
        logger.debug(self.connection_url)

        engine = create_async_engine(
            self.connection_url.replace("postgresql://", "postgresql+asyncpg://"),
            echo=settings.PYTHON_ENV == "development",
        )

        session_maker = async_sessionmaker(bind=engine)
        session = None

        try:
            session = session_maker()
            yield session
        finally:
            if session is not None:
                await session.close()
            await engine.dispose()

    @contextmanager
    def get_connection(self) -> Generator[Session, None, None]:
        with self._get_session() as session:
            try:
                yield session
            except Exception:
                session.rollback()
                raise

    @asynccontextmanager
    async def get_async_connection(self) -> AsyncGenerator[AsyncSession, None]:
        async with self._get_async_session() as session:
            try:
                yield session
            except Exception:
                await session.rollback()
                raise
