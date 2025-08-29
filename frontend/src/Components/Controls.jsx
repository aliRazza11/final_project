import { useState, useEffect } from "react";

export default function Controls({ diffusion, setDiffusion, mode, setMode }) {
  const [editingSteps, setEditingSteps] = useState(false);
  const [tempSteps, setTempSteps] = useState(diffusion.steps);

  // Both betaMin & betaMax share same limits
  const betaRange = { min: 0.0001, max: 1, defaultMin: 0.001, defaultMax: 0.02 };

  useEffect(() => {
    setDiffusion((prev) => ({
      ...prev,
      betaMin: prev.betaMin ?? betaRange.defaultMin,
      betaMax: prev.betaMax ?? betaRange.defaultMax,
      steps: prev.steps ?? 100,
      schedule: prev.schedule ?? "linear",
    }));
  }, []);

  // clamp helper
  const clamp = (val, min, max, fallback) => {
    if (Number.isNaN(val)) return fallback;
    if (val < min) return fallback;
    if (val > max) return fallback;
    return val;
  };

  return (
    <div className="flex flex-wrap justify-center items-start gap-4 md:gap-8 lg:gap-16 text-center">
      {/* Mode */}
      <div className="flex flex-col items-center">
        <label className="text-sm font-medium text-gray-700 mb-1">Mode</label>
        <select
          className="px-3 py-1.5 h-9 rounded-lg border border-gray-300 bg-white text-sm"
          value={mode}
          onChange={(e) => setMode(e.target.value)}
        >
          <option value="fast">Fast Diffusion</option>
          <option value="slow">Diffusion</option>
        </select>
      </div>

      {/* Steps */}
      <div className="flex flex-col items-center">
        <label className="text-sm font-medium text-gray-700 mb-1">Steps</label>

        <div className="hidden sm:flex items-center gap-3">
          <input
            type="range"
            min="1"
            max="1000"
            value={diffusion.steps}
            onChange={(e) =>
              setDiffusion((p) => ({ ...p, steps: Number(e.target.value) }))
            }
            className="w-48 h-9 accent-black"
          />

          {editingSteps ? (
            <input
              type="number"
              min="1"
              max="1000"
              value={tempSteps}
              autoFocus
              onChange={(e) => setTempSteps(e.target.value)}
              onBlur={() => {
                let val = Number(tempSteps);
                if (Number.isNaN(val) || val < 1) val = 1;
                if (val > 1000) val = 1000;
                setDiffusion((p) => ({ ...p, steps: val }));
                setEditingSteps(false);
              }}
              onKeyDown={(e) => {
                if (e.key === "Enter") e.currentTarget.blur();
                if (e.key === "Escape") {
                  setTempSteps(diffusion.steps);
                  setEditingSteps(false);
                }
              }}
              className="border border-gray-300 rounded px-2 py-0.5 h-7 w-16 text-center"
            />
          ) : (
            <span
              className="cursor-pointer font-mono text-sm px-2 py-0.5 h-7 flex items-center border rounded bg-gray-50 hover:bg-gray-100"
              onClick={() => {
                setTempSteps(diffusion.steps);
                setEditingSteps(true);
              }}
            >
              {diffusion.steps}
            </span>
          )}
        </div>

        <div className="sm:hidden w-24">
          <input
            type="number"
            min="1"
            max="1000"
            value={diffusion.steps}
            onChange={(e) =>
              setDiffusion((p) => ({ ...p, steps: Number(e.target.value) }))
            }
            className="border border-gray-300 rounded px-2 py-1 h-9 w-full text-center"
          />
        </div>
      </div>

      {/* Beta Min */}
      <div className="flex flex-col items-center">
        <label className="text-sm font-medium text-gray-700 mb-1">Beta Min</label>
        <input
          type="number"
          step="0.0001"
          value={diffusion.betaMin}
          onBlur={(e) => {
            const val = clamp(Number(e.target.value), betaRange.min, betaRange.max, betaRange.defaultMin);
            setDiffusion((p) => ({ ...p, betaMin: val }));
          }}
          onChange={(e) =>
            setDiffusion((p) => ({ ...p, betaMin: Number(e.target.value) }))
          }
          className="border border-gray-300 rounded px-2 py-1 h-9 w-28 text-center"
        />
        <p className="text-xs text-gray-500 mt-1">
          Range {betaRange.min} – {betaRange.max}
        </p>
      </div>

      {/* Beta Max */}
      <div className="flex flex-col items-center">
        <label className="text-sm font-medium text-gray-700 mb-1">Beta Max</label>
        <input
          type="number"
          step="0.0001"
          value={diffusion.betaMax}
          onBlur={(e) => {
            const val = clamp(Number(e.target.value), betaRange.min, betaRange.max, betaRange.defaultMax);
            setDiffusion((p) => ({ ...p, betaMax: val }));
          }}
          onChange={(e) =>
            setDiffusion((p) => ({ ...p, betaMax: Number(e.target.value) }))
          }
          className="border border-gray-300 rounded px-2 py-1 h-9 w-28 text-center"
        />
        <p className="text-xs text-gray-500 mt-1">
          Range {betaRange.min} – {betaRange.max}
        </p>
      </div>

      {/* Schedule */}
      <div className="flex flex-col items-center">
        <label className="text-sm font-medium text-gray-700 mb-1">Schedule</label>
        <select
          value={diffusion.schedule}
          onChange={(e) =>
            setDiffusion((p) => ({ ...p, schedule: e.target.value }))
          }
          className="border border-gray-300 rounded px-2 py-1 h-9"
        >
          <option value="linear">Linear</option>
          <option value="cosine">Cosine</option>
        </select>
      </div>
    </div>
  );
}
