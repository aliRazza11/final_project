export default function Controls({ diffusion, setDiffusion, mode, setMode }) {
  return (
    <div className=" flex flex-wrap justify-center items-center gap-6 text-center">
      {/* Mode */}
      <div className="flex flex-col items-center">
        <label className="text-sm font-medium text-gray-700 mb-1">Mode</label>
        <select
          className="px-3 py-2 rounded-lg border border-gray-300 bg-white text-sm"
          value={mode}
          onChange={(e) => setMode(e.target.value)}
        >
          <option value="fast">Fast diffusion (REST)</option>
          <option value="slow">Slow diffusion (WebSocket)</option>
        </select>
      </div>

      {/* Steps */}
      <div className="flex flex-col items-center">
        <label className="text-sm font-medium text-gray-700 mb-1">
          Steps: {diffusion.steps}
        </label>
        <input
          type="range"
          min="1"
          max="1000"
          value={diffusion.steps}
          onChange={(e) =>
            setDiffusion((p) => ({ ...p, steps: e.target.value }))
          }
          className="w-64 accent-black"
        />
      </div>

      {/* Beta Min */}
      <div className="flex flex-col items-center">
        <label className="text-sm font-medium text-gray-700 mb-1">Beta Min</label>
        <input
          type="number"
          value={diffusion.betaMin}
          onChange={(e) =>
            setDiffusion((p) => ({ ...p, betaMin: e.target.value }))
          }
          className="border border-gray-300 rounded px-2 py-1 w-24 text-center"
        />
      </div>

      {/* Beta Max */}
      <div className="flex flex-col items-center">
        <label className="text-sm font-medium text-gray-700 mb-1">Beta Max</label>
        <input
          type="number"
          value={diffusion.betaMax}
          onChange={(e) =>
            setDiffusion((p) => ({ ...p, betaMax: e.target.value }))
          }
          className="border border-gray-300 rounded px-2 py-1 w-24 text-center"
        />
      </div>

      {/* Schedule */}
      <div className="flex flex-col items-center">
        <label className="text-sm font-medium text-gray-700 mb-1">Schedule</label>
        <select
          value={diffusion.schedule}
          onChange={(e) =>
            setDiffusion((p) => ({ ...p, schedule: e.target.value }))
          }
          className="border border-gray-300 rounded px-2 py-1"
        >
          <option value="linear">Linear</option>
          <option value="cosine">Cosine</option>
        </select>
      </div>
    </div>
  );
}
