import datetime
import os
from pathlib import Path
from typing import Optional
from uuid import UUID

import magic
from fastapi import (APIRouter, BackgroundTasks, Depends, FastAPI, File,
                     Header, HTTPException, UploadFile)
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import (AsyncEngine, AsyncSession,
                                    async_sessionmaker, create_async_engine)
from sqlalchemy.orm import joinedload
from sqlalchemy.orm.exc import NoResultFound

from api.dependency.basic_auth import BasicAuthRoute, get_current_username
from config.config import Config
from database.model import (BirdSnap, BirdSnapImage, BirdSnapStatus, Device,
                            User)
from database.util import DBUtil
from schema.response import ResponseStatus, StatusResponse
from storage.storage import BadFileTypeError, Storage


def CreateImageEndpoint(
    app: FastAPI, sessionmaker: async_sessionmaker[AsyncSession],  db_util: DBUtil, storage: Storage
):
    router = APIRouter(
        route_class=BasicAuthRoute(sessionmaker, db_util)
    )
    @router.get(
        path="/snap/image",
        summary="download birdsnap image",
        description="download birdsnap image",
        tags=["snap"],
        response_class=FileResponse
    )
    async def image(
        # basic auth
        auth_username: str = Depends(get_current_username),
        
        # other params
        id: int = 0,
    ) -> FileResponse:
        async with sessionmaker() as session:

            try:
                user = (await session.execute(select(User).where(User.name == auth_username))).scalar_one()
            except Exception as e:
                raise HTTPException(status_code=400, detail="unknown user") from e
            
            
            try:
                query = select(BirdSnapImage).where(BirdSnapImage.id == id)
                image = (await session.execute(
                    query.options(
                        joinedload(BirdSnapImage.birdsnap)
                    )
                )).scalar_one()
            
            except NoResultFound as e:
                raise HTTPException(
                    status_code=400, detail="image not available"
                ) from e
            
            if (not image.birdsnap.is_public) and image.birdsnap.device.owner.id != user.id:
                raise HTTPException(
                    status_code=400, detail="image not available"
                )
            
            try:
                path = storage.get_birdsnapimage(image.path)
                if path.suffix.lower() in ["jpg", "jpeg"]:
                    media_type = "image/jpeg"
                elif path.suffix.lower() in ["png"]:
                    media_type = "image/png"
                else:
                    media_type = None
                return FileResponse(path=path, media_type=media_type)
            
            except Exception as e:
                raise HTTPException(
                    status_code=400, detail="image not available"
                ) from e            
    
    app.include_router(router)
            

            
