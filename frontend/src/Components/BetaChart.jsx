// src/Components/BetaChart.jsx
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  ReferenceLine,
  ReferenceDot,
} from "recharts";

export default function BetaChart({ chartPoints, scrubT, setScrubT }) {
  if (!chartPoints.length) return null;
  const latest = chartPoints[chartPoints.length - 1];

  return (
    <div className="w-full mt-6">
      <div className="text-sm font-medium text-gray-700 mb-2 text-center">
        Beta Schedule
      </div>
      <div className="w-full h-56 bg-white rounded-lg border p-2">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart
            data={chartPoints}
            margin={{ top: 8, right: 16, bottom: 8, left: 0 }}
            onClick={(e) => {
              if (typeof e?.activeLabel === "number") {
                setScrubT(e.activeLabel);
              }
            }}
          >
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="x" />
            <YAxis domain={["auto", "auto"]} />
            <Tooltip
              formatter={(v) =>
                v != null && !isNaN(v) ? Number(v).toExponential(3) : "—"
              }
              labelFormatter={(l) => `global t = ${l}`}
            />
            <Line
              type="monotone"
              dataKey="beta"
              stroke="#16a34a"
              strokeWidth={2}
              dot={false}
              isAnimationActive={false}
            />
            {typeof scrubT === "number" && (
              <ReferenceLine x={scrubT} stroke="#0ea5e9" strokeDasharray="4 3" />
            )}
            {scrubT != null && (
              <ReferenceDot
                x={scrubT}
                y={chartPoints.find((p) => p.x === scrubT)?.beta}
                r={5}
              />
            )}
          </LineChart>
        </ResponsiveContainer>
      </div>
      <div className="mt-1 text-xs text-gray-500 text-center">
        {latest?.beta != null
          ? `Latest: global t=${latest.x}, beta=${latest.beta.toExponential(3)}`
          : `Latest: global t=${latest?.x ?? "—"}, beta=—`}
      </div>
    </div>
  );
}
