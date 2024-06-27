from dataclasses import dataclass


@dataclass
class SecurityConfig:
    api_key: str
    password_salt: str
