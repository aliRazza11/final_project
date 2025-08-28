# app/models/mnist.py
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String
from app.db.base import Base

class User(Base):
    """
    Database model for application users.

    Attributes:
        id (int): Primary key, auto-incremented.
        username (str): Display or login name (not unique).
        email (str): Unique user email, used for authentication.
        password_hash (str): Hashed user password (bcrypt, argon2, etc.).
    """
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))