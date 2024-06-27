import datetime
import os
from pathlib import Path
from typing import Optional
from uuid import UUID

import magic
from fastapi import (BackgroundTasks, FastAPI, File, Header, HTTPException,
                     UploadFile)
from pydantic import BaseModel, field_validator
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import (AsyncEngine, AsyncSession,
                                    async_sessionmaker, create_async_engine)
from sqlalchemy.orm.exc import MultipleResultsFound, NoResultFound

from config.config import Config
from database.model import (BirdSnap, BirdSnapImage, BirdSnapStatus, Device,
                            User)
from database.util import DBUtil
from schema.response import ResponseStatus, StatusResponse
from storage.storage import BadFileTypeError, Storage


class CreateUserRequestBody(BaseModel):
    name: str
    email: str
    password: str

    @field_validator("name")
    @classmethod
    def validate_name(cls, name: str) -> str:
        if not name.isalnum():
            raise ValueError("only use numbers and characters for the username")
        return name

    @field_validator("password")
    @classmethod
    def validate_password(cls, password: str) -> str:
        if len(password) < 8 or len(password) > 30:
            raise ValueError("password must contain between 8 and 30 characters")
        return password


def CreateCreateUserEndpoint(
    app: FastAPI,
    sessionmaker: async_sessionmaker[AsyncSession],
    db_util: DBUtil,
):
    @app.post(
        path="/user/create",
        summary="creates an user",
        description="creates an user",
        tags=["user"],
    )
    async def create(body: CreateUserRequestBody) -> StatusResponse:
        async with sessionmaker() as session:
            user = User(
                password_hash=db_util.hash_func(body.password),
                name=body.name,
                email=body.email,
            )

            try:
                session.add(user)
                await session.commit()
            except IntegrityError as e:
                raise HTTPException(
                    status_code=400, detail="name or email already in use"
                ) from e

            return StatusResponse(
                status=ResponseStatus.OK,
                details="user created",
            )
