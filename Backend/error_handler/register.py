from fastapi import FastAPI

from error_handler.error_handler import CreateHTTPExceptionHandler


def register(app: FastAPI):
    CreateHTTPExceptionHandler(app)
    CreateHTTPExceptionHandler(app)
