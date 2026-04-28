from typing import AsyncGenerator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from api.settings import settings

_engine = create_async_engine(settings.DATABASE_URL, pool_pre_ping=True)
_SessionLocal = async_sessionmaker(bind=_engine, autoflush=False, autocommit=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    db = _SessionLocal()
    try:
        yield db
    finally:
        await db.close()


async def check_db_connection() -> bool:
    try:
        async with _engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False
