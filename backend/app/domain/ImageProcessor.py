# app/domain/ImageProcessor.py
from __future__ import annotations
import base64
import logging
from dataclasses import dataclass
from io import BytesIO
from typing import Optional, Tuple

import numpy as np
from PIL import Image

logger = logging.getLogger(__name__)


class ImageProcessor:
    """Decode/encode base64 images, with optional resizing and validation."""
    def __init__(self, encoded_img: str):
        """
        Initialize the processor with a base64-encoded image.

        Args:
            encoded_img (str): Base64 string (with or without data URL prefix).
        """
        logger.debug("ImageProcessor initialized with encoded image of length %d", len(encoded_img))
        self.encoded_img = encoded_img
        self._decoded_image: Optional[np.ndarray] = None

    # ---------- Decode ----------
    def decode_image(self) -> np.ndarray:
        """
        Decode the base64-encoded image into an RGB numpy array.

        Returns:
            np.ndarray: Decoded image (HxWx3, dtype=uint8).
        """
        try:
            img = self._decode_image(self.encoded_img)
            self._decoded_image = img
            logger.debug("Decoded image stored: shape=%s, dtype=%s", img.shape, img.dtype)
            return img
        except ValueError as e:
            logger.error("Decoding failed: %s", e)
            raise
        except Exception as e:
            logger.error("Decoding failed: %s", e)
            raise  

    def resize(self, img, *, max_side: Optional[int] = None,) -> np.ndarray:
        """
        Resize an image while preserving aspect ratio.

        Args:
            img (np.ndarray): Input image (HxWxC).
            max_side (int, optional): Maximum size of the longer side. If None, no resizing.

        Returns:
            np.ndarray: Resized image (or original if no resizing needed).
        """
        if max_side is not None and max_side > 0:
            h, w = img.shape[:2]
            m = max(h, w)
            if m > max_side:
                scale = max_side / float(m)
                new_size = (max(int(w * scale), 1), max(int(h * scale), 1))
                try:
                    with Image.fromarray(img) as im:
                        im = im.resize(new_size, resample=Image.LANCZOS)
                        img = np.asarray(im, dtype=np.uint8)
                    logger.debug("Image resized to: %s", img.shape)
                except Exception as e:
                    logger.error("Resizing failed: %s", e)
                    raise ValueError(f"Image resizing failed: {e}")
            self._decoded_image = img
        return img
    # ---------- Introspection ----------
    @property
    def shape(self) -> Tuple[int, int, int]:
        """
        Get the shape of the decoded image, decoding if necessary.

        Returns:
            tuple[int, int, int]: Shape of the decoded image (H, W, C).
        """
        if self._decoded_image is None:
            self.decode_image()
        logger.debug("Returning image shape: %s", self._decoded_image.shape)
        return self._decoded_image.shape



    # ---------- Encode helpers (useful for API responses) ----------
    @staticmethod
    def uint8_from_float01(x: np.ndarray, mode: str = "clip") -> np.ndarray:
        """
        Convert float array to uint8 image.
        
        Args:
            x: Input float array.
            mode: "clip" = assume values in [0,1], clip outside.
                "rescale" = min/max rescale to [0,255].
        """
        if not isinstance(x, np.ndarray):
            raise TypeError(f"x must be a numpy array, got {type(x)}")
        if mode == "clip":
            return (np.clip(x, 0, 1) * 255.0 + 0.5).astype(np.uint8)
        elif mode == "rescale":
            x_min, x_max = x.min(), x.max()
            return ((x - x_min) / (x_max - x_min + 1e-8) * 255.0 + 0.5).astype(np.uint8)
        else:
            raise ValueError(f"Unknown mode: {mode}")



    @staticmethod
    def normalize_img(img) -> np.ndarray:
        """
        Normalize uint8 image array to float32 in [0, 1].

        Args:
            img (np.ndarray): Input image array (dtype=uint8).

        Returns:
            np.ndarray: Normalized float32 image.
        """
        try:
            return (img.astype(np.float32) / 255.0).clip(0.0, 1.0)
        except Exception as e:
            raise

    @staticmethod
    def array_to_base64(arr: np.ndarray, format: str = "JPEG", quality: int = 90) -> str:
        """
        Encode a numpy image array to a base64 string (no data URL prefix).

        Args:
            arr (np.ndarray): Input image array (HxW, HxWx1, HxWx3, or HxWx4).
            format (str): Image format (e.g., "JPEG", "PNG").
            quality (int): Quality for lossy formats (JPEG/WebP).

        Returns:
            str: Base64-encoded image string.
        """
        if not isinstance(arr, np.ndarray):
            raise TypeError("arr must be a numpy array")
        try:
            if arr.ndim == 2:  # grayscale
                pil = Image.fromarray(arr, mode="L")
            elif arr.ndim == 3:
                if arr.shape[2] == 1:
                    pil = Image.fromarray(arr.squeeze(-1), mode="L")
                    format = "PNG"  # safer for single-channel
                elif arr.shape[2] == 3:
                    pil = Image.fromarray(arr, mode="RGB")
                elif arr.shape[2] == 4:
                    pil = Image.fromarray(arr, mode="RGBA")
                    if format.upper() == "JPEG":  # JPEG can’t store alpha
                        pil = pil.convert("RGB")
                else:
                    raise ValueError(f"Unsupported channel count: {arr.shape[2]}")
            else:
                raise ValueError("Expected HxW or HxWx{1,3,4} uint8 array.")

            buff = BytesIO()
            save_kwargs = {}
            if format.upper() == "JPEG":
                save_kwargs["quality"] = int(quality)
                save_kwargs["optimize"] = True
            pil.save(buff, format=format, **save_kwargs)
            return base64.b64encode(buff.getvalue()).decode("utf-8")
        except Exception as e:
            logger.error("Base64 encoding failed: %s", e)
            raise ValueError(f"Failed to encode image to base64: {e}")
        

    @staticmethod
    def _strip_data_url_prefix(b64: str) -> str:
        """
        Remove data URL prefix from base64 string if present.

        Args:
            b64 (str): Base64 string (with or without 'data:image/...;base64,').

        Returns:
            str: Cleaned base64 string.
        """
        if not isinstance(b64, str):
            raise TypeError(f"b64 must be a string, got {type(b64)}")
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
        """
        Encode a numpy array to a base64 data URL.

        Args:
            arr (np.ndarray): Input image array.
            format (str): Image format ("JPEG", "PNG", etc.).
            quality (int): Quality for lossy formats.

        Returns:
            str: Full data URL (e.g., 'data:image/jpeg;base64,...').
        """
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
        Convert a numpy image array to raw binary image data.

        Args:
            arr (np.ndarray): Image array (HxW grayscale or HxWxC RGB).
            format (str): Output format ("JPEG", "PNG", "WEBP", etc.).
            quality (int): Quality for lossy formats (JPEG/WebP).

        Returns:
            bytes: Encoded image bytes.
        """
        if not isinstance(arr, np.ndarray):
            raise ValueError("Input must be a numpy array")
        
        try:
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
        except Exception as e:
            logger.error("Binary conversion failed: %s", e)
            raise ValueError(f"Failed to convert array to binary: {e}")



    def _decode_image(self, encoded_img: str) -> np.ndarray:
        """
        Internal: Decode a base64 string into a numpy RGB image.

        Args:
            encoded_img (str): Base64-encoded image string.

        Returns:
            np.ndarray: Decoded image (HxWx3, dtype=uint8).

        Raises:
            ValueError: If decoding fails or image data is invalid.
        """
        try:
            raw = base64.b64decode(self._strip_data_url_prefix(encoded_img), validate=True)
            with Image.open(BytesIO(raw)) as im:
                # Normalize to RGB to keep the rest of the pipeline simple.
                mode = im.mode
                if mode not in ("RGB", "L"):  # only allow grayscale or RGB
                    im = im.convert("RGB")
                arr = np.asarray(im, dtype=np.uint8)
            logger.debug("Image decoded from base64: shape=%s, dtype=%s", arr.shape, arr.dtype)
            return arr
        except Exception as e:
            logger.error("Image decoding failed: %s", e)
            raise ValueError(f"Invalid image data: {e}")