from __future__ import annotations
import base64
import logging
from dataclasses import dataclass
from io import BytesIO
from typing import Optional, Tuple

import numpy as np
from PIL import Image

logger = logging.getLogger(__name__)



@dataclass
class ImageProcessor:
    """Decode/encode base64 images, with optional resizing and validation."""
    encoded_img: str
    _decoded_image: Optional[np.ndarray] = None  # HxWxC uint8

    # ---------- Decode ----------
    def decode_image(self) -> np.ndarray:
        """Decode into HxWx3 uint8; optionally resize (preserving aspect)."""
        img = self._decode_image(self.encoded_img)
        self._decoded_image = img
        return img

    def resize(self, img, *, max_side: Optional[int] = None,) -> np.ndarray:
        if max_side is not None and max_side > 0:
            h, w = img.shape[:2]
            m = max(h, w)
            if m > max_side:
                scale = max_side / float(m)
                new_size = (max(int(w * scale), 1), max(int(h * scale), 1))
                with Image.fromarray(img) as im:
                    im = im.resize(new_size, resample=Image.LANCZOS)
                    img = np.asarray(im, dtype=np.uint8)
                logger.debug("Image resized to: %s", img.shape)
            self._decoded_image = img
        return img
    # ---------- Introspection ----------
    def get_shape(self) -> Tuple[int, int, int]:
        if self._decoded_image is None:
            raise RuntimeError("Image not decoded yet. Call decode_image() first.")
        return self._decoded_image.shape

    # ---------- Encode helpers (useful for API responses) ----------


    @staticmethod
    def normalize_img(img):
        return (img.astype(np.float32) / 255.0).clip(0.0, 1.0)

    @staticmethod
    def array_to_base64(
        arr: np.ndarray,
        format: str = "JPEG",
        quality: int = 90,
    ) -> str:
        """
        Encode an HxWx{1,3} uint8 numpy array to raw base64 (no data URL prefix).
        """
        if arr.ndim == 2:
            mode = "L"
            pil = Image.fromarray(arr, mode=mode)
        elif arr.ndim == 3 and arr.shape[2] in (1, 3):
            if arr.shape[2] == 1:
                pil = Image.fromarray(arr.squeeze(-1), mode="L")
                format = "PNG"  # safer for single-channel if caller didn't specify
            else:
                pil = Image.fromarray(arr, mode="RGB")
        else:
            raise ValueError("Expected HxW or HxWx{1,3} uint8 array.")
        buff = BytesIO()
        save_kwargs = {}
        if format.upper() == "JPEG":
            save_kwargs["quality"] = int(quality)
            save_kwargs["optimize"] = True
        pil.save(buff, format=format)
        return base64.b64encode(buff.getvalue()).decode("utf-8")
    
    @staticmethod
    def _strip_data_url_prefix(b64: str) -> str:
        # Accept both raw base64 and data URLs: data:image/png;base64,XXXX
        if "," in b64 and b64.strip().lower().startswith("data:"):
            return b64.split(",", 1)[1]
        return b64



    @staticmethod
    def array_to_data_url(
        arr: np.ndarray,
        format: str = "JPEG",
        quality: int = 90,
    ) -> str:
        mime = {
            "JPEG": "image/jpeg",
            "JPG": "image/jpeg",
            "PNG": "image/png",
            "WEBP": "image/webp",
        }.get(format.upper(), "application/octet-stream")
        b64 = ImageProcessor.array_to_base64(arr, format=format, quality=quality)
        return f"data:{mime};base64,{b64}"
    
    @staticmethod
    def array_to_binary(
        arr: np.ndarray,
        format: str = "JPEG",
        quality: int = 90
    ) -> bytes:
        """
        Convert a numpy image array to binary image data.

        Args:
            arr (np.ndarray): Image array (H, W) grayscale or (H, W, C) RGB/RGBA.
            format (str): Output image format ("JPEG", "PNG", "WEBP", etc.).
            quality (int): Image quality (relevant for lossy formats like JPEG/WebP).

        Returns:
            bytes: Encoded image as raw binary.
        """
        if arr is None or not isinstance(arr, np.ndarray):
            raise ValueError("Input must be a numpy array")

        # Ensure valid range and dtype
        if arr.dtype != np.uint8:
            arr = np.clip(arr, 0, 255).astype(np.uint8)

        # Convert grayscale to 2D -> L mode
        if arr.ndim == 2:
            img = Image.fromarray(arr, mode="L")
        else:
            img = Image.fromarray(arr)

        buffer = BytesIO()
        save_kwargs = {}
        if format.upper() in {"JPEG", "WEBP"}:
            save_kwargs["quality"] = quality

        img.save(buffer, format=format.upper(), **save_kwargs)
        return buffer.getvalue()



    def _decode_image(self, encoded_img: str) -> np.ndarray:
        try:
            raw = base64.b64decode(self._strip_data_url_prefix(encoded_img), validate=True)
            with Image.open(BytesIO(raw)) as im:
                # Normalize to RGB to keep the rest of the pipeline simple.
                im = im.convert("RGB")
                arr = np.asarray(im, dtype=np.uint8)
            logger.debug("Image decoded from base64: shape=%s, dtype=%s", arr.shape, arr.dtype)
            return arr
        except Exception as e:
            logger.error("Image decoding failed: %s", e)
            raise ValueError(f"Invalid image data: {e}")