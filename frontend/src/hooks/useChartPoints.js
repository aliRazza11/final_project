// src/hooks/useChartPoints.js
import { useMemo } from "react";

/**
 * Derives chart-ready points from timeline frames.
 */
export default function useChartPoints(frames) {
  return useMemo(
    () =>
      frames
        .map((f) => {
          const c = f?.metrics?.Cosine;
          const b = f?.betas;
          return {
            x: f.globalT,
            residual: typeof c === "number" && isFinite(c) ? 1 - c : null,
            beta: typeof b === "number" && isFinite(b) ? b : null,
          };
        })
        .filter((p) => p.residual !== null || p.beta !== null),
    [frames]
  );
}
