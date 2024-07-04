import datetime
import logging
import os
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
from fastapi.responses import FileResponse
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm.exc import NoResultFound

from api.dependency.basic_auth import BasicAuthRoute, get_current_username
from bird_classifier.classifier import Classifier
from database.model import (
    BirdSnap,
    BirdSnapImage,
    BirdSnapStatus,
    Device,
    TestImage,
    User,
)
from database.util import DBUtil
from storage.storage import Storage


def CreateGetTestImageEndpoint(
    app: FastAPI,
    sessionmaker: async_sessionmaker[AsyncSession],
    db_util: DBUtil,
    storage: Storage,
):
    router = APIRouter(
        route_class=BasicAuthRoute(sessionmaker, db_util)
    )
    @router.get(
        path="/device/get-test-image",
        summary="get a test-image",
        description="get a test-image",
        tags=["device"],
    )
    async def get_test_image(
        device_id: UUID = Header(),
        username: str = Depends(get_current_username),
    ) -> FileResponse:
        async with sessionmaker() as session:
            try:
                user = (await session.execute(select(User).where(User.name == username))).scalar_one()
            except Exception as e:
                raise HTTPException(status_code=400, detail="unknown user") from e

            try:
                device = (await session.execute(select(Device).where(Device.id == device_id))).scalar_one()
            except Exception as e:
                raise HTTPException(status_code=400, detail="unknown device") from e
            
            if device.owner.id != user.id:
                raise HTTPException(status_code=403, detail="user must be the owner of the device")
            
            try:
                query = select(TestImage).where(
                    TestImage.device_id == device_id
                ).order_by(
                    desc(TestImage.creation_time)
                ).limit(1)

                testimage = (await session.execute(query)).scalar_one()
            except Exception as e:
                raise HTTPException(status_code=400, detail="no test image")
            
            try:
                path = storage.get_birdsnapimage(testimage.path)

                if path.suffix.lower() in ["jpg", "jpeg"]:
                    media_type = "image/jpeg"
                elif path.suffix.lower() in ["png"]:
                    media_type = "image/png"
                else:
                    media_type = None
                
                return FileResponse(path=path, media_type=media_type)
            
            except Exception as e:
                raise HTTPException(
                    status_code=500, detail="image not available"
                ) from e 
    app.include_router(router)