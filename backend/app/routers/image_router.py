# app/routers/image_router.py
from fastapi import APIRouter, Depends, Request, status, UploadFile, File, HTTPException
from fastapi.responses import Response, JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.core.security import verify_csrf
from app.db.session import get_db
from app.schemas.image import ImageCreate, ImageOut, MnistOut, MnistRequest
from app.repositories.image_repo import ImageRepo, ImageNotFoundError
from app.services.image_service import ImageService
# from app.services.mnist_service import MnistService
from app.services.auth_service import AuthService
from app.models.user import User
from app.repositories.user_repo import UserRepository
import logging


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/images", tags=["Images"])



async def get_current_user_dep(request: Request, db: AsyncSession = Depends(get_db)) -> User:
    """
    Dependency to fetch the currently authenticated user.

    Args:
        request (Request): The incoming HTTP request containing cookies/headers.
        db (AsyncSession): Database session dependency.

    Returns:
        User: The authenticated user instance.
    """
    try:
        auth_service = AuthService(UserRepository(db))
        return await auth_service.get_current_user(request)
    except Exception as e:
        logger.exception("Error fetching current user")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="Failed to authenticate user")


@router.post("", response_model=ImageOut, status_code=status.HTTP_201_CREATED)
async def upload_image(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_dep),
    csrf_ok: None = Depends(verify_csrf),
):
    """
    Upload an image and store it in the database.

    Args:
        file (UploadFile): The uploaded image file.
        db (AsyncSession): Database session dependency.
        current_user (User): The authenticated user.
        csrf_ok (None): CSRF token validation dependency.

    Returns:
        ImageOut: Metadata of the stored image.
    """
    try:
        contents = await file.read()
        if not contents:
            raise HTTPException(status_code=400, detail="Uploaded file is empty")
        
        image_in = ImageCreate(
            image_data=contents,
            filename=file.filename or "upload",
            content_type=file.content_type or "application/octet-stream",
        )
        svc = ImageService(ImageRepo(db))
        return await svc.create_image(image_in, current_user.id)
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to upload image")
        raise HTTPException(status_code=500, detail="Image upload failed")
    

@router.get("", response_model=List[ImageOut])
async def list_user_images(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_dep)
):
    """
    List all images uploaded by the current user.

    Args:
        db (AsyncSession): Database session dependency.
        current_user (User): The authenticated user.

    Returns:
        List[ImageOut]: A list of image metadata.
    """
    try:
        svc = ImageService(ImageRepo(db))
        return await svc.list_images(current_user.id)
    except ImageNotFoundError as e:
        logger.exception("Failed to list user images")
        raise HTTPException(status_code=500, detail="Image not found")
    


@router.get("/{image_id}")
async def get_image_bytes(
    image_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_dep)
):
    """
    Retrieve raw image bytes for a given image ID, if owned by the user.

    Args:
        image_id (int): The ID of the image.
        db (AsyncSession): Database session dependency.
        current_user (User): The authenticated user.

    Raises:
        HTTPException: 404 if the image is not found.

    Returns:
        Response: The image file as a binary response with appropriate headers.
    """
    try:
        svc = ImageService(ImageRepo(db))
        img = await svc.get_user_image(image_id, current_user.id)
        if not img:
            raise HTTPException(status_code=404, detail="Not found")
        return Response(content=img.image_data, media_type=img.content_type,
                        headers={"Content-Disposition": f'inline; filename="{img.filename}"'})
    except ImageNotFoundError:
        raise
    except Exception as e:
        logger.exception("Error fetching image bytes")
        raise HTTPException(status_code=500, detail="Failed to retrieve image")
    


@router.delete("/{image_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_image(
    image_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_dep),
    csrf_ok: None = Depends(verify_csrf),
):
    """
    Delete a user's image by ID.

    Args:
        image_id (int): The ID of the image to delete.
        db (AsyncSession): Database session dependency.
        current_user (User): The authenticated user.
        csrf_ok (None): CSRF token validation dependency.

    Raises:
        HTTPException: 404 if the image does not exist.

    Returns:
        JSONResponse: A success message if deletion succeeds.
    """
    try:
        svc = ImageService(ImageRepo(db))
        img = await svc.get_user_image(image_id, current_user.id)
        if not img:
            raise HTTPException(status_code=404, detail="Not found")
        await svc.delete_image(img)
        return JSONResponse(content={"message": "Image deleted successfully"}, status_code=200)
    except ImageNotFoundError:
        raise HTTPException(status_code=400, detail="Image not found")
    except Exception as e:
        logger.exception("Failed to delete image")
        raise HTTPException(status_code=500, detail="Image deletion failed")


@router.get("/digit/{digit}", response_model=List[MnistOut])
async def get_images_by_digit(
    digit: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieve MNIST dataset images filtered by digit value.

    Args:
        digit (int): The target digit (0–9).
        db (AsyncSession): Database session dependency.

    Raises:
        HTTPException: 400 if digit is not between 0–9.
        HTTPException: 404 if no images are found for the digit.

    Returns:
        List[MnistOut]: A list of MNIST images for the given digit.
    """
    try:
        req = MnistRequest(digit=digit)
        svc = ImageService(ImageRepo(db))
        images = await svc.get_images_for_digit(req.digit)
        if not images:
            raise HTTPException(status_code=404, detail="No images found for this digit")
        return images
    except ImageNotFoundError:
        raise
    except Exception as e:
        logger.exception("Failed to fetch MNIST images")
        raise HTTPException(status_code=500, detail="Could not retrieve MNIST images")