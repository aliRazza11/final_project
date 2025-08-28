from __future__ import annotations
import numpy as np
import logging
from dataclasses import dataclass
from typing import Literal

logger = logging.getLogger(__name__)

ScheduleType = Literal["linear", "cosine"]


@dataclass(frozen=True)
class BetaScheduleResult:
    beta: np.ndarray                # (T,) float32
    alpha: np.ndarray               # (T,) float32
    alpha_bar: np.ndarray           # (T,) float32
    sqrt_alpha_bar: np.ndarray      # (T,) float32
    sqrt_one_minus_alpha_bar: np.ndarray  # (T,) float32
    sqrt_one_minus_beta: np.ndarray       # (T,) float32


class BetaScheduler:
    """
    Produces DDPM-style noise schedules with all commonly-used
    derived arrays precomputed for speed & stability.
    """

    def __init__(
        self,
        steps: int,
        schedule: ScheduleType = "linear",
        beta_start: float = 1e-3,
        beta_end: float = 2e-2,
        cosine_s: float = 8e-3,  # per Nichol & Dhariwal (cosine schedule)
    ):
        
        self.steps, self.schedule = int(steps), schedule
        self.beta_start, self.beta_end, self.cosine_s = float(beta_start), float(beta_end), float(cosine_s)

        self._res = self._build()
        logger.info("Built %s schedule with %d steps.", self.schedule, self.steps)

    # ---------- Public API ----------
    def get_beta(self) -> np.ndarray:
        return self._res.beta

    def get_alpha(self) -> np.ndarray:
        return self._res.alpha

    def get_alpha_bar(self) -> np.ndarray:
        return self._res.alpha_bar

    def get_all(self) -> BetaScheduleResult:
        return self._res

    # ---------- Internals ----------
    def _build(self) -> BetaScheduleResult:
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

        logger.info("Built %s schedule with %d steps.", self.schedule, self.steps)
        
        return BetaScheduleResult(
            beta=beta,
            alpha=alpha,
            alpha_bar=alpha_bar,
            sqrt_alpha_bar=sqrt_alpha_bar,
            sqrt_one_minus_alpha_bar=sqrt_one_minus_alpha_bar,
            sqrt_one_minus_beta=sqrt_one_minus_beta,
        )
