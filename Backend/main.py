import logging
from pathlib import Path

from fastapi import FastAPI

import api
import error_handler
from config.config import get_config
from database.setup import create_engine_sessionmaker
from database.util import create_db_util
from lifespan import lifespan_maker
from middleware.api_key import CreateApiKeyMiddleware
from storage.setup import create_storage

# load config
config = get_config()

# Setup Logging
logging.basicConfig(level=config.logging_level)

# setup db
engine, sessionmaker = create_engine_sessionmaker(config)
db_util = create_db_util(config)

# storage
storage = create_storage(config)

# lifespan
lifespan = lifespan_maker(engine)

# setup fastapi
app = FastAPI(lifespan=lifespan)
error_handler.register(app)

# middleware
app.middleware("http")(CreateApiKeyMiddleware(config.security.api_key))

api.register(app, sessionmaker, db_util, storage)
