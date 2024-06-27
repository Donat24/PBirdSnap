import secrets

from fastapi import APIRouter, HTTPException, Request, Response
from fastapi.responses import JSONResponse, PlainTextResponse


def CreateApiKeyMiddleware(key:str):
    async def middleware(request: Request, call_next) -> Response:
        header = request.headers.get("API-KEY", "")
        if not secrets.compare_digest(key, header):
            return PlainTextResponse(
                status_code=401,
                content="FORBIDDEN",
            )
        response = await call_next(request)
        return response
    return middleware