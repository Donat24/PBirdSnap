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
from inference_sdk import InferenceHTTPClient
from sqlalchemy import select
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
from schema.response import ResponseStatus, StatusResponse
from storage.storage import BadFileTypeError, Storage


def CreateUploadTestImageEndpoint(
    app: FastAPI,
    sessionmaker: async_sessionmaker[AsyncSession],
    db_util: DBUtil,
    storage: Storage,
):
    router = APIRouter(
        route_class=BasicAuthRoute(sessionmaker, db_util)
    )
    @router.post(
        path="/device/upload-test-image",
        summary="upload an test-image",
        description="upload an test-image",
        tags=["device"],
    )
    async def upload_test_image(
        _: str = Depends(get_current_username),
        device_id: UUID = Header(),
        image: UploadFile = File(description="Image"),
        curr_time: Optional[datetime.datetime] = Header(
            alias="Date",
            default=None,
            include_in_schema=False,
        ),
    ) -> StatusResponse:
        async with sessionmaker() as session:

            # Set snap time
            if curr_time is None:
                curr_time = datetime.datetime.now()

            # checks mime
            if not image.content_type in ["image/jpeg", "image/png"]:
                raise HTTPException(
                    status_code=415, detail="only supports jpeg and png"
                )

            try:
                device = (await session.execute(select(Device).where(Device.id == device_id))).scalar_one()
            except Exception as e:
                raise HTTPException(status_code=400, detail="unknown device") from e

            # save file
            try:
                storage_path = storage.save_birdsnapimage(
                    device_id,
                    image.file,
                    curr_time,
                )
            except BadFileTypeError as e:
                raise HTTPException(
                    status_code=415, detail="only supports jpeg and png"
                ) from e

            try:
                device = (
                    await session.execute(select(Device).where(Device.id == device_id))
                ).scalar_one()
            except NoResultFound as e:
                raise HTTPException(status_code=415, detail="unknown device") from e

            # create db entry
            testimage = TestImage(
                creation_time=curr_time,
                device_id=device.id,
                path=storage_path
            )
            session.add(testimage)
            await session.commit()
            await session.refresh(testimage)

            return StatusResponse(
                status=ResponseStatus.OK,
                details="test-image uploaded",
            )
    app.include_router(router)