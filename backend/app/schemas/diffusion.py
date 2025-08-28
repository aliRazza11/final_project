# app/schemas/diffusion.py
from typing import Literal, Optional
from pydantic import BaseModel, Field, field_validator


class DiffuseRequest(BaseModel):
    image_b64: str = Field(
        ...,
        description="Raw base64 or data URL: data:image/jpeg;base64,..."
    )
    steps: int = Field(..., ge=1, le=1000)
    schedule: Literal["linear", "cosine"] = "linear"
    seed: Optional[int] = None

    # Optional override for beta range
    beta_start: float = Field(0.001, ge=1e-8, le=0.001)
    beta_end: float = Field(0.02, ge=1e-8, le=0.02)

    return_data_url: bool = True  # return data URL for easy <img src=...>

class DiffuseResponse(BaseModel):
    image: str  # base64 or data URL depending on return_data_url
    t: int      # the timestep used


class WSStartPayload(BaseModel):
    image_b64: str = Field(..., description="data URL or raw base64")
    steps: int = Field(..., ge=1, le=1000)
    schedule: Literal["linear", "cosine"] = "linear"
    seed: Optional[int] = None

    # ✅ Properly-typed, validated fields (defaults provided)
    beta_start: float = Field(1e-3, ge=1e-8, le=0.001)
    beta_end: float = Field(2e-2, ge=1e-8, le=0.02)

    preview_every: int = Field(1, ge=1, description="Emit a preview every N steps")
    quality: int = Field(85, ge=1, le=100)
    data_url: bool = True
    include_metrics: bool = False