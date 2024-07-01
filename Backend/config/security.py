from dataclasses import dataclass
from typing import Optional


@dataclass
class SecurityConfig:
    api_key: Optional[str]
    password_salt: str
