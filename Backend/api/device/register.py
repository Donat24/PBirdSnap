import datetime
import os
import uuid
from pathlib import Path
from typing import Optional
from uuid import UUID

import magic
from fastapi import (APIRouter, BackgroundTasks, Depends, FastAPI, File,
                     Header, HTTPException, UploadFile)
from pydantic import BaseModel, field_validator
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import (AsyncEngine, AsyncSession,
                                    async_sessionmaker, create_async_engine)
from sqlalchemy.orm.exc import MultipleResultsFound, NoResultFound

from api.dependency.basic_auth import BasicAuthRoute, get_current_username
from config.config import Config
from database.model import (BirdSnap, BirdSnapImage, BirdSnapStatus, Device,
                            DeviceType, User)
from database.util import DBUtil
from schema.response import ResponseStatus, StatusResponse
from storage.storage import BadFileTypeError, Storage


class RegisterDeviceRequestBody(BaseModel):
    id: uuid.UUID
    type: DeviceType
    name: str
    public_by_default: bool
    is_info_public: bool
    longitude:Optional[float]
    latitude:Optional[float]


def CreateRegisterDeviceEndpoint(
    app: FastAPI,
    sessionmaker: async_sessionmaker[AsyncSession],
    db_util: DBUtil,
):
    router = APIRouter(
        route_class=BasicAuthRoute(sessionmaker, db_util)
    )
    @router.post(
        path="/device/register",
        summary="register a device",
        description="register a device",
        tags=["device"],
    )
    async def register(
        body: RegisterDeviceRequestBody,
        username: str = Depends(get_current_username),
        ) -> StatusResponse:
        async with sessionmaker() as session:
            try:
                user = (await session.execute(select(User).where(User.name == username))).scalar_one()
            except Exception as e:
                raise HTTPException(status_code=400, detail="unknown user") from e

            try:
                device = Device(
                    id = body.id,
                    type = body.type,
                    name = body.name,
                    owner_id = user.id,
                    public_by_default = body.public_by_default,
                    is_info_public = body.is_info_public,
                    longitude = body.longitude,
                    latitude = body.latitude,
                )

                session.add(device)
                await session.commit()
                
                return StatusResponse(
                    status=ResponseStatus.OK,
                    details="device registered"
                )
            
            except IntegrityError as e:
                raise HTTPException(
                    status_code=400, detail="device already registered"
                ) from e

    app.include_router(router)

    