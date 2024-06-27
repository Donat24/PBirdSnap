import datetime
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import (AsyncEngine, AsyncSession,
                                    async_sessionmaker, create_async_engine)
from starlette.exceptions import HTTPException as StarletteHTTPException

from schema.response import ResponseStatus, StatusResponse


def CreateHTTPExceptionHandler(app: FastAPI) -> None:
    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request, exc):
        return JSONResponse(
            StatusResponse(
                status=ResponseStatus.FAILURE, details=str(exc.detail)
            ).model_dump(),
            status_code=exc.status_code,
        )


def CreateRequestValidationExceptionHandler(app: FastAPI) -> None:
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request, exc):
        return JSONResponse(
            StatusResponse(
                status=ResponseStatus.FAILURE, details=str(exc)
            ).model_dump(),
            status_code=400,
        )
