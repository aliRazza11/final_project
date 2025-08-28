from fastapi import WebSocket, Depends
from app.domain.Diffusion import Diffusion
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


_last_beta_array: list[float] = []

def get_last_beta_array() -> list[float]:
    return _last_beta_array

class DiffusionService:
    @staticmethod
    def fast_diffusion(req: DiffuseRequest) -> DiffuseResponse:
        inst = Diffusion(
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
        image_out = inst.fast_diffuse_base64(
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
        steps = int(t)
        svc = ImageService(ImageRepo(db))
        images = await svc.list_images(current_user.id)
        image = images[0]
        encoded_img = image.image_data

        encoded_img = Image.open(BytesIO(encoded_img))
        im_arr = np.array(encoded_img)
        encoded_img = ImageProcessor.array_to_base64(im_arr)
        inst = Diffusion(
            encoded_img=str(encoded_img),
            steps=steps,
            beta_start=0.001,
            beta_end=0.02
        )
        global _last_beta_array
        _last_beta_array.clear()
        _last_beta_array = inst.beta.tolist()
        return inst.diffuse_at_t(int(steps-1))


class DiffuseWSService:
    @staticmethod
    async def run_diffusion(ws: WebSocket, payload: WSStartPayload):
        inst = Diffusion(
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
        steps = payload.steps
        stride = max(1, payload.preview_every)

        last_encoded = None
        last_metrics = None
        beta = None

        for t, beta, frame in inst.frames():
            if (t % stride) == 0 or (t == steps - 1):
                # encoded = (
                #     ImageProcessor.array_to_data_url(
                #         frame, format="JPEG", quality=payload.quality
                #     )
                #     if payload.data_url
                #     else ImageProcessor.array_to_base64(
                #         frame, format="JPEG", quality=payload.quality
                #     )
                # )
                encoded = ImageProcessor.array_to_data_url(frame, format="JPEG", quality=payload.quality)

                metrics = None
                if payload.include_metrics:
                    try:
                        metrics = inst.compute_metrics(
                            frame, (inst.x0 * 255.0 + 0.5).astype("uint8")
                        )
                    except Exception:
                        metrics = None

                last_encoded = encoded
                last_metrics = metrics

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
 