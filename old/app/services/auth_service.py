from fastapi import HTTPException, status, Request, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.user_repo import UserRepo
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    get_sub_from_access_cookie,
    get_sub_from_refresh_cookie
)
from app.models.user import User
from sqlalchemy import select

class AuthService:
    def __init__(self, user_repo: UserRepo):
        self.user_repo = user_repo

    async def signup(self, email: str, username: str, password: str):
        if await self.user_repo.by_email(email):
            raise HTTPException(status_code=400, detail="Email already registered")
        user = await self.user_repo.create(email, username, hash_password(password))
        return user

    async def login(self, email: str, password: str):
        user = await self.user_repo.by_email(email)
        if not user or not verify_password(password, user.password_hash):
            raise HTTPException(status_code=401, detail="Invalid credentials")
        return user

    async def issue_tokens(self, user_id: int):
        return create_access_token(str(user_id)), create_refresh_token(str(user_id))

    async def get_current_user(self, request: Request) -> User:
        user_id = get_sub_from_access_cookie(request)
        result = await self.user_repo.db.execute(select(User).where(User.id == int(user_id)))
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
            )
        return user

    async def refresh_from_request(self, request: Request):
        user_id = int(get_sub_from_refresh_cookie(request))
        user = await self.user_repo.by_id(user_id)
        if not user:
            raise HTTPException(status_code=401, detail="User not found")

        access = create_access_token(str(user.id))
        refresh = create_refresh_token(str(user.id))
        return user, access, refresh

    def hash_password(self, password: str) -> str:
        return hash_password(password)

    def verify_password(self, plain: str, hashed: str) -> bool:
        return verify_password(plain, hashed)
    