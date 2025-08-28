# app/routers/frame_router.py
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.repositories.frame_repo import FrameRepo
from app.services.frame_service import FrameService
from app.routers.image_router import get_current_user_dep
from app.models.user import User
from app.models.image import Image
from sqlalchemy import select
import base64

router = APIRouter(prefix="/frames", tags=["Frames"])

@router.post("/{image_id}")
async def save_frames(
    image_id: int,
    frames: list[dict],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_dep),
):
    # verify image belongs to user
    res = await db.execute(select(Image).where(Image.id == image_id, Image.user_id == current_user.id))
    image = res.scalar_one_or_none()
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")

    svc = FrameService(FrameRepo(db))

    # convert from data URL → bytes
    for f in frames:
        if f.get("image") and f["image"].startswith("data:"):
            header, b64 = f["image"].split(",", 1)
            f["frame_data"] = base64.b64decode(b64)
        else:
            f["frame_data"] = None
    await svc.save_frames(image_id, frames)
    return {"ok": True, "count": len(frames)}

@router.get("/{image_id}")
async def get_frames(
    image_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_dep),
):
    svc = FrameService(FrameRepo(db))
    frames = await svc.get_frames(image_id)
    return [
        {
            "localT": f.local_t,
            "globalT": f.global_t,
            "betas": f.beta,
            "metrics": f.metrics,
            "image": "data:image/jpeg;base64," + base64.b64encode(f.frame_data).decode("utf-8"),
        }
        for f in frames
    ]
