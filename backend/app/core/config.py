from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    APP_NAME: str
    ENV: str
    FRONTEND_ORIGIN: str
    DATABASE_URL: str
    JWT_SECRET: str
    JWT_ALG: str
    ACCESS_TOKEN_TTL_MIN: int
    REFRESH_TOKEN_TTL_DAYS: int
    COOKIE_DOMAIN: Optional[str]
    SECURE_COOKIES: bool

    class Config:
        env_file = ".env"


settings = Settings()
