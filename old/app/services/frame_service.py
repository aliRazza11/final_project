# app/services/frame_service.py
from app.repositories.frame_repo import FrameRepo
from app.models.frame import ImageFrame
from typing import List

class FrameService:
    def __init__(self, repo: FrameRepo):
        self.repo = repo

    async def save_frames(self, image_id: int, frames: List[dict]) -> None:
        # overwrite logic
        await self.repo.overwrite_for_image(image_id, frames)

    async def get_frames(self, image_id: int) -> list[ImageFrame]:
        return await self.repo.list_for_image(image_id)
