"""
Application configuration module.

This module defines environment-based settings for the FastAPI app,
using Pydantic's BaseSettings. Values are automatically loaded from
environment variables or a `.env` file (defined in Config.env_file).

Centralizing configuration here allows consistent access to values like
database URLs, JWT secrets, and cookie settings throughout the app.
"""
# app/core/config.py
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables or a `.env` file.

    Attributes:
        APP_NAME: Name of the application.
        ENV: Current environment (e.g., "development", "production").
        FRONTEND_ORIGIN: Allowed frontend origin for CORS.
        DATABASE_URL: Database connection URL.
        JWT_SECRET: Secret key used for signing JWT tokens.
        JWT_ALG: Algorithm used for JWT signing (e.g., "HS256").
        ACCESS_TOKEN_TTL_MIN: Access token expiry time in minutes.
        REFRESH_TOKEN_TTL_DAYS: Refresh token expiry time in days.
        COOKIE_DOMAIN: Domain to set cookies for (optional).
        SECURE_COOKIES: Whether to use `Secure` flag on cookies.
    """
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
