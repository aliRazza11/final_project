# app/models/frame.py
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import ForeignKey, DateTime, func, LargeBinary, Float, JSON, Integer
from app.db.base import Base
from datetime import datetime

class ImageFrame(Base):
    __tablename__ = "image_frames"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    image_id: Mapped[int] = mapped_column(ForeignKey("images.id", ondelete="CASCADE"), nullable=False)

    local_t: Mapped[int] = mapped_column(Integer, nullable=False)
    global_t: Mapped[int] = mapped_column(Integer, nullable=False)

    frame_data: Mapped[bytes] = mapped_column(LargeBinary(length=(2**32 - 1)), nullable=False)
    beta: Mapped[float] = mapped_column(Float, nullable=True)
    metrics: Mapped[dict] = mapped_column(JSON, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
