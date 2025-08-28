# app/routers/auth.py
from fastapi import APIRouter, Depends, Response, Request, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.schemas.user import UserCreate, UserLogin, UserRead
from app.repositories.user_repo import UserRepository, UserNotFoundError
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
    """
    Register a new user account.

    - Validates input using `UserCreate` schema.
    - Creates a new user record in the database.
    - Issues access and refresh tokens.
    - Sets authentication cookies on the response.

    Args:
        payload (UserCreate): Incoming user registration data.
        resp (Response): FastAPI response object used to set cookies.
        db (AsyncSession): Database session dependency.

    Returns:
        UserRead: Public user details (id, username, email).
    """
    try:
        svc = AuthService(UserRepository(db))
        user = await svc.signup(payload.email, payload.username, payload.password)
        access, refresh = await svc.issue_tokens(user.id)
        set_auth_cookies(resp, access, refresh)
        user = UserRead(id=user.id, username=user.username, email=user.email)
        print(user)
        return user
    except ValueError as e:
        logging.error(f"Signup failed: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logging.exception("Unexpected error during signup")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/login", response_model=UserRead)
async def login(payload: UserLogin, resp: Response, db: AsyncSession = Depends(get_db)):
    """
    Authenticate a user and issue tokens.

    - Validates credentials against stored user records.
    - Issues new access and refresh tokens.
    - Sets authentication cookies on the response.

    Args:
        payload (UserLogin): Incoming login request (email + password).
        resp (Response): Response object to set cookies.
        db (AsyncSession): Database session dependency.

    Returns:
        UserRead: Public user details (id, username, email).
    """
    try:
        print("yes")
        svc = AuthService(UserRepository(db))
        user = await svc.login(payload.email, payload.password)
        access, refresh = await svc.issue_tokens(user.id)
        set_auth_cookies(resp, access, refresh)
        return UserRead(id=user.id, username=user.username, email=user.email)
    except ValueError as e:
        logging.error(f"Login failed: {e}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
    except HTTPException:  # Let HTTPExceptions pass through
        raise
    except Exception as e:
        logging.exception("Unexpected error during login")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")



@router.post("/refresh", response_model=UserRead)
async def refresh(
    resp: Response,
    request: Request,
    db: AsyncSession = Depends(get_db),
    csrf_ok: None = Depends(verify_csrf),
):
    """
    Refresh authentication tokens.

    - Validates CSRF token and refresh token from cookies.
    - Issues new access and refresh tokens.
    - Updates authentication cookies.

    Args:
        resp (Response): Response object to update cookies.
        request (Request): Incoming request containing refresh token.
        db (AsyncSession): Database session dependency.
        csrf_ok (None): Dependency ensuring CSRF check passes.

    Returns:
        UserRead: Public user details (id, username, email).
    """
    try:
        svc = AuthService(UserRepository(db))
        user, access, refresh_token = await svc.refresh_from_request(request)
        set_auth_cookies(resp, access, refresh_token)
        return UserRead(id=user.id, username=user.username, email=user.email)
    except (ValueError, UserNotFoundError) as e:
        
        logging.warning(f"Refresh failed: {e}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
    except Exception as e:
        logging.exception("Unexpected error during token refresh")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")



@router.get("/me", response_model=UserRead)
async def me(request: Request, db: AsyncSession = Depends(get_db)):
    """
    Retrieve the currently authenticated user.

    - Extracts user ID from the access token cookie.
    - Queries the database for the corresponding user record.

    Args:
        request (Request): Incoming request containing auth cookies.
        db (AsyncSession): Database session dependency.

    Raises:
        HTTPException: If no valid authenticated user is found.

    Returns:
        UserRead: Public user details (id, username, email).
    """
    try:
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
    except ValueError:
        logging.warning("Invalid access token format")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid access token")
    except Exception as e:
        logging.exception("Unexpected error fetching current user")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.post("/logout")
async def logout(resp: Response, csrf_ok: None = Depends(verify_csrf)):
    """
    Log out the current user.

    - Requires a valid CSRF token.
    - Clears authentication cookies from the response.

    Args:
        resp (Response): Response object used to clear cookies.
        csrf_ok (None): Dependency ensuring CSRF check passes.

    Returns:
        dict: Confirmation message {"detail": "logged out"}.
    """
    try:
        clear_auth_cookies(resp)
        return {"detail": "logged out"}
    except Exception as e:
        logging.exception("Logout failed.")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")