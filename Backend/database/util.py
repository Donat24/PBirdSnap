import base64
from typing import Callable, Union

import bcrypt

from config.config import Config


class DBUtil:
    def __init__(
        self,
        hash_func: Callable[[Union[bytes, str]], str],
    ) -> None:
        self.hash_func = hash_func


def create_db_util(config: Config) -> DBUtil:
    return DBUtil(
        hash_func=_create_hash_function(config),
    )


def _create_hash_function(config: Config) -> Callable[[Union[bytes, str]], str]:

    salt = config.security.password_salt.encode("utf-8")

    def salt_and_hash_password(password: Union[bytes, str]) -> str:
        if isinstance(password, bytes):
            return base64.b64encode(bcrypt.hashpw(password, salt)).decode("ascii")
        else:
            return base64.b64encode(
                bcrypt.hashpw(password.encode("utf-8"), salt)
            ).decode("ascii")

    return salt_and_hash_password
