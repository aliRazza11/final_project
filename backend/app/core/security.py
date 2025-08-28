"""
Authentication utilities for the FastAPI app.

Includes:
- Password hashing and verification (bcrypt)
- JWT access and refresh token generation/validation
- Secure cookie management for auth tokens
- CSRF token handling for state-changing requests
"""
# app/core/security.py
from datetime import datetime, timedelta, timezone
from fastapi import Response, Request, HTTPException, status
from passlib.context import CryptContext
import jwt, secrets
from app.core.config import settings

pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(pw: str) -> str:
    """Hash a plaintext password using bcrypt."""
    return pwd.hash(pw)

def verify_password(pw: str, hashed: str) -> bool:
    """Verify that a plaintext password matches its bcrypt hash."""
    return pwd.verify(pw, hashed)

# -------------------------
# Token Utilities
# -------------------------
def _exp(minutes: int):
    """Return an expiration datetime in UTC, minutes from now."""
    return datetime.now(timezone.utc) + timedelta(minutes=minutes)

def create_access_token(sub: str) -> str:
    """
    Create a short-lived JWT access token.

    Args:
        sub: The subject (e.g., user ID or email).

    Returns:
        Encoded JWT access token.
    """
    payload = {"sub": sub, "exp": _exp(settings.ACCESS_TOKEN_TTL_MIN)}
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALG)

def create_refresh_token(sub: str) -> str:
    """
    Create a long-lived JWT refresh token.

    Args:
        sub: The subject (e.g., user ID or email).

    Returns:
        Encoded JWT refresh token.
    """
    payload = {"sub": sub, "exp": datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_TTL_DAYS)}
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALG)


# -------------------------
# Cookie Utilities
# ------------------------
def set_auth_cookies(resp: Response, access: str, refresh: str) -> str:
    """
    Set access, refresh, and CSRF cookies on the response.

    Args:
        resp: FastAPI Response object.
        access: Encoded JWT access token.
        refresh: Encoded JWT refresh token.

    Returns:
        A newly generated CSRF token (also set as a cookie).
    """
    cookie_params = dict(
        httponly=True,
        secure=settings.SECURE_COOKIES,
        samesite="lax",
        path="/",
        domain=settings.COOKIE_DOMAIN
    )
    resp.set_cookie("access_token", access, **cookie_params)
    resp.set_cookie("refresh_token", refresh, **cookie_params)

    csrf = secrets.token_urlsafe(24)
    resp.set_cookie(
        "csrf_token", csrf,
        httponly=False, secure=settings.SECURE_COOKIES, samesite="lax",
        path="/", domain=settings.COOKIE_DOMAIN
    )
    return csrf

def clear_auth_cookies(resp: Response):
    """Remove authentication and CSRF cookies from the response."""
    for name in ("access_token","refresh_token","csrf_token"):
        resp.delete_cookie(name, path="/", domain=settings.COOKIE_DOMAIN)


# -------------------------
# Token Validation
# -------------------------
def get_sub_from_access_cookie(request: Request) -> str:
    """
    Extract and validate subject from access token in cookies.

    Raises:
        HTTPException(401): If token is missing or invalid.
    """
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing token")
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALG])
        return str(payload["sub"])
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token, please login again")
    
def get_sub_from_refresh_cookie(request: Request) -> str:
    """
    Extract and validate subject from refresh token in cookies.

    Raises:
        HTTPException(401): If token is missing, expired, or invalid.
    """
    token = request.cookies.get("refresh_token")
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing refresh token")
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALG])
        return str(payload["sub"])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Refresh token expired")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")


# -------------------------
# CSRF Protection
# -------------------------
def verify_csrf(request: Request) -> None:
    """
    Weak CSRF check – only validates that csrf_token cookie exists.
    WARNING: This does not fully protect against CSRF attacks.
    """
    if request.method in ("POST", "PUT", "PATCH", "DELETE"):
        cookie = request.cookies.get("csrf_token")
        if not cookie:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="CSRF token missing or invalid")