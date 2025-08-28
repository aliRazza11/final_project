# app/models/frame.py
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import ForeignKey, DateTime, func, LargeBinary, Float, JSON, Integer
from app.db.base import Base
from datetime import datetime

class ImageFrame(Base):
    """
    Database model for storing frames associated with an image.

    Each frame belongs to a parent image (`image_id`) and represents a
    time step in both local and global coordinates. Raw frame data is
    stored as binary, along with optional beta value and metrics.

    Attributes:
        id (int): Primary key.
        image_id (int): Foreign key referencing `images.id`.
        local_t (int): Local time index within an image sequence.
        global_t (int): Global time index across all sequences.
        frame_data (bytes): Binary-encoded frame (e.g., compressed image).
        beta (float, optional): Diffusion beta value at this timestep.
        metrics (dict, optional): JSON-encoded metrics related to the frame.
        created_at (datetime): Timestamp of record creation.
    """
    __tablename__ = "image_frames"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    image_id: Mapped[int] = mapped_column(ForeignKey("images.id", ondelete="CASCADE"), nullable=False)

    local_t: Mapped[int] = mapped_column(Integer, nullable=False)
    global_t: Mapped[int] = mapped_column(Integer, nullable=False)

    frame_data: Mapped[bytes] = mapped_column(LargeBinary(length=(2**32 - 1)), nullable=False)
    beta: Mapped[float] = mapped_column(Float, nullable=True)
    metrics: Mapped[dict] = mapped_column(JSON, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
