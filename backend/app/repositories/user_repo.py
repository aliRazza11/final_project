# app/repositories/user_repo.py
from __future__ import annotations
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from app.models.user import User


class UserRepoError(Exception):
    """Base exception for user repository errors."""

class UserNotFoundError(UserRepoError):
    """Raised when a user cannot be found in the database."""

class UserRepository:
    """
    Repository class for performing database operations on the User model.

    Provides a clean abstraction layer between the database session
    and business logic. Encapsulates common CRUD operations.
    """
    def __init__(self, db: AsyncSession):
        """
        Initialize the repository with a database session.

        Args:
            db (AsyncSession): Active SQLAlchemy async session.
        """
        self.db = db

    async def get_by_email(self, email: str) -> User|None:
        """
        Retrieve a user by email address.

        Args:
            email (str): User's email address.

        Returns:
            User | None: Matching User instance or None if not found.
        """
        try:
            print(" db issue here")
            res = await self.db.execute(select(User).where(User.email == email))
            user = res.scalar_one_or_none()
            if not user:
                raise UserNotFoundError(f"User with email {email} not found")
            return user
        except SQLAlchemyError as e:
            raise UserRepoError("Failed to fetch user by email from the database") from e

    async def get_by_id(self, user_id: int) -> User|None:
        """
        Retrieve a user by their unique ID.

        Args:
            user_id (int): User's primary key.

        Returns:
            User | None: Matching User instance or None if not found.
        """
        try:
            res = await self.db.execute(select(User).where(User.id == user_id))
            user = res.scalar_one_or_none()
            if not user:
                raise UserNotFoundError(f"User with id {user_id} not found")
            return user
        except SQLAlchemyError as e:
            raise UserRepoError("Failed to fetch user by id from the database") from e

    async def username_exists(self, username: str, exclude_user_id: int|None = None) -> bool:
        """
        Check whether a username already exists.

        Args:
            username (str): Username to check.
            exclude_user_id (int | None): Optional ID to exclude (useful for updates).

        Returns:
            bool: True if username exists, False otherwise.
        """
        try:
            q = select(User).where(User.username == username)
            if exclude_user_id:
                q = q.where(User.id != exclude_user_id)
            res = await self.db.execute(q)
            return res.scalar_one_or_none() is not None
        except SQLAlchemyError as e:
            raise UserRepoError("Failed to check username existence") from e

    async def email_exists(self, email: str, exclude_user_id: int|None = None) -> bool:
        """
        Check whether an email already exists.

        Args:
            email (str): Email to check.
            exclude_user_id (int | None): Optional ID to exclude (useful for updates).

        Returns:
            bool: True if email exists, False otherwise.
        """
        try:
            q = select(User).where(User.email == email)
            if exclude_user_id:
                q = q.where(User.id != exclude_user_id)
            res = await self.db.execute(q)
            return res.scalar_one_or_none() is not None
        except SQLAlchemyError as e:
            raise UserRepoError("Failed to check email existence") from e

    async def create(self, email: str, username: str, password_hash: str) -> User:
        """
        Create and persist a new user.

        Args:
            email (str): User's email address.
            username (str): Chosen username.
            password_hash (str): Securely hashed password.

        Returns:
            User: Newly created User instance.
        """
        try:
            user = User(email=email, username=username, password_hash=password_hash)
            self.db.add(user)
            await self.db.commit()
            await self.db.refresh(user)
            return user
        except IntegrityError as e:
            await self.db.rollback()
            raise UserRepoError("Failed to create user: email or username may already exist") from e
        except SQLAlchemyError as e:
            await self.db.rollback()
            raise UserRepoError("Failed to create user due to database error") from e
        

    async def update_user(
        self,
        user: User,
        *,
        username: str|None = None,
        email: str|None = None,
        password_hash: str|None = None,
    ) -> User:
        """
        Update an existing user with new values.

        Args:
            user (User): The user instance to update.
            username (str | None): New username (optional).
            email (str | None): New email address (optional).
            password_hash (str | None): New password hash (optional).

        Returns:
            User: Updated User instance.
        """
        if username:
            user.username = username
        if email:
            user.email = email
        if password_hash:
            user.password_hash = password_hash
        try:
            self.db.add(user)
            await self.db.commit()
            await self.db.refresh(user)
            return user
        except IntegrityError as e:
            await self.db.rollback()
            raise UserRepoError("Failed to update user: email or username may already exist") from e
        except SQLAlchemyError as e:
            await self.db.rollback()
            raise UserRepoError("Failed to update user due to database error") from e

    async def delete_user(self, user: User) -> None:
        """
        Permanently delete a user from the database.

        Args:
            user (User): User instance to delete.
        """
        try:
            await self.db.delete(user)
            await self.db.commit()
        except SQLAlchemyError as e:
            await self.db.rollback()
            raise UserRepoError("Failed to delete user from the database") from e