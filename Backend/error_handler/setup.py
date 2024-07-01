from fastapi import FastAPI

from error_handler.error_handler import CreateHTTPExceptionHandler


def create_error_handler(app: FastAPI):
    CreateHTTPExceptionHandler(app)
    CreateHTTPExceptionHandler(app)
