from fastapi import FastAPI
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from api.auth.failed import CreateAuthFailed
from api.device.register import CreateRegisterDeviceEndpoint
from api.like.like import CreateLikeEndpoint
from api.like.unlike import CreateUnlikeEndpoint
from api.snap.get import CreateGetEndpoint
from api.snap.get_all import CreateGetAllEndpoint
from api.snap.image import CreateImageEndpoint
from api.snap.upload import CreateUploadEndpoint
from api.user.create import CreateCreateUserEndpoint
from database.util import DBUtil
from storage.storage import Storage


def register(
    app: FastAPI,
    sessionmaker: async_sessionmaker[AsyncSession],
    db_util: DBUtil,
    storage: Storage,
):
    CreateAuthFailed(app)
    CreateGetEndpoint(app, sessionmaker, db_util)
    CreateGetAllEndpoint(app, sessionmaker, db_util)
    CreateUploadEndpoint(app, sessionmaker, storage)
    CreateImageEndpoint(app, sessionmaker, db_util, storage)
    CreateCreateUserEndpoint(app, sessionmaker, db_util)
    CreateRegisterDeviceEndpoint(app, sessionmaker, db_util)
    CreateLikeEndpoint(app, sessionmaker, db_util)
    CreateUnlikeEndpoint(app, sessionmaker, db_util)
