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
    <div className="rounded-lg border-2 border-[#234058] bg-[#F1EEE6] p-3 shadow-lg font-mono">
      <p className="text-[10px] font-bold uppercase tracking-[0.2em] text-[#78716c]">
        Week {data.week}
      </p>
      <div className="mt-2 space-y-1 text-sm">
        <div className="flex items-center justify-between gap-4">
          <span className="text-[#78716c]">ROI</span>
          <span
            className={`font-bold ${
              data.roi_dollars >= 0 ? "text-[#15803d]" : "text-[#8C302C]"
            }`}
          >
            ${data.roi_dollars.toFixed(1)}
          </span>
        </div>
        <div className="flex items-center justify-between gap-4">
          <span className="text-[#78716c]">Accuracy</span>
          <span className="font-bold text-[#234058]">
            {data.accuracy.toFixed(0)}%
          </span>
        </div>
        <div className="flex items-center justify-between gap-4">
          <span className="text-[#78716c]">Picks</span>
          <span className="font-bold text-[#234058]">{data.picks_count}</span>
        </div>
      </div>
    </div>
  );
}

export default function RoiChart({ data }: RoiChartProps) {
  if (data.length === 0) {
    return (
      <div className="flex h-56 flex-col items-center justify-center gap-3 rounded-lg border-2 border-dashed border-[#d1d5db] bg-[#F1EEE6] text-center font-mono">
        <div className="text-4xl">📈</div>
        <div>
          <p className="text-lg font-bold text-[#234058]">No data yet</p>
          <p className="mt-1 text-sm text-[#78716c]">
            ROI trends will appear once picks are graded
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="h-64 w-full font-mono" aria-label="ROI trend chart">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data} margin={{ top: 5, right: 20, bottom: 5, left: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#234058" opacity={0.15} />
          <XAxis
            dataKey="week"
            stroke="#78716c"
            tick={{ fill: "#234058", fontSize: 10, fontFamily: "monospace", fontWeight: "bold" }}
            tickLine={false}
            label={{ value: "Week", position: "insideBottom", offset: -5, fill: "#78716c" }}
          />
          <YAxis
            stroke="#78716c"
            tick={{ fill: "#234058", fontSize: 10, fontFamily: "monospace", fontWeight: "bold" }}
            tickLine={false}
            label={{ value: "ROI ($)", angle: -90, position: "insideLeft", fill: "#78716c" }}
          />
          <Tooltip content={<CustomTooltip />} />
          <Line
            type="monotone"
            dataKey="roi_dollars"
            stroke="#8C302C"
            strokeWidth={2}
            dot={{ fill: "#8C302C", r: 4 }}
            activeDot={{ r: 6, fill: "#8C302C", stroke: "#F1EEE6", strokeWidth: 2 }}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
