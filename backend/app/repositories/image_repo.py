# app/repositories/image_repo.py
from __future__ import annotations
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from app.models.image import Image
from app.models.mnist import Mnist
from app.schemas.image import ImageCreate
from app.models.frame import ImageFrame
from typing import List

class ImageRepoError(Exception):
    """Base exception for image repository errors."""

class ImageNotFoundError(ImageRepoError):
    """Raised when no image is found for a given criteria."""


class MnistRepoError(Exception):
    """Base exception for MNIST repository errors."""

class MnistNotFoundError(MnistRepoError):
    """Raised when no MNIST samples are found for a given digit."""

class FrameRepoError(Exception):
    """Base exception for frame repository errors."""


class FrameNotFoundError(FrameRepoError):
    """Raised when no frame is found for a given image ID."""


class ImageRepo:
    """
    Repository for `Image` entities.

    Provides CRUD operations on user-uploaded images.
    """
    def __init__(self, db: AsyncSession):
        """
        Initialize repository with a database session.

        Args:
            db (AsyncSession): Active SQLAlchemy async session.
        """
        self.db = db

    async def create(self, image_in: ImageCreate, user_id: int) -> Image:
        """
        Create and persist a new image record for a user.

        Args:
            image_in (ImageCreate): Pydantic schema containing image data,
                filename, and content type.
            user_id (int): ID of the owning user.

        Returns:
            Image: The newly created image record.
        """
        db_image = Image(
            image_data=image_in.image_data,
            filename=image_in.filename,
            content_type=image_in.content_type,
            user_id=user_id
        )
        try:
            self.db.add(db_image)
            await self.db.commit()
            await self.db.refresh(db_image)
            return db_image
        except IntegrityError as e:
            await self.db.rollback()
            raise ImageRepoError("Failed to create image due to integrity error.") from e
        except SQLAlchemyError as e:
            await self.db.rollback()
            raise ImageRepoError("Failed to create image due to database error.") from e

    async def get_by_user(self, user_id: int) -> list[Image]:
        """
        Retrieve all images belonging to a user.

        Args:
            user_id (int): ID of the user.

        Returns:
            list[Image]: List of images ordered by creation time (descending).
        """
        try:
            result = await self.db.execute(
                select(Image)
                .where(Image.user_id == user_id)
                .order_by(Image.created_at.desc())
                )
            images = result.scalars().all()
            if not images:
                raise ImageNotFoundError(f"No Image found for user_id={user_id}. Please upload an image first to use /diffuse")
            return images
        except SQLAlchemyError as e:
            raise ImageRepoError("Failed to fetch images from the database.") from e

    async def get_one_for_user(self, image_id: int, user_id: int) -> Image | None:
        """
        Retrieve a single image by ID, scoped to a specific user.

        Args:
            image_id (int): Image ID to fetch.
            user_id (int): Owner user ID.

        Returns:
            Image | None: The image if found, otherwise None.
        """
        try:
            result = await self.db.execute(
                select(Image).where(Image.id == image_id, Image.user_id == user_id)
                )
            image = result.scalar_one_or_none()
            if not image:
                raise ImageNotFoundError(f"Image with id={image_id} not found for user_id={user_id}")
            return image
        except Exception as e:
            return e

    async def delete(self, image: Image) -> None:
        """
        Delete an image record.

        Args:
            image (Image): The image object to delete.

        Returns:
            None
        """
        try:
            await self.db.delete(image)
            await self.db.commit()
        except SQLAlchemyError as e:
            raise ImageRepoError("Failed to delete image from the database. Please try again") from e
        
    async def get_by_digit(self, digit: int) -> list[Mnist]:
        """
        Retrieve all MNIST samples for a given digit.

        Args:
            digit (int): Digit label (0–9).

        Returns:
            list[Mnist]: List of ordered samples for that digit.
        """
        try:
            result = await self.db.execute(
                select(Mnist).where(Mnist.digit == digit).order_by(Mnist.sample_index.asc())
            )
            samples = result.scalars().all()
            if not samples:
                raise MnistNotFoundError(f"No MNIST samples found for digit={digit}")
            return samples
        except SQLAlchemyError as e:
            raise MnistRepoError("Failed to fetch MNIST samples from the database.") from e
        

    """
    Repository layer for `ImageFrame` entities.

    Handles database operations such as create, delete, and query
    for frames belonging to a given image.
    """
    def __init__(self, db: AsyncSession):
        """
        Initialize repository with a database session.

        Args:
            db (AsyncSession): Active SQLAlchemy async session.
        """
        self.db = db

    async def frame_create(self,
        image_id: int,
        local_t: int,
        global_t: int,
        frame_data: bytes,
        beta: float,
        metrics: dict
        ) -> ImageFrame:
        """
        Create and persist a new frame for an image.

        Args:
            image_id (int): ID of the parent image.
            local_t (int): Local timestep index.
            global_t (int): Global timestep index.
            frame_data (bytes): Binary frame content.
            beta (float): Diffusion beta value.
            metrics (dict): Additional frame-related metadata.

        Returns:
            ImageFrame: The newly created frame object.
        """
        frame = ImageFrame(
            image_id=image_id,
            local_t=local_t,
            global_t=global_t,
            frame_data=frame_data,
            beta=beta,
            metrics=metrics,
        )
        try:
            self.db.add(frame)
            await self.db.commit()
            await self.db.refresh(frame)
            return frame
        except IntegrityError as e:
            await self.db.rollback()
            raise FrameRepoError("Failed to create frame due to integrity error.") from e
        except SQLAlchemyError as e:
            await self.db.rollback()
            raise FrameRepoError("Failed to create frame due to integrity error.") from e

    async def overwrite_for_image(self, image_id: int, frames: List[dict]) -> None:
        """
        Replace all frames of a given image with a new list.

        Args:
            image_id (int): ID of the parent image.
            frames (List[dict]): List of frame dicts containing:
                - localT (int)
                - globalT (int)
                - frame_data (bytes)
                - betas (float, optional)
                - metrics (dict, optional)

        Returns:
            None
        """
        try:
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
        except SQLAlchemyError as e:
            await self.db.rollback()
            raise FrameRepoError("Failed to overwrite frames due to database error.") from e

    async def list_for_image(self, image_id: int) -> list[ImageFrame]:
        """
        Retrieve all frames for a given image, ordered by local_t.

        Args:
            image_id (int): ID of the parent image.

        Returns:
            list[ImageFrame]: Ordered list of frames.
        """
        try:
            res = await self.db.execute(
                select(ImageFrame)
                .where(ImageFrame.image_id == image_id)
                .order_by(ImageFrame.local_t.asc())
                )
            return res.scalars().all()
        except SQLAlchemyError as e:
            raise FrameRepoError("Failed to list frames due to database error.") from e
