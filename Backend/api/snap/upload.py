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
from database.model import BirdSnap, BirdSnapImage, BirdSnapStatus, Device
from database.util import DBUtil
from schema.response import ResponseStatus, StatusResponse
from storage.storage import BadFileTypeError, Storage


def CreateUploadEndpoint(
    app: FastAPI,
    sessionmaker: async_sessionmaker[AsyncSession],
    db_util: DBUtil,
    storage: Storage,
    classifier:Classifier,
):
    router = APIRouter(
        route_class=BasicAuthRoute(sessionmaker, db_util)
    )
    @router.post(
        path="/snap/upload",
        summary="upload a birdsnap",
        description="upload a birdsnap",
        tags=["snap"],
    )
    async def upload(
        background_tasks: BackgroundTasks,
        # params
        _: str = Depends(get_current_username),
        device_id: UUID = Header(),
        image: UploadFile = File(description="Image"),
        snap_time: Optional[datetime.datetime] = Header(
            alias="Date",
            default=None,
            include_in_schema=False,
        ),
    ) -> StatusResponse:
        async with sessionmaker() as session:

            # Set snap time
            if snap_time is None:
                snap_time = datetime.datetime.now()

            # save file
            try:
                storage_path = storage.save_birdsnapimage(
                    device_id,
                    image.file,
                    snap_time,
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
            birdsnap = BirdSnap(
                is_public=device.public_by_default,
                status=BirdSnapStatus.PROCESSING,
                device_id=device.id,
                snap_time=snap_time,
            )
            session.add(birdsnap)
            await session.commit()
            await session.refresh(birdsnap)

            birdsnapimage = BirdSnapImage(birdsnap_id=birdsnap.id, path=storage_path)
            session.add(birdsnapimage)
            await session.commit()
            await session.refresh(birdsnapimage)

            background_tasks.add_task(process_birdsnap, birdsnapimage.id)

            return StatusResponse(
                status=ResponseStatus.OK,
                details="birdsnap processing scheduled",
            )
    app.include_router(router)

    async def process_birdsnap(image_id: int):
        async with sessionmaker() as session:
            birdsnapimage = (
                await session.execute(select(BirdSnapImage).where(BirdSnapImage.id == image_id))
            ).scalar_one()
            birdsnap = birdsnapimage.birdsnap

            try:
                storage_path = storage.get_birdsnapimage(birdsnapimage.path)
            except Exception:
                logging.error(f"unable to get storage path for image with id:{birdsnapimage.id}")
                # cleanup
                birdsnap.status = BirdSnapStatus.DELETED
                return
            
            try:
                bird_species = classifier(storage_path)
            except Exception as e:
                # in case of an error
                # set image as available
                logging.error(f"unable to determan bird species for image with id:{birdsnapimage.id}",exc_info=e)
                birdsnap.status = BirdSnapStatus.CLASSIFICATION_FAILED
                await session.commit()
                return

            if bird_species:
                # if birds where detected
                birdsnap.bird_species = bird_species
                birdsnap.status = BirdSnapStatus.AVAILABLE
                await session.commit()
                return
            
            else:
                birdsnap = birdsnapimage.birdsnap
                birdsnap.status = BirdSnapStatus.NO_BIRD_DETECTED
                await session.commit()
                return


