# app/services/image_service.py
from __future__ import annotations
from app.repositories.image_repo import ImageRepo
from app.schemas.image import ImageCreate
from app.models.image import Image, Mnist

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
        return await self.repo.get_by_digit(digit)