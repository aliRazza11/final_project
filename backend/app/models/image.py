# app/models/image.py
from typing import Optional
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey, DateTime, func, LargeBinary, String, Column, Integer
from app.db.base import Base

class Image(Base):
    """
    Database model for storing uploaded images.

    Attributes:
        id (int): Primary key.
        user_id (int): Foreign key referencing `users.id`.
        image_data (bytes): Raw binary image data (limited to ~16 MB).
        filename (str): Original filename of the uploaded image.
        content_type (str): MIME type (e.g., "image/png").
        created_at (datetime, optional): Timestamp of creation (defaults to `now()`).
    """
    __tablename__ = "images"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    image_data: Mapped[bytes] = mapped_column(LargeBinary(length=(2**24 - 1)), nullable=False)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    content_type: Mapped[str] = mapped_column(String(100), nullable=False)
    created_at: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True), server_default=func.now())