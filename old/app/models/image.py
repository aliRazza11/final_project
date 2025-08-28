from typing import Optional
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey, DateTime, func, LargeBinary, String, Column, Integer
from app.db.base import Base

class Image(Base):
    __tablename__ = "images"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    image_data: Mapped[bytes] = mapped_column(LargeBinary(length=(2**24 - 1)), nullable=False)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    content_type: Mapped[str] = mapped_column(String(100), nullable=False)
    created_at: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True), server_default=func.now())

class Mnist(Base):
    __tablename__ = "mnist"
    id = Column(Integer, primary_key=True, index=True)
    digit = Column(Integer, nullable=False, index=True)
    sample_index = Column(Integer, nullable=False)
    image_data = Column(LargeBinary, nullable=False)
