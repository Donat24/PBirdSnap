import base64
import secrets
from typing import Callable, Type

from fastapi import APIRouter, HTTPException, Request, Response
from fastapi.params import Depends
from fastapi.routing import APIRoute
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from sqlalchemy import select
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm.exc import NoResultFound

from database.model import User
from database.util import DBUtil

security = HTTPBasic()

def get_current_username(
    credentials: HTTPBasicCredentials = Depends(security),
) -> str:
    return credentials.username

def BasicAuthRoute(sessionmaker: async_sessionmaker[AsyncSession], db_util:DBUtil) -> Type[APIRoute]:
    
    class _BasicAuthRoute(APIRoute):
        def get_route_handler(self) -> Callable:

            original_route_handler = super().get_route_handler()

            async def custom_route_handler(request: Request) -> Response:
                async with sessionmaker() as session:
                    
                    #get credentials
                    header = request.headers.get("Authorization", "")

                    try:
                        scheme, credentials = header.strip().split(" ")
                    except Exception as e:
                        raise HTTPException(status_code=401, detail="UNAUTORIZED") from e

                    if scheme.lower() != "basic":
                        raise HTTPException(status_code=401, detail="UNAUTORIZED")

                    #read credentials
                    username, _, password = base64.b64decode(credentials).decode("utf-8").partition(":")
                    password = db_util.hash_func(password)

                    #read db
                    try:
                        user = (await session.execute(select(User).where(User.name == username))).scalar_one()
                        correct_username = user.name
                        correct_password = user.password_hash
                    
                    except NoResultFound as e:
                        correct_username = ""
                        correct_password = ""
                    
                    #compare
                    is_correct_username = secrets.compare_digest(username, correct_username)
                    is_correct_password = secrets.compare_digest(password, correct_password)
                    
                    if not (is_correct_username and is_correct_password):
                        raise HTTPException(status_code=401, detail="UNAUTORIZED")
                
                return await original_route_handler(request)

            return custom_route_handler
    
    return _BasicAuthRoute