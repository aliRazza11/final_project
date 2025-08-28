from fastapi import APIRouter, Depends, Response, Request, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.schemas.user import UserCreate, UserLogin, UserRead
from app.repositories.user_repo import UserRepo
from app.services.auth_service import AuthService
from app.core.security import set_auth_cookies, clear_auth_cookies, get_sub_from_access_cookie, get_sub_from_refresh_cookie, create_refresh_token, create_access_token
import logging
from app.models.user import User
from sqlalchemy import select
from app.core.security import verify_csrf
logging.basicConfig(level=logging.DEBUG)

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/signup", response_model=UserRead)
async def signup(payload: UserCreate, resp: Response, db: AsyncSession = Depends(get_db)):
    svc = AuthService(UserRepo(db))
    user = await svc.signup(payload.email, payload.username, payload.password)
    access, refresh = await svc.issue_tokens(user.id)
    set_auth_cookies(resp, access, refresh)
    return UserRead(id=user.id, username=user.username, email=user.email)

@router.post("/login", response_model=UserRead)
async def login(payload: UserLogin, resp: Response, db: AsyncSession = Depends(get_db)):
    svc = AuthService(UserRepo(db))
    user = await svc.login(payload.email, payload.password)
    access, refresh = await svc.issue_tokens(user.id)
    set_auth_cookies(resp, access, refresh)
    return UserRead(id=user.id, username=user.username, email=user.email)


@router.post("/refresh", response_model=UserRead)
async def refresh(
    resp: Response,
    request: Request,
    db: AsyncSession = Depends(get_db),
    csrf_ok: None = Depends(verify_csrf),
):
    svc = AuthService(UserRepo(db))
    user, access, refresh_token = await svc.refresh_from_request(request)
    set_auth_cookies(resp, access, refresh_token)
    return UserRead(id=user.id, username=user.username, email=user.email)

@router.get("/me", response_model=UserRead)
async def me(request: Request, db: AsyncSession = Depends(get_db)):
    user_id = int(get_sub_from_access_cookie(request))
    res = await db.execute(select(User).where(User.id == user_id))
    user = res.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    return UserRead(
        id=user.id,
        username=user.username,
        email=user.email
    )
@router.post("/logout")
async def logout(resp: Response, csrf_ok: None = Depends(verify_csrf)):
    clear_auth_cookies(resp)
    return {"detail": "logged out"}
