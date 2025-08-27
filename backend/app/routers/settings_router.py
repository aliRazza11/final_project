from fastapi import APIRouter, Depends, Request, status, HTTPException, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.settings import (
    SettingsUpdate,
    SettingsUpdateResult,
    DeleteAccountRequest,
    DeleteAccountResult,
)
from app.repositories.user_repo import UserRepo
from app.services.auth_service import AuthService
from app.services.settings_service import SettingsService
from app.models.user import User
from app.core.security import clear_auth_cookies
from app.core.security import verify_csrf


router = APIRouter(prefix="/settings", tags=["Settings"])

# Dependency to get logged-in user
async def get_current_user_dep(request: Request, db: AsyncSession = Depends(get_db)) -> User:
    auth_service = AuthService(UserRepo(db))
    return await auth_service.get_current_user(request)

@router.patch("", response_model=SettingsUpdateResult)
async def update_settings(
    payload: SettingsUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_dep),
    csrf_ok: None = Depends(verify_csrf),
):
    svc = SettingsService(UserRepo(db), AuthService(UserRepo(db)))

    try:
        _, reauth_required, msg = await svc.update_settings(current_user.id, payload)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # If password changed, clear cookies so user must login again
    response = SettingsUpdateResult(ok=True, reauth_required=reauth_required, message=msg)
    return response

@router.post("/delete", response_model=DeleteAccountResult)
async def delete_account(
    payload: DeleteAccountRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_dep),
    csrf_ok: None = Depends(verify_csrf),
    resp: Response = None,
):
    svc = SettingsService(UserRepo(db), AuthService(UserRepo(db)))

    try:
        msg = await svc.delete_account(current_user.id, payload)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # After deleting user, clear cookies
    clear_auth_cookies(resp)  # will work if you pass `Response` object instead of None

    return DeleteAccountResult(ok=True, message=msg)
