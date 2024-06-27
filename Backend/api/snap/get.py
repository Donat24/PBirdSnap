import datetime
from typing import Optional
from urllib.parse import urljoin, urlparse

from fastapi import APIRouter, Depends, FastAPI, HTTPException, Query, Request
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import (AsyncEngine, AsyncSession,
                                    async_sessionmaker, create_async_engine)
from sqlalchemy.orm import joinedload
from sqlalchemy.orm.exc import NoResultFound

from api.dependency.basic_auth import BasicAuthRoute, get_current_username
from database.model import BirdSnap, BirdSnapLike, Device, User
from database.util import DBUtil
from schema import response


def CreateGetEndpoint(
    app: FastAPI,
    sessionmaker: async_sessionmaker[AsyncSession],
    db_util: DBUtil,
):
    router = APIRouter(
        route_class=BasicAuthRoute(sessionmaker, db_util)
    )
    @router.get(
       path="/snap/get",
        summary="returns one bird snap",
        description="returns one bird snap",
        tags=["snap"],
    )
    async def getAll(
        request: Request,

        # basic auth
        auth_username: str = Depends(get_current_username),

        # other params
        id: int = 0,
    ) -> response.BirdSnap:
        async with sessionmaker() as session:
            try:
                user = (await session.execute(select(User).where(User.name == auth_username))).scalar_one()
            except Exception as e:
                raise HTTPException(status_code=400, detail="unknown user") from e


            try:
                query = select(BirdSnap).where(BirdSnap.id == id)
                birdsnap = (await session.execute(
                    query.options(
                        joinedload(BirdSnap.device)
                    ).options(
                        joinedload(BirdSnap.users_liked)
                    ).options(
                        joinedload(BirdSnap.images)
                    )
                )).scalar_one()
            
            except NoResultFound as e:
                raise HTTPException(
                    status_code=400, detail="birdsnap not available"
                ) from e

            if (not birdsnap.is_public) and birdsnap.device.owner.id != user.id:
                raise HTTPException(status_code=400, detail="birdsnap not available")
            
            return response.BirdSnap(
                id = birdsnap.id,
                device_info=response.DeviceInfo(
                    id=birdsnap.device.id,
                    name=birdsnap.device.name,
                    longitude=birdsnap.device.longitude if birdsnap.device.is_info_public else None,
                    latitude=birdsnap.device.latitude if birdsnap.device.is_info_public else None,
                ),
                user_info=response.UserInfo(
                    id=birdsnap.device.owner.id,
                    name=birdsnap.device.owner.name
                ),
                like_info=response.LikeInfo(
                    is_liked=user.id in [user.id for user in birdsnap.users_liked],
                    likes=len(birdsnap.users_liked),
                    users=[response.UserInfo(id = user.id, name= user.name) for user in birdsnap.users_liked]
                ),
                is_public=birdsnap.is_public,
                snap_time=birdsnap.snap_time,
                images=[response.BirdSnapImage(
                    id=image.id,
                ) for image in birdsnap.images],
                bird_species=birdsnap.bird_species
            )

    app.include_router(router)

    
