from datetime import datetime, timedelta, timezone
from fastapi import Response, Request, HTTPException, status
from passlib.context import CryptContext
import jwt, secrets
from app.core.config import settings

pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(pw: str) -> str:
    return pwd.hash(pw)

def verify_password(pw: str, hashed: str) -> bool:
    return pwd.verify(pw, hashed)

def _exp(minutes: int):
    return datetime.now(timezone.utc) + timedelta(minutes=minutes)

def create_access_token(sub: str) -> str:
    payload = {"sub": sub, "exp": _exp(settings.ACCESS_TOKEN_TTL_MIN)}
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALG)

def create_refresh_token(sub: str) -> str:
    payload = {"sub": sub, "exp": datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_TTL_DAYS)}
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALG)

def set_auth_cookies(resp: Response, access: str, refresh: str) -> str:
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
    for name in ("access_token","refresh_token","csrf_token"):
        resp.delete_cookie(name, path="/", domain=settings.COOKIE_DOMAIN)

def get_sub_from_access_cookie(request: Request) -> str:
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing token")
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALG])
        return str(payload["sub"])
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token, please login again")
    
def get_sub_from_refresh_cookie(request: Request) -> str:
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

def verify_csrf(request: Request) -> None:
    """
    Enforce CSRF for state-changing HTTP methods.
    Frontend must send header: X-CSRF-Token: <csrf_token cookie value>
    """
    if request.method in ("POST", "PUT", "PATCH", "DELETE"):
        cookie = request.cookies.get("csrf_token")
        if not  cookie :
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="CSRF token missing or invalid")