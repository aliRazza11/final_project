export default function ModeSelector({ value, onChange }) {
  return (
    <div className="flex items-center gap-3">
      <label className="text-sm font-medium text-gray-700">Mode</label>
      <select
        className="px-3 py-2 rounded-lg border border-gray-300 bg-white text-sm"
        value={value}
        onChange={(e) => onChange(e.target.value)}
      >
        <option value="fast">Fast diffusion (REST)</option>
        <option value="slow">Slow diffusion (WebSocket)</option>
      </select>
    </div>
  );
}
