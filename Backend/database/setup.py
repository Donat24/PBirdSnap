import asyncio
import urllib
from typing import Tuple

from sqlalchemy.ext.asyncio import (AsyncEngine, AsyncSession,
                                    async_sessionmaker, create_async_engine)

from config.config import Config
from database.model import Base


def create_engine_sessionmaker(
    config: Config,
) -> Tuple[AsyncEngine, async_sessionmaker[AsyncSession]]:
    url = f"postgresql+asyncpg://{config.db.user}:{urllib.parse.quote_plus(config.db.password)}@{config.db.host}:{config.db.port}/{config.db.db}"
    engine = create_async_engine(url)
    sessionmaker = async_sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return engine, sessionmaker


async def create_schema(engine: AsyncEngine) -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
