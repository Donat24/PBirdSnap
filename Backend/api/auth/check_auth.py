import datetime
import os
import uuid
from pathlib import Path
from typing import Optional
from uuid import UUID

import magic
from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    FastAPI,
    File,
    Header,
    HTTPException,
    UploadFile,
)
from pydantic import BaseModel, field_validator
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm.exc import MultipleResultsFound, NoResultFound

from api.dependency.basic_auth import BasicAuthRoute, get_current_username
from config.config import Config
from database.model import (
    BirdSnap,
    BirdSnapImage,
    BirdSnapStatus,
    Device,
    DeviceType,
    User,
)
from database.util import DBUtil
from schema.response import ResponseStatus, StatusResponse
from storage.storage import BadFileTypeError, Storage


def CreateAuthCheckEndpoint(
    app: FastAPI,
    sessionmaker: async_sessionmaker[AsyncSession],
    db_util: DBUtil,
):
    router = APIRouter(
        route_class=BasicAuthRoute(sessionmaker, db_util)
    )
    @router.get(
        path="/auth/check",
        summary="check auth",
        description="check auth",
        tags=["auth"],
    )
    async def check(
        _: str = Depends(get_current_username),
        ) -> StatusResponse:
        return StatusResponse(
            status=ResponseStatus.OK,
            details="login works"
        )

    app.include_router(router)

    