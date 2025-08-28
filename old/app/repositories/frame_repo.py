# app/repositories/frame_repo.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from app.models.frame import ImageFrame
from typing import List

class FrameRepo:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, image_id: int, local_t: int, global_t: int, frame_data: bytes, beta: float, metrics: dict) -> ImageFrame:
        frame = ImageFrame(
            image_id=image_id,
            local_t=local_t,
            global_t=global_t,
            frame_data=frame_data,
            beta=beta,
            metrics=metrics,
        )
        self.db.add(frame)
        await self.db.commit()
        await self.db.refresh(frame)
        return frame

    async def overwrite_for_image(self, image_id: int, frames: List[dict]) -> None:
        await self.db.execute(delete(ImageFrame).where(ImageFrame.image_id == image_id))
        await self.db.commit()
        objs = [
            ImageFrame(
                image_id=image_id,
                local_t=f["localT"],
                global_t=f["globalT"],
                frame_data=f["frame_data"],
                beta=f.get("betas"),
                metrics=f.get("metrics"),
            )
            for f in frames
        ]
        self.db.add_all(objs)
        await self.db.commit()

    async def list_for_image(self, image_id: int) -> list[ImageFrame]:
        res = await self.db.execute(select(ImageFrame).where(ImageFrame.image_id == image_id).order_by(ImageFrame.local_t.asc()))
        return res.scalars().all()
