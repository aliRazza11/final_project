# app/api/images.py
from fastapi import APIRouter, Depends, Request, status, UploadFile, File, HTTPException
from fastapi.responses import Response, JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.core.security import verify_csrf
from app.db.session import get_db
from app.schemas.image import ImageCreate, ImageOut, MnistOut
from app.repositories.image_repo import ImageRepo, MnistRepo
from app.services.image_service import ImageService, MnistService
from app.services.auth_service import AuthService
from app.models.user import User
from app.repositories.user_repo import UserRepo
router = APIRouter(prefix="/images", tags=["Images"])

async def get_current_user_dep(request: Request, db: AsyncSession = Depends(get_db)) -> User:
    auth_service = AuthService(UserRepo(db))
    return await auth_service.get_current_user(request)

@router.post("", response_model=ImageOut, status_code=status.HTTP_201_CREATED)
async def upload_image(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_dep),
    csrf_ok: None = Depends(verify_csrf),
):
    contents = await file.read()
    image_in = ImageCreate(
        image_data=contents,
        filename=file.filename or "upload",
        content_type=file.content_type or "application/octet-stream",
    )
    svc = ImageService(ImageRepo(db))
    return await svc.create_image(image_in, current_user.id)

@router.get("", response_model=List[ImageOut])
async def list_user_images(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_dep)
):
    svc = ImageService(ImageRepo(db))
    return await svc.list_images(current_user.id)

@router.get("/{image_id}")
async def get_image_bytes(
    image_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_dep)
):
    svc = ImageService(ImageRepo(db))
    img = await svc.get_user_image(image_id, current_user.id)
    if not img:
        raise HTTPException(status_code=404, detail="Not found")
    return Response(content=img.image_data, media_type=img.content_type,
                    headers={"Content-Disposition": f'inline; filename="{img.filename}"'})

@router.delete("/{image_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_image(
    image_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_dep),
    csrf_ok: None = Depends(verify_csrf),
):
    svc = ImageService(ImageRepo(db))
    img = await svc.get_user_image(image_id, current_user.id)
    if not img:
        raise HTTPException(status_code=404, detail="Not found")
    await svc.delete_image(img)
    return JSONResponse(content={"message": "Image deleted successfully"}, status_code=200)


@router.get("/digit/{digit}", response_model=List[MnistOut])
async def get_images_by_digit(
    digit: int,
    db: AsyncSession = Depends(get_db)
):
    if digit < 0 or digit > 9:
        raise HTTPException(status_code=400, detail="Digit must be between 0 and 9")

    svc = MnistService(MnistRepo(db))
    images = await svc.get_images_for_digit(digit)
    if not images:
        raise HTTPException(status_code=404, detail="No images found for this digit")
    return images