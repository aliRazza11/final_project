import { useState } from "react";

export default function Controls({ diffusion, setDiffusion, mode, setMode }) {
  const [editingSteps, setEditingSteps] = useState(false);
  const [tempSteps, setTempSteps] = useState(diffusion.steps);

  // validation ranges from backend schema
  const betaMinRange = { min: 0.001, max: 0.001 };
  const betaMaxRange = { min: 0.001, max: 0.02 };

  const isBetaMinValid =
    diffusion.betaMin >= betaMinRange.min && diffusion.betaMin <= betaMinRange.max;
  const isBetaMaxValid =
    diffusion.betaMax >= betaMaxRange.min && diffusion.betaMax <= betaMaxRange.max;

  return (
    <div className="flex flex-wrap justify-center items-end gap-6 text-center">
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
        <div className="flex items-center gap-3">
          <input
            type="range"
            min="1"
            max="1000"
            value={diffusion.steps}
            onChange={(e) =>
              setDiffusion((p) => ({ ...p, steps: Number(e.target.value) }))
            }
            className="w-48 accent-black"
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
              className="border border-gray-300 rounded px-2 py-1 h-9 w-20 text-center"
            />
          ) : (
            <span
              className="cursor-pointer font-mono text-sm px-2 py-1 h-9 flex items-center border rounded bg-gray-50 hover:bg-gray-100"
              onClick={() => {
                setTempSteps(diffusion.steps);
                setEditingSteps(true);
              }}
            >
              {diffusion.steps}
            </span>
          )}
        </div>
        <p className="text-xs text-gray-500 mt-1">Allowed range: 1 – 1000</p>
      </div>

      {/* Beta Min */}
      <div className="flex flex-col items-center">
        <label className="text-sm font-medium text-gray-700 mb-1">Beta Min</label>
        <input
          type="number"
          value={diffusion.betaMin}
          onChange={(e) =>
            setDiffusion((p) => ({ ...p, betaMin: Number(e.target.value) }))
          }
          className={`border rounded px-2 py-1 h-9 w-28 text-center ${
            isBetaMinValid ? "border-gray-300" : "border-red-500 bg-red-50"
          }`}
        />
        {!isBetaMinValid && (
          <p className="text-xs text-red-600 mt-1">
            Must be between {betaMinRange.min} and {betaMinRange.max}
          </p>
        )}
      </div>

      {/* Beta Max */}
      <div className="flex flex-col items-center">
        <label className="text-sm font-medium text-gray-700 mb-1">Beta Max</label>
        <input
          type="number"
          value={diffusion.betaMax}
          onChange={(e) =>
            setDiffusion((p) => ({ ...p, betaMax: Number(e.target.value) }))
          }
          className={`border rounded px-2 py-1 h-9 w-28 text-center ${
            isBetaMaxValid ? "border-gray-300" : "border-red-500 bg-red-50"
          }`}
        />
        {!isBetaMaxValid && (
          <p className="text-xs text-red-600 mt-1">
            Must be between {betaMaxRange.min} and {betaMaxRange.max}
          </p>
        )}
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
