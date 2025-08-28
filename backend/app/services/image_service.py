# app/services/image_service.py
from __future__ import annotations
from app.repositories.image_repo import ImageRepo
from app.schemas.image import ImageCreate
from app.models.image import Image
from app.models.mnist import Mnist
from app.models.frame import ImageFrame
from typing import List

class ImageService:
    def __init__(self, image_repo: ImageRepo):
        self.image_repo = image_repo

    async def create_image(self, image_in: ImageCreate, user_id: int) -> Image:
        return await self.image_repo.create(image_in, user_id)

    async def list_images(self, user_id: int) -> list[Image]:
        return await self.image_repo.get_by_user(user_id)

    async def get_user_image(self, image_id: int, user_id: int) -> Image | None:
        return await self.image_repo.get_one_for_user(image_id, user_id)

    async def delete_image(self, image: Image) -> None:
        return await self.image_repo.delete(image)

    async def get_images_for_digit(self, digit: int) -> list[Mnist]:
        return await self.image_repo.get_by_digit(digit)
    
    async def save_frames(self, image_id: int, frames: List[dict]) -> None:
        """
        Save or overwrite frames for a given image.

        This will remove any existing frames linked to the image
        and replace them with the provided list.

        Args:
            image_id (int): The ID of the image to associate frames with.
            frames (List[dict]): A list of frame data dictionaries
                                 (must match the expected schema in the repo).
        """
        # overwrite logic
        await self.image_repo.overwrite_for_image(image_id, frames)

    async def get_frames(self, image_id: int) -> list[ImageFrame]:
        """
        Retrieve all frames associated with a given image.

        Args:
            image_id (int): The ID of the image to fetch frames for.

        Returns:
            list[ImageFrame]: A list of ImageFrame ORM objects
                              representing the stored frames.
        """
        return await self.image_repo.list_for_image(image_id)
