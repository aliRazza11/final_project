# app/domain/BetaSchedular.py
from __future__ import annotations
import numpy as np
import logging
from dataclasses import dataclass
from typing import Literal

logger = logging.getLogger(__name__)

ScheduleType = Literal["linear", "cosine"]


@dataclass(frozen=True)
class BetaScheduleResult:
    """
    Container for precomputed diffusion schedule arrays.

    Attributes:
        beta (np.ndarray): Noise variance schedule, shape (T,), float32.
        alpha (np.ndarray): 1 - beta at each step, shape (T,), float32.
        alpha_bar (np.ndarray): Cumulative product of alphas, shape (T,), float32.
        sqrt_alpha_bar (np.ndarray): Square root of alpha_bar, shape (T,), float32.
        sqrt_one_minus_alpha_bar (np.ndarray): Square root of (1 - alpha_bar), shape (T,), float32.
        sqrt_one_minus_beta (np.ndarray): Square root of (1 - beta), shape (T,), float32.
    """
    beta: np.ndarray                # (T,) float32
    alpha: np.ndarray               # (T,) float32
    alpha_bar: np.ndarray           # (T,) float32
    sqrt_alpha_bar: np.ndarray      # (T,) float32
    sqrt_one_minus_alpha_bar: np.ndarray  # (T,) float32
    sqrt_one_minus_beta: np.ndarray       # (T,) float32


class BetaScheduler:
    """
    Scheduler for generating noise schedules in diffusion models
    (e.g., DDPM). Supports linear and cosine schedules.

    Precomputes beta, alpha, alpha_bar, and related square-root
    arrays for numerical stability and efficiency.

    Args:
        steps (int): Total number of diffusion steps (T).
        schedule (ScheduleType, optional): Type of schedule,
            either "linear" or "cosine". Defaults to "linear".
        beta_start (float, optional): Starting beta value for
            the linear schedule. Defaults to 1e-3.
        beta_end (float, optional): Ending beta value for
            the linear schedule. Defaults to 2e-2.
        cosine_s (float, optional): Small constant shift used
            in the cosine schedule. Defaults to 8e-3.
    """

    def __init__(
        self,
        steps: int,
        schedule: ScheduleType = "linear",
        beta_start: float = 1e-3,
        beta_end: float = 2e-2,
        cosine_s: float = 8e-3,  # per Nichol & Dhariwal (cosine schedule)
    ):
        try:  
            self.steps, self.schedule = int(steps), schedule
            self.beta_start, self.beta_end, self.cosine_s = float(beta_start), float(beta_end), float(cosine_s)

            self._computed = self._build()
            logger.info("Built %s schedule with %d steps.", self.schedule, self.steps)

        except Exception as e:
            logger.exception("Failed to initialize BetaScheduler: %s", e)
            raise

    # ---------- Public API ----------
    @property
    def beta(self) -> np.ndarray:
        """
        Returns the beta schedule.

        Returns:
            np.ndarray: Beta values of shape (T,).
        """
        return self._computed.beta

    @property
    def alpha(self) -> np.ndarray:
        """
        Returns the alpha schedule (1 - beta).

        Returns:
            np.ndarray: Alpha values of shape (T,).
        """
        return self._computed.alpha
    @property
    def alpha_bar(self) -> np.ndarray:
        """
        Returns the cumulative product of alphas.

        Returns:
            np.ndarray: Alpha_bar values of shape (T,).
        """
        return self._computed.alpha_bar

    def get_all(self) -> BetaScheduleResult:
        """
        Returns all precomputed arrays in a dataclass.

        Returns:
            BetaScheduleResult: Object containing beta, alpha,
            alpha_bar, sqrt_alpha_bar, sqrt_one_minus_alpha_bar,
            and sqrt_one_minus_beta.
        """
        return self._computed

    # ---------- Internals ----------
    def _build(self) -> BetaScheduleResult:
        logger.info("Building Beta values")
        """
        Constructs the diffusion schedule based on the chosen type.

        For "linear":
            - Beta is linearly interpolated between beta_start and beta_end.

        For "cosine":
            - Alpha_bar follows a cosine schedule (Nichol & Dhariwal).

        Returns:
            BetaScheduleResult: Dataclass containing all computed arrays.
        """
        try:
            logger.info("Building Beta schedule: %s", self.schedule)
            if self.schedule == "linear":
                beta = np.linspace(self.beta_start, self.beta_end, self.steps, dtype=np.float16)
                beta = np.clip(beta, 1e-8, 0.999)  # numerical safety
                alpha = (1.0 - beta).astype(np.float32)
                alpha_bar = np.cumprod(alpha, dtype=np.float32)
            else:
                T = self.steps
                s = self.cosine_s
                ts = np.arange(T, dtype=np.float32)
                f = lambda u: np.cos(((u + s) / (1.0 + s)) * (np.pi / 2.0)) ** 2
                denom = f(0.0)
                alpha_bar = (f(ts / T) / denom).astype(np.float32)
                alpha_bar = np.clip(alpha_bar, 1e-8, 1.0)
                beta = np.empty(T, dtype=np.float32)
                beta[0] = 1.0 - alpha_bar[0]
                prev = alpha_bar[0]
                for t in range(1, T):
                    beta[t] = 1.0 - (alpha_bar[t] / prev)
                    prev = alpha_bar[t]
                beta = np.clip(beta, 1e-8, 0.999)
                alpha = (1.0 - beta).astype(np.float32)
                # Recompute alpha_bar from alpha to stay perfectly consistent
                alpha_bar = np.cumprod(alpha, dtype=np.float32)


            sqrt_alpha_bar = np.sqrt(alpha_bar, dtype=np.float32)
            sqrt_one_minus_alpha_bar = np.sqrt(1.0 - alpha_bar, dtype=np.float32)
            sqrt_one_minus_beta = np.sqrt(1.0 - beta, dtype=np.float32)

        
            return BetaScheduleResult(
                beta=beta,
                alpha=alpha,
                alpha_bar=alpha_bar,
                sqrt_alpha_bar=sqrt_alpha_bar,
                sqrt_one_minus_alpha_bar=sqrt_one_minus_alpha_bar,
                sqrt_one_minus_beta=sqrt_one_minus_beta,
            )
        except Exception as e:
            logger.exception("Error while building the beta schedule: %s", e)
            raise