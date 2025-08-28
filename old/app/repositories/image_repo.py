# app/repositories/image_repo.py
from __future__ import annotations
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.image import Image, Mnist
from app.schemas.image import ImageCreate, MnistOut

class ImageRepo:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, image_in: ImageCreate, user_id: int) -> Image:
        db_image = Image(
            image_data=image_in.image_data,
            filename=image_in.filename,
            content_type=image_in.content_type,
            user_id=user_id
        )
        self.db.add(db_image)
        await self.db.commit()
        await self.db.refresh(db_image)
        return db_image

    async def get_by_user(self, user_id: int) -> list[Image]:
        try:
            result = await self.db.execute(select(Image).where(Image.user_id == user_id).order_by(Image.created_at.desc()))
            return result.scalars().all()
        except Exception as e:
            return []

    async def get_one_for_user(self, image_id: int, user_id: int) -> Image | None:
        result = await self.db.execute(select(Image).where(Image.id == image_id, Image.user_id == user_id))
        return result.scalar_one_or_none()

    async def delete(self, image: Image) -> None:
        await self.db.delete(image)
        await self.db.commit()



class MnistRepo:
    def __init__(self, db: AsyncSession):
        self.db = db
    async def get_by_digit(self, digit: int) -> list[Mnist]:
        result = await self.db.execute(
            select(Mnist).where(Mnist.digit == digit).order_by(Mnist.sample_index.asc())
        )
        return result.scalars().all()