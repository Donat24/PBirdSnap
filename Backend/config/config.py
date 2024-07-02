import os
from dataclasses import dataclass

from config.database import DBConfig
from config.security import SecurityConfig
from config.storage import StorageConfig


@dataclass
class Config:
    logging_level: int
    db: DBConfig
    storage: StorageConfig
    security: SecurityConfig
    


def get_config() -> Config:
    return Config(
        logging_level=int(os.environ.get("LOGLEVEL", "20")),
        db=DBConfig(
            user=os.environ["DBUSER"],
            password=os.environ["DBPASSWORD"],
            host=os.environ["DBHOST"],
            port=int(os.environ["DBPORT"]),
            db=os.environ["DBNAME"],
        ),
        storage=StorageConfig(path=os.environ["STORAGEPATH"]),
        security=SecurityConfig(
            password_salt=os.environ["PASSWORDSALT"],
        )
    )
