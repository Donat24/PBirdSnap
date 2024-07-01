
from typing import Callable

from fastapi import FastAPI

from config.config import Config
from middleware.api_key import CreateApiKeyMiddleware


class MiddlewareCreator:
    def __init__(self, config:Config):
        self.config = config
    
    def __call__(self, app:FastAPI) -> None:
        if self.config.security.api_key is not None:
            app.middleware("http")(CreateApiKeyMiddleware(self.config.security.api_key))