import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from database.setup import create_schema


def create_lifespan(engine: AsyncEngine):
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        await create_schema(engine)
        yield

    return lifespan
