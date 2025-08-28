# app/domain/Diffusion.py
from __future__ import annotations
import logging
from typing import Generator, Tuple
import numpy as np

logger = logging.getLogger(__name__)


def _mix_seed(seed: int, t: int) -> int:
    """
    Mix a base seed with a timestep `t` to produce a deterministic
    but unique seed for that specific step.

    This ensures that random noise is reproducible across runs
    (given the same base seed), but also varies per timestep.

    Args:
        seed (int): Base random seed.
        t (int): Current timestep.

    Returns:
        int: Mixed 32-bit integer seed for timestep `t`.
    """
    return (seed ^ (t * 0x9E3779B1)) & 0xFFFFFFFF


class Diffusion:
    """
    Implements the **core forward diffusion process** used in
    denoising diffusion models.

    - Operates directly on numpy arrays (pure math).
    - Does not depend on higher-level abstractions like
      encoders/decoders or schedulers beyond the arrays passed in.
    - Provides both exact iterative diffusion and closed-form
      diffusion sampling.
    - Includes utility functions for generating frames and computing
      similarity metrics.

    Attributes:
        x0 (np.ndarray): Original clean input image (normalized to [0, 1]).
        img_shape (tuple): Shape of the input image.
        steps (int): Total number of diffusion steps.
        beta (np.ndarray): Beta schedule values.
        alpha (np.ndarray): Alpha values (1 - beta).
        alpha_bar (np.ndarray): Cumulative product of alphas.
        sqrt_alpha_bar (np.ndarray): Square root of alpha_bar.
        sqrt_one_minus_alpha_bar (np.ndarray): Square root of (1 - alpha_bar).
        sqrt_one_minus_beta (np.ndarray): Square root of (1 - beta).
        _base_seed (int): Base RNG seed for reproducibility.
    """

    def __init__(
        self,
        x0: np.ndarray,
        beta: np.ndarray,
        alpha: np.ndarray,
        alpha_bar: np.ndarray,
        sqrt_alpha_bar: np.ndarray,
        sqrt_one_minus_alpha_bar: np.ndarray,
        sqrt_one_minus_beta: np.ndarray,
        *,
        seed: int,
    ) -> None:
        """
        Initialize a Diffusion instance.

        Args:
            x0 (np.ndarray): Input image (normalized float array).
            beta (np.ndarray): Beta schedule.
            alpha (np.ndarray): Alpha values (1 - beta).
            alpha_bar (np.ndarray): Cumulative product of alphas.
            sqrt_alpha_bar (np.ndarray): Precomputed sqrt(alpha_bar).
            sqrt_one_minus_alpha_bar (np.ndarray): Precomputed sqrt(1 - alpha_bar).
            sqrt_one_minus_beta (np.ndarray): Precomputed sqrt(1 - beta).
            seed (int): Random seed for noise reproducibility.
        """
        if not isinstance(x0, np.ndarray):
            raise TypeError(f"x0 must be a numpy array, got {type(x0)}")
        
        self.x0 = x0
        self.img_shape = x0.shape
        self.steps = len(beta)

        # Schedule arrays
        self.beta = beta
        self.alpha = alpha
        self.alpha_bar = alpha_bar
        self.sqrt_alpha_bar = sqrt_alpha_bar
        self.sqrt_one_minus_alpha_bar = sqrt_one_minus_alpha_bar
        self.sqrt_one_minus_beta = sqrt_one_minus_beta

        self._base_seed = seed
        logger.info(
            "Diffusion ready: steps=%d, shape=%s, seed=%d",
            self.steps, self.img_shape, self._base_seed
        )

    # ---------- Core Math APIs ----------

    def closed_form_diffusion(self, t: int) -> np.ndarray:
        """
        Compute the diffused sample at step `t` using the **closed-form formula**.

        This is O(1) with respect to the number of steps,
        because it directly applies the known formula:

            x_t = sqrt(alpha_bar_t) * x0 + sqrt(1 - alpha_bar_t) * noise

        Args:
            t (int): Timestep index (0 <= t < steps).

        Returns:
            np.ndarray: Noisy sample x_t at timestep `t`.
        """
        if not isinstance(t, int):
            raise TypeError(f"t must be an integer, got {type(t)}")
        try:
            rng = np.random.default_rng(_mix_seed(self._base_seed, t))
            eps = rng.normal(size=self.img_shape, loc=0.0, scale=1.0).astype(np.float32)
            xt = self.sqrt_alpha_bar[t] * self.x0 + self.sqrt_one_minus_alpha_bar[t] * eps
            return xt
        except Exception as e:
            logger.error("Closed-form diffusion failed at t=%d: %s", t, e)
            raise RuntimeError(f"Closed-form diffusion failed at t={t}: {e}")
        # return ImageProcessor.uint8_from_float01(xt)

    def iterative_diffusion(self, t: int) -> np.ndarray:
        """
        Compute the diffused sample at step `t` by **iteratively applying**
        the forward diffusion chain from step 0 → t.

        This is slower (O(t)) but exactly mirrors the original process.

        Args:
            t (int): Timestep index (0 <= t < steps).

        Returns:
            np.ndarray: Noisy sample x_t at timestep `t`.
        """
        if not isinstance(t, int):
            raise TypeError(f"t must be an integer, got {type(t)}")
        try:
            xt = self.x0
            rng = np.random.default_rng(_mix_seed(self._base_seed, t))
            eps_list = rng.normal(size=(t+1, *self.img_shape))
            for i in range(t + 1):
                # eps = rng.normal(size=self.img_shape, loc=0.0, scale=1.0).astype(np.float32)
                xt = self.sqrt_one_minus_beta[i] * xt + np.sqrt(self.beta[i]).astype(np.float32) * eps_list[i]
            return xt
        except Exception as e:
            logger.error("Iterative diffusion failed at t=%d: %s", t, e)
            raise RuntimeError(f"Iterative diffusion failed at t={t}: {e}")
        # return ImageProcessor.uint8_from_float01(xt)

    def frames(self) -> Generator[Tuple[int, float, np.ndarray], None, None]:
        """
        Generate the entire forward diffusion sequence step by step.

        Yields:
            tuple:
                - timestep (int): Current step index.
                - beta (float): Beta value at this step.
                - xt (np.ndarray): Image array after applying noise at this step.

        Note:
            This uses a fresh RNG sequence, so it is not deterministic
            across runs unless you set a global RNG seed before calling.
        """
        try:
            rng = np.random.default_rng()
            xt = self.x0
            for i in range(self.steps):
                eps = rng.normal(size=self.img_shape, loc=0.0, scale=1.0).astype(np.float32)
                xt = self.sqrt_one_minus_beta[i] * xt + np.sqrt(self.beta[i]).astype(np.float32) * eps
                # yield i, float(self.beta[i]), ImageProcessor.uint8_from_float01(xt)
                yield i, float(self.beta[i]), xt
        except Exception as e:
            logger.error("Frame generation failed: %s", e)
            raise RuntimeError(f"Frame generation failed: {e}")
    

    def compute_metrics(self, xt1: np.ndarray, xt0: np.ndarray) -> dict:
        """
        Compute similarity/degradation metrics between two noisy frames.

        Args:
            xt1 (np.ndarray): First image/frame (uint8 or float).
            xt0 (np.ndarray): Second image/frame (uint8 or float).

        Returns:
            dict: Dictionary of metrics, including:
                - "SSIM": Structural Similarity Index.
                - "Cosine": Cosine similarity between flattened arrays.
        """

        return self._compute_metrics(xt1, xt0)
        
    # ---------- Helpers ----------
    
    def _compute_metrics(self, xt1: np.ndarray, xt0: np.ndarray) -> dict:
        """
        Internal helper for computing similarity metrics.

        Implements:
        - SSIM (manual implementation for structural similarity).
        - Cosine similarity (vector-based comparison).

        Args:
            xt1 (np.ndarray): First image.
            xt0 (np.ndarray): Second image.

        Returns:
            dict: {"SSIM": float, "Cosine": float}
        """
        def _ssim_manual(x: np.ndarray, y: np.ndarray, L: int = 255) -> float:
            """
            Simplified SSIM (Structural Similarity Index) implementation.

            Args:
                x (np.ndarray): First image (float or uint8).
                y (np.ndarray): Second image.
                L (int, optional): Dynamic range of pixel values. Defaults to 255.

            Returns:
                float: SSIM score in range [-1, 1], where 1 means identical.
            """
            # Convert to float
            x = x.astype(np.float64)
            y = y.astype(np.float64)

            mu_x = x.mean()
            mu_y = y.mean()
            sigma_x = x.var()
            sigma_y = y.var()
            sigma_xy = ((x - mu_x) * (y - mu_y)).mean()

            C1 = (0.01 * L) ** 2
            C2 = (0.03 * L) ** 2

            return ((2 * mu_x * mu_y + C1) * (2 * sigma_xy + C2)) / \
                ((mu_x**2 + mu_y**2 + C1) * (sigma_x + sigma_y + C2))

        def _cosine_similarity(x: np.ndarray, y: np.ndarray) -> float:
            """
            Compute cosine similarity between two arrays.

            Args:
                x (np.ndarray): First array.
                y (np.ndarray): Second array.

            Returns:
                float: Cosine similarity in range [-1, 1].
            """
            x = x.astype(np.float64).ravel()
            y = y.astype(np.float64).ravel()
            return np.dot(x, y) / (np.linalg.norm(x) * np.linalg.norm(y))
        try:
            return {
                "SSIM": _ssim_manual(xt0, xt1),
                "Cosine": _cosine_similarity(xt0, xt1)
            }
        except Exception as e:
            logger.error("Metric calculation failed: %s", e)
            raise RuntimeError(f"Metric calculation failed: {e}")