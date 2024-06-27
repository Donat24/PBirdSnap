import asyncio
import urllib
from typing import Tuple

from sqlalchemy.ext.asyncio import (AsyncEngine, AsyncSession,
                                    async_sessionmaker, create_async_engine)

from config.config import Config
from database.model import Base
from storage.storage import Storage


def create_storage(config: Config) -> Storage:
    storage = Storage(config.storage.path)
    storage.setup()
    return storage
