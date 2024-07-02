from dataclasses import dataclass
from typing import Optional


@dataclass
class SecurityConfig:
    password_salt: str
