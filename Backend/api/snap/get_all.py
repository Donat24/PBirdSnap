import datetime
from typing import Optional
from urllib.parse import urljoin, urlparse

from fastapi import APIRouter, Depends, FastAPI, HTTPException, Query, Request
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import (AsyncEngine, AsyncSession,
                                    async_sessionmaker, create_async_engine)
from sqlalchemy.orm import joinedload

from api.dependency.basic_auth import BasicAuthRoute, get_current_username
from database.model import BirdSnap, BirdSnapLike, Device, User
from database.util import DBUtil
from schema import response


def CreateGetAllEndpoint(
    app: FastAPI,
    sessionmaker: async_sessionmaker[AsyncSession],
    db_util: DBUtil,
):
    router = APIRouter(
        route_class=BasicAuthRoute(sessionmaker, db_util)
    )
    @router.get(
       path="/snap/get-all",
        summary="returns all available bird snaps",
        description="returns all available bird snaps",
        tags=["snap"],
    )
    async def getAll(
        request: Request,

        # basic auth
        auth_username: str = Depends(get_current_username),

        # other params
        username: Optional[int] = None,
        since: Optional[datetime.datetime] = None,
        last:Optional[int] = None,
        offset: Optional[int] = None,
        limit: Optional[int] = None,
    ) -> response.PaginatedResult[response.BirdSnap]:
        async with sessionmaker() as session:
            try:
                user = (await session.execute(select(User).where(User.name == auth_username))).scalar_one()
            except Exception as e:
                raise HTTPException(status_code=400, detail="unknown user") from e


            if username is not None and username != user.name:
                query = select(BirdSnap).join(BirdSnap.device).join(Device.owner).where(
                    User.name == username
                ).where(
                    BirdSnap.is_public == True
                )
            else:
                query = select(BirdSnap).join(BirdSnap.device).join(Device.owner).where(
                    User.name == user.name
                )

            if since is not None:
                query = query.where(
                    BirdSnap.snap_time > since
                )
            
            if last is not None:
                query = query.limit(last)
            
            query = query.order_by(BirdSnap.snap_time)
            total_count = (await session.execute(
                select(func.count()).select_from(query.subquery())
            )).scalar_one()

            if limit is not None:
                query=select(query.subquery()).limit(limit)
            
                if offset is not None:
                    query = query.offset(offset)
            elif offset is not None:
                raise HTTPException(status_code=400, detail="offset without limit not supported")
            
            birdsnaps = (
                await session.execute(query.options(
                    joinedload(BirdSnap.device)
                ).options(
                    joinedload(BirdSnap.users_liked)
                ).options(
                    joinedload(BirdSnap.images)
                ))
            ).unique().scalars().all()

            baseurl = urljoin(str(request.url), urlparse(str(request.url)).path)
            if limit is not None and len(birdsnaps) < total_count:
                #TODO
                next_url = baseurl
                prev_url = baseurl
            else:
                next_url = None
                prev_url = None
            
            return response.PaginatedResult[response.BirdSnap](
                page=response.Page(
                    next  = next_url,
                    prev  = prev_url,
                    index = offset//limit if (limit is not None and limit is not 0 and offset is not None) else 0,
                    page_count=len(birdsnaps),
                    total_count=total_count,
                ),
                results=[
                    response.BirdSnap(
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
                    ) for birdsnap in birdsnaps
                ]
            )

    app.include_router(router)

    
