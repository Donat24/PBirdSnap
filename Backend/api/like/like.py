import datetime
import os
import uuid
from pathlib import Path
from typing import Optional
from uuid import UUID

import magic
from fastapi import (APIRouter, BackgroundTasks, Depends, FastAPI, File,
                     Header, HTTPException, Query, UploadFile)
from pydantic import BaseModel, field_validator
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import (AsyncEngine, AsyncSession,
                                    async_sessionmaker, create_async_engine)
from sqlalchemy.orm.exc import MultipleResultsFound, NoResultFound

from api.dependency.basic_auth import BasicAuthRoute, get_current_username
from config.config import Config
from database.model import (BirdSnap, BirdSnapImage, BirdSnapLike,
                            BirdSnapStatus, Device, DeviceType, User)
from database.util import DBUtil
from schema.response import ResponseStatus, StatusResponse
from storage.storage import BadFileTypeError, Storage


def CreateLikeEndpoint(
    app: FastAPI,
    sessionmaker: async_sessionmaker[AsyncSession],
    db_util: DBUtil,
):
    router = APIRouter(
        route_class=BasicAuthRoute(sessionmaker, db_util)
    )
    @router.post(
        path="/like/like",
        summary="like a birdsnap",
        description="like a birdsnap",
        tags=["like"],
    )
    async def like(
        birdsnap_id: int = Query(),
        username: str = Depends(get_current_username),
        ) -> StatusResponse:
        async with sessionmaker() as session:
            try:
                user = (await session.execute(select(User).where(User.name == username))).scalar_one()
            except Exception as e:
                raise HTTPException(status_code=400, detail="unknown user") from e

            try:
                birdsnap = (await session.execute(select(BirdSnap).where(BirdSnap.id == birdsnap_id))).scalar_one()
            except Exception as e:
                raise HTTPException(status_code=400, detail="unknown birdsnap") from e

            if (not birdsnap.pubic) and (birdsnap.device.owner.name != username):
                raise HTTPException(status_code=400, detail="birdsnap is not public")
            
            try:
                like = BirdSnapLike(
                    birdsnap_id = birdsnap.id,
                    user_id = user.id
                )

                session.add(like)
                await session.commit()
            
                return StatusResponse(
                    status=ResponseStatus.OK,
                    details=f"birdsnap {birdsnap_id} liked"
                )
            
            except IntegrityError:
                
                await session.rollback()

                return StatusResponse(
                    status=ResponseStatus.OK,
                    details=f"birdsnap {birdsnap_id} already liked"
                )

    app.include_router(router)

    