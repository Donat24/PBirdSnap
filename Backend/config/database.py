from dataclasses import dataclass


@dataclass
class DBConfig:
    user: str
    password: str
    host: str
    port: int
    db: str
