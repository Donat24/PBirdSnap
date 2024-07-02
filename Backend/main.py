import logging

from fastapi import FastAPI

from api.register import register as register_api
from config.config import Config, get_config
from database.setup import create_engine_sessionmaker
from database.util import create_db_util
from error_handler.setup import create_error_handler
from lifespan import create_lifespan
from storage.setup import create_storage


def setup(config:Config) -> FastAPI:
    
    # setup Logging
    logging.basicConfig(level=config.logging_level)

    # setup db
    engine, sessionmaker = create_engine_sessionmaker(config)
    db_util = create_db_util(config)

    # storage
    storage = create_storage(config)

    # lifespan
    lifespan = create_lifespan(engine)

    # setup fastapi
    app = FastAPI(lifespan=lifespan)
    create_error_handler(app)

    register_api(app, sessionmaker, db_util, storage)
    
    return app

# load config
config = get_config()
app = setup(config)
