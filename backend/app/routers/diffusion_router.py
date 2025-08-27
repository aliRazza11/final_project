# app/routers/diffusion_router.py

from fastapi import (
    APIRouter,
    Depends,
    Request,
    HTTPException,
    WebSocket,
    WebSocketDisconnect,
    status,
    Response
)
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
import asyncio, json

from app.schemas.diffusion import DiffuseRequest, DiffuseResponse, WSStartPayload
from app.services.diffusion_service import (
    DiffusionService,
    DiffuseWSService,
    get_last_beta_array,
)
from app.db.session import get_db
from app.services.auth_service import AuthService
from app.repositories.user_repo import UserRepo
from app.models.user import User
from app.core.security import verify_csrf
from app.domain.ImageProcessor import ImageProcessor


router = APIRouter(prefix="", tags=["Diffusion"])


# ----------------------
# Dependencies
# ----------------------
async def get_current_user_dep(
    request: Request, db: AsyncSession = Depends(get_db)
) -> User:
    auth_service = AuthService(UserRepo(db))
    return await auth_service.get_current_user(request)

@router.post("/diffuse", response_model=DiffuseResponse)
async def diffuse(
    req: DiffuseRequest,
    current_user: User = Depends(get_current_user_dep),
    csrf_ok: None = Depends(verify_csrf),
):
    """Run fast diffusion (POST requires CSRF + auth)."""
    try:
        return DiffusionService.fast_diffusion(req)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Diffusion failed: {e}")


@router.get("/diffuse/{t}")
async def diffuse_t(
    t: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_dep),
):
    """Run standard diffusion (auth required)."""
    try:
        diffused = await DiffusionService.standard_diffusion(t, db, current_user)
        binary_data = ImageProcessor.array_to_binary(diffused)
        return Response(content=binary_data, media_type="image/jpeg")
    except Exception as e:
        return {"Error": f"{e}"}


@router.get("/schedule")
async def schedule(current_user: User = Depends(get_current_user_dep)):
    """Return the last beta schedule (auth required)."""
    print("HDKSHKDSD")
    array = get_last_beta_array()
    if array:
        return array
    else:
        raise HTTPException(status_code=400, detail="Please run diffusion to generate")

@router.websocket("/diffuse/ws")
async def diffuse_ws(ws: WebSocket):
    await ws.accept()
    task: Optional[asyncio.Task] = None
    try:
        start_msg = await ws.receive_json()
        payload = WSStartPayload(**start_msg)

        task = asyncio.create_task(DiffuseWSService.run_diffusion(ws, payload))

        while True:
            other = await ws.receive_text()
            try:
                cmd = json.loads(other)
                if cmd.get("action") == "cancel" and task and not task.done():
                    task.cancel()
                    await ws.send_text(json.dumps({"status": "canceled"}))
                    await ws.close()
                    break
            except Exception:
                pass

    except WebSocketDisconnect:
        if task and not task.done():
            task.cancel()
    except asyncio.CancelledError:
        pass
    except Exception as e:
        try:
            await ws.send_text(json.dumps({"status": "error", "detail": str(e)}))
        finally:
            await ws.close()

