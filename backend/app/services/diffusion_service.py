# app/services/diffusion_service.py
from fastapi import WebSocket, Depends, WebSocketDisconnect, HTTPException
from app.domain.Controller import Controller
from app.schemas.diffusion import DiffuseRequest, DiffuseResponse, WSStartPayload
from app.domain.ImageProcessor import ImageProcessor
import asyncio, json
from app.services.image_service import ImageService
from app.repositories.image_repo import ImageRepo
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.routers.image_router import get_current_user_dep
from app.models.user import User
from PIL import Image
from io import BytesIO
import numpy as np
from typing import Optional


_last_beta_array: list[float] = []

def get_last_beta_array() -> list[float]:
    """
    Retrieve the last beta schedule used in a diffusion run.

    Returns:
        list[float]: A list of beta values from the most recent diffusion process.
    """
    return _last_beta_array

class DiffusionService:
    """Service layer for handling synchronous (fast/standard) diffusion workflows."""
    @staticmethod
    def fast_diffusion(req: DiffuseRequest) -> DiffuseResponse:
        """
        Run a fast diffusion process from an input image.

        Args:
            req (DiffuseRequest): Diffusion request payload containing:
                - base64-encoded input image
                - number of diffusion steps
                - beta schedule parameters (start, end, type)
                - random seed (optional)

        Returns:
            DiffuseResponse: Contains the base64-encoded output image and
            the final step index.

        Side Effects:
            Updates the global `_last_beta_array` with the beta schedule
            generated during this diffusion run.

        Raises:
            Exception: If diffusion fails internally.
        """
        inst = Controller(
            encoded_img=req.image_b64,
            steps=req.steps,
            beta_start=req.beta_start,
            beta_end=req.beta_end,
            beta_schedule=req.schedule,
            seed=req.seed,
            max_side=None,  # protect server from huge uploads
        )
        global _last_beta_array
        _last_beta_array.clear()
        t = req.steps - 1
        image_out = inst.frame_as_base64(
            t,
            data_url=True,
            format="JPEG",
            quality=92,
        )
        _last_beta_array = inst.beta.tolist()
        # print(_last_beta_array)
        return DiffuseResponse(image=image_out, t=t)

    @staticmethod
    async def standard_diffusion(
        t: str,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user_dep)
    ):
        """
        Run a standard (slower, DB-integrated) diffusion process.

        This method retrieves the most recent stored image for the
        current user, encodes it, and runs diffusion for the specified
        number of steps.

        Args:
            t (str): Number of diffusion steps to perform (string, converted to int).
            db (AsyncSession): SQLAlchemy async session dependency.
            current_user (User): The currently authenticated user.

        Returns:
            np.ndarray: The resulting image array at step (steps - 1).

        Side Effects:
            Updates the global `_last_beta_array` with the beta schedule
            used in this diffusion run.

        Raises:
            Exception: If no images exist for the user or diffusion fails.
        """
        try:
            steps = int(t)
            svc = ImageService(ImageRepo(db))
            images = await svc.list_images(current_user.id)
            image = images[0]
            encoded_img = image.image_data
            encoded_img = Image.open(BytesIO(encoded_img))
            im_arr = np.array(encoded_img)
            print(im_arr.shape)
            encoded_img = ImageProcessor.array_to_base64(im_arr)
            inst = Controller(
                encoded_img=str(encoded_img),
                steps=steps,
                beta_start=0.001,
                beta_end=0.02
            )
            global _last_beta_array
            _last_beta_array.clear()
            _last_beta_array = inst.beta.tolist()
            return inst.get_frame_array(int(steps-1))
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Standard diffusion failed: {str(e)}")
        
    @staticmethod
    async def handle_connection(ws: WebSocket):
        """
        Manage a WebSocket connection for real-time diffusion streaming.

        Workflow:
            1. Accepts the WebSocket connection.
            2. Receives an initial payload (`WSStartPayload`) defining diffusion params.
            3. Streams intermediate diffusion frames back to the client at a
               configurable interval (`preview_every`).
            4. Optionally computes and sends metrics for each frame.
            5. Listens for client commands (e.g., cancel).
            6. Sends a final completion message before closing.

        Args:
            ws (WebSocket): Active WebSocket connection.

        Messages Sent to Client (JSON):
            - `t` (int): Current step index.
            - `beta` (float): Current beta value.
            - `step` (int): Human-readable step count (t + 1).
            - `progress` (float): Progress ratio (0.0–1.0).
            - `image` (str): Base64-encoded image (JPEG).
            - `metrics` (dict, optional): Quality/metric results (if enabled).
            - Final message includes `"status": "done"` or `"status": "canceled"`.

        Raises:
            WebSocketDisconnect: If client disconnects unexpectedly.
            asyncio.CancelledError: If the diffusion task is canceled mid-run.
            Exception: Any unhandled error, sent to client as error message.
        """
        await ws.accept()
        task: Optional[asyncio.Task] = None

        try:
            # Receive first message with diffusion payload
            start_msg = await ws.receive_json()
            payload = WSStartPayload(**start_msg)

            # Setup diffusion instance
            inst = Controller(
                encoded_img=payload.image_b64,
                steps=payload.steps,
                beta_start=payload.beta_start,
                beta_end=payload.beta_end,
                beta_schedule=payload.schedule,
                seed=payload.seed,
                max_side=512,
            )

            global _last_beta_array
            _last_beta_array.clear()
            steps, stride = payload.steps, max(1, payload.preview_every)

            async def diffusion_task():
                last_encoded, last_metrics, beta = None, None, None
                test = []
                for t, beta, frame in inst.iter_frames():
                    frame = ImageProcessor.uint8_from_float01(frame)
                    if (t % stride) == 0 or (t == steps - 1):
                        encoded = ImageProcessor.array_to_data_url(
                            frame, format="JPEG", quality=payload.quality
                        )

                        metrics = None
                        if payload.include_metrics:
                            try:
                                metrics = inst.compare_frames(
                                    frame, (inst.x0 * 255.0 + 0.5).astype("uint8")
                                )
                            except Exception:
                                metrics = None

                        last_encoded, last_metrics = encoded, metrics

                        msg = {
                            "t": t,
                            "beta": beta,
                            "step": t + 1,
                            "progress": (t + 1) / steps,
                            "image": encoded,
                        }
                        if metrics is not None:
                            msg["metrics"] = metrics

                        await ws.send_text(json.dumps(msg))

                    await asyncio.sleep(0)
                    _last_beta_array.append(beta)
                # Send final completion message
                await ws.send_text(json.dumps({
                    "status": "done",
                    "t": steps - 1,
                    "beta": beta,
                    "step": steps,
                    "progress": 1.0,
                    "image": last_encoded,
                    **({"metrics": last_metrics} if last_metrics is not None else {}),
                }))
                await ws.close()

            # Start diffusion loop
            task = asyncio.create_task(diffusion_task())

            # Listen for client commands
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
                    continue

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
