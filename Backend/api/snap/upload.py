import datetime
import os
from pathlib import Path
from typing import Optional
from uuid import UUID

import magic
from fastapi import (BackgroundTasks, FastAPI, File, Header, HTTPException,
                     UploadFile)
from sqlalchemy import select
from sqlalchemy.ext.asyncio import (AsyncEngine, AsyncSession,
                                    async_sessionmaker, create_async_engine)
from sqlalchemy.orm.exc import NoResultFound

from config.config import Config
from database.model import BirdSnap, BirdSnapImage, BirdSnapStatus, Device
from schema.response import ResponseStatus, StatusResponse
from storage.storage import BadFileTypeError, Storage


def CreateUploadEndpoint(
    app: FastAPI, sessionmaker: async_sessionmaker[AsyncSession], storage: Storage
):
    @app.post(
        path="/snap/upload",
        summary="upload a birdsnap",
        description="upload a birdsnap",
        tags=["snap"],
    )
    async def upload(
        background_tasks: BackgroundTasks,
        # params
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

            # checks mime
            if not image.content_type in ["image/jpeg", "image/png"]:
                raise HTTPException(
                    status_code=415, detail="only supports jpeg and png"
                )

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

    async def process_birdsnap(image_id: int):
        async with sessionmaker() as session:
            birdsnapimage = (
                await session.execute(select(BirdSnapImage).where(BirdSnapImage.id == image_id))
            ).scalar_one()
            
            birdsnap = birdsnapimage.birdsnap
            birdsnap.bird_species = None
            birdsnap.status = BirdSnapStatus.AVAILABLE
            await session.commit()
