


from fastapi import FastAPI, HTTPException

from schema.response import StatusResponse


def CreateAuthFailed(
    app: FastAPI,
):
    @app.get(
        path="/auth/failed",
        include_in_schema=False,
    )
    async def failed() -> StatusResponse:
        raise HTTPException(
            status_code=401, detail="api key missing"
        )