# app/routers/diffusion_router.py

"""
Diffusion Router
================

This module defines the FastAPI routes for image diffusion functionality,
including synchronous API endpoints and WebSocket streaming for diffusion
progress updates. Authentication and CSRF validation are enforced where
necessary. The routes rely on the `DiffusionService`,
and related domain/service classes.
"""

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
    get_last_beta_array,
)
from app.db.session import get_db
from app.services.auth_service import AuthService
from app.repositories.user_repo import UserRepository
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
    """
    Dependency to retrieve the currently authenticated user.

    Args:
        request (Request): The incoming HTTP request.
        db (AsyncSession): Database session dependency.

    Returns:
        User: The currently authenticated user instance.

    Raises:
        HTTPException: If authentication fails or user is invalid.
    """
    auth_service = AuthService(UserRepository(db))
    return await auth_service.get_current_user(request)


@router.post("/diffuse", response_model=DiffuseResponse)
async def diffuse(
    req: DiffuseRequest,
    current_user: User = Depends(get_current_user_dep),
    csrf_ok: None = Depends(verify_csrf),
):
    """
    Run fast diffusion process.

    - Requires CSRF validation and user authentication.
    - Uses the `DiffusionService.fast_diffusion` method.

    Args:
        req (DiffuseRequest): Input payload containing diffusion parameters.
        current_user (User): The authenticated user (injected dependency).
        csrf_ok (None): Dependency to enforce CSRF token validation.

    Returns:
        DiffuseResponse: The diffusion output data.

    Raises:
        HTTPException: If the diffusion process fails.
    """
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
    """
    Run standard diffusion process.

    - Requires user authentication.
    - Stores and retrieves results from the database.

    Args:
        t (str): Diffusion input string.
        db (AsyncSession): Database session dependency.
        current_user (User): Authenticated user.

    Returns:
        Response: JPEG image of the diffused output.

    Raises:
        HTTPException: If the diffusion process fails.
    """
    try:
        diffused = await DiffusionService.standard_diffusion(t, db, current_user)
        binary_data = ImageProcessor.array_to_binary(diffused)
        return Response(content=binary_data, media_type="image/jpeg")
    except Exception as e:
        return {"Error": f"{e}"}


@router.get("/schedule")
async def schedule(current_user: User = Depends(get_current_user_dep)):
    """
    Retrieve the most recent beta schedule used in diffusion.

    - Requires user authentication.
    - Returns an array representing the last generated beta schedule.

    Args:
        current_user (User): The authenticated user.

    Returns:
        list | numpy.ndarray: The last beta schedule.

    Raises:
        HTTPException: If no schedule is available.
    """
    array = get_last_beta_array()
    if array:
        return array
    else:
        raise HTTPException(status_code=400, detail="Please run diffusion to generate")


@router.websocket("/diffuse/ws")
async def diffuse_ws(ws: WebSocket):
    """
    WebSocket endpoint for real-time diffusion streaming.

    - Accepts a WebSocket connection.
    - Delegates handling to `DiffuseWSService.handle_connection`.

    Args:
        ws (WebSocket): WebSocket connection instance.

    Returns:
        None
    """
    await DiffusionService.handle_connection(ws)
