# app/domain/Controller.py
import logging
from typing import Optional, Generator, Tuple

import numpy as np

from app.domain.Diffusion import Diffusion
from app.domain.ImageProcessor import ImageProcessor
from app.domain.BetaScheduler import BetaScheduler

logger = logging.getLogger(__name__)


class Controller:
    """
    Controller class that orchestrates the ImageProcessor, BetaScheduler, and Diffusion.

    This acts as the entry point for the web app to:
      - Process input images (decode, resize, normalize).
      - Generate beta schedules and derived parameters.
      - Run diffusion processes and return frames in different formats.
    """

    def __init__(
        self,
        encoded_img: str,
        steps: int,
        beta_start: float,
        beta_end: float,
        beta_schedule: str = "linear",
        *,
        seed: Optional[int] = None,
        max_side: Optional[int] = None,
    ) -> None:
        """
        Initialize the Controller.

        Args:
            encoded_img (str): Base64-encoded input image.
            steps (int): Number of diffusion steps.
            beta_start (float): Starting value of beta schedule.
            beta_end (float): Ending value of beta schedule.
            beta_schedule (str, optional): Type of beta schedule ("linear" or "cosine"). Defaults to "linear".
            seed (Optional[int], optional): Random seed for reproducibility. Defaults to None.
            max_side (Optional[int], optional): Resize max dimension of input image. Defaults to None.
        """
        logger.info(
            "Initializing Controller with steps=%d, schedule=%s, beta_start=%g, beta_end=%g, seed=%s",
            steps, beta_schedule, beta_start, beta_end, seed,
        )
        # --- Image processing ---
        ip = ImageProcessor(encoded_img)
        decoded = ip.decode_image()
        resized = ip.resize(decoded, max_side=max_side)
        self.x0 = ip.normalize_img(resized)

        # --- Beta schedule ---
        sched = BetaScheduler(steps, beta_schedule, beta_start, beta_end)
        self.beta = sched.beta
        alpha = sched.alpha
        alpha_bar = sched.alpha_bar
        sqrt_alpha_bar = sched.get_all().sqrt_alpha_bar
        sqrt_one_minus_alpha_bar = sched.get_all().sqrt_one_minus_alpha_bar
        sqrt_one_minus_beta = sched.get_all().sqrt_one_minus_beta

        # --- Diffusion core ---
        self.diffusion = Diffusion(
            self.x0,
            self.beta,
            alpha,
            alpha_bar,
            sqrt_alpha_bar,
            sqrt_one_minus_alpha_bar,
            sqrt_one_minus_beta,
            seed=int(seed if seed is not None else np.random.SeedSequence().entropy),
        )
        self._ip = ip  # keep reference for encoding outputs

    # ---------- Public APIs ----------

    def frame_as_base64(
        self, t: int, *, format: str = "JPEG", quality: int = 90, data_url: bool = False
    ) -> str:
        """
        Get a diffused frame at a given timestep as a base64 string or data URL.

        Args:
            t (int): Diffusion timestep.
            format (str, optional): Output image format. Defaults to "JPEG".
            quality (int, optional): Image quality (0–100). Defaults to 90.
            data_url (bool, optional): If True, returns data URL instead of plain base64. Defaults to False.

        Returns:
            str: Base64 or data URL string of the frame.
        """
        temp = self.diffusion.closed_form_diffusion(t)
        arr = ImageProcessor.uint8_from_float01(temp)
        if data_url:
            return self._ip.array_to_data_url(arr, format=format, quality=quality)
        return self._ip.array_to_base64(arr, format=format, quality=quality)

    def get_frame_array(self, t: int) -> np.ndarray:
        """
        Get a diffused frame at a given timestep as a numpy array.

        Args:
            t (int): Diffusion timestep.

        Returns:
            np.ndarray: Frame as uint8 numpy array.
        """
        temp = self.diffusion.iterative_diffusion(t)
        return ImageProcessor.uint8_from_float01(temp)

    def iter_frames(self) -> Generator[Tuple[int, float, np.ndarray], None, None]:
        """
        Stream frames across all timesteps.

        Yields:
            Generator[Tuple[int, float, np.ndarray]]:
                (timestep, beta value, frame array).
        """
        # frame = self.diffusion.frames()
        # print(type(frame))
        # return ImageProcessor.uint8_from_float01(frame)
        return self.diffusion.frames()

    def compare_frames(self, xt1: np.ndarray, xt0: np.ndarray) -> dict:
        """
        Compare two frames and compute similarity/degradation metrics.

        Args:
            xt1 (np.ndarray): First frame.
            xt0 (np.ndarray): Second frame.

        Returns:
            dict: Dictionary of computed metrics (e.g., PSNR, SSIM).
        """
        return self.diffusion.compute_metrics(xt1, xt0)