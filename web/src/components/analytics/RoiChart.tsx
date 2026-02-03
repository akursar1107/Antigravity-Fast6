"use client";

import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import type { RoiTrend } from "@/lib/api";

interface RoiChartProps {
  data: RoiTrend[];
}

interface CustomTooltipProps {
  active?: boolean;
  payload?: Array<{ payload: RoiTrend }>;
}

function CustomTooltip({ active, payload }: CustomTooltipProps) {
  if (!active || !payload || payload.length === 0) {
    return null;
  }

  const data = payload[0].payload as RoiTrend;

  return (
    <div className="rounded-lg border border-slate-700 bg-slate-900/95 p-3 shadow-lg">
      <p className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-400">
        Week {data.week}
      </p>
      <div className="mt-2 space-y-1 text-sm">
        <div className="flex items-center justify-between gap-4">
          <span className="text-slate-400">ROI</span>
          <span
            className={`font-semibold ${
              data.roi_dollars >= 0 ? "text-emerald-400" : "text-red-400"
            }`}
          >
            ${data.roi_dollars.toFixed(1)}
          </span>
        </div>
        <div className="flex items-center justify-between gap-4">
          <span className="text-slate-400">Accuracy</span>
          <span className="font-medium text-slate-200">
            {data.accuracy.toFixed(0)}%
          </span>
        </div>
        <div className="flex items-center justify-between gap-4">
          <span className="text-slate-400">Picks</span>
          <span className="font-medium text-slate-200">{data.picks_count}</span>
        </div>
      </div>
    </div>
  );
}

export default function RoiChart({ data }: RoiChartProps) {
  if (data.length === 0) {
    return (
      <div className="flex h-56 flex-col items-center justify-center gap-3 rounded-xl border border-dashed border-slate-700/70 bg-slate-950/40 text-center">
        <div className="text-4xl">📈</div>
        <div>
          <p className="text-lg font-semibold text-slate-300">No data yet</p>
          <p className="mt-1 text-sm text-slate-500">
            ROI trends will appear once picks are graded
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="h-64 w-full" aria-label="ROI trend chart">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data} margin={{ top: 5, right: 20, bottom: 5, left: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#334155" opacity={0.3} />
          <XAxis
            dataKey="week"
            stroke="#64748b"
            tick={{ fill: "#94a3b8", fontSize: 12 }}
            tickLine={false}
            label={{ value: "Week", position: "insideBottom", offset: -5, fill: "#64748b" }}
          />
          <YAxis
            stroke="#64748b"
            tick={{ fill: "#94a3b8", fontSize: 12 }}
            tickLine={false}
            label={{ value: "ROI ($)", angle: -90, position: "insideLeft", fill: "#64748b" }}
          />
          <Tooltip content={<CustomTooltip />} />
          <Line
            type="monotone"
            dataKey="roi_dollars"
            stroke="#6366f1"
            strokeWidth={2}
            dot={{ fill: "#6366f1", r: 4 }}
            activeDot={{ r: 6, fill: "#818cf8" }}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
