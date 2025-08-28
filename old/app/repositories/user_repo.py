# app/repositories/user_repo.py
from __future__ import annotations
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.user import User

class UserRepo:
    def __init__(self, db: AsyncSession): 
        self.db = db

    async def by_email(self, email: str) -> User|None:
        print(" db issue here")
        res = await self.db.execute(select(User).where(User.email == email))
        return res.scalar_one_or_none()

    async def by_id(self, user_id: int) -> User|None:
        res = await self.db.execute(select(User).where(User.id == user_id))
        return res.scalar_one_or_none()

    async def username_exists(self, username: str, exclude_user_id: int|None = None) -> bool:
        q = select(User).where(User.username == username)
        if exclude_user_id:
            q = q.where(User.id != exclude_user_id)
        res = await self.db.execute(q)
        return res.scalar_one_or_none() is not None

    async def email_exists(self, email: str, exclude_user_id: int|None = None) -> bool:
        q = select(User).where(User.email == email)
        if exclude_user_id:
            q = q.where(User.id != exclude_user_id)
        res = await self.db.execute(q)
        return res.scalar_one_or_none() is not None

    async def create(self, email: str, username: str, password_hash: str) -> User:
        user = User(email=email, username=username, password_hash=password_hash)
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def update_user(
        self,
        user: User,
        *,
        username: str|None = None,
        email: str|None = None,
        password_hash: str|None = None,
    ) -> User:
        if username:
            user.username = username
        if email:
            user.email = email
        if password_hash:
            user.password_hash = password_hash
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def delete_user(self, user: User) -> None:
        await self.db.delete(user)
        await self.db.commit()
