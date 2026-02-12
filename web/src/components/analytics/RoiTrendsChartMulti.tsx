"use client";

import React, { useMemo } from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
} from "recharts";
import type { RoiTrendByUser } from "@/lib/api";

const CHART_COLORS = [
  "#8C302C", // Deep Tanager - primary/first user
  "#A2877D", // Bronze
  "#234058", // Salty Dog
  "#64748b", // Muted
  "#94a3b8", // Light
];

function transformToChartData(
  raw: RoiTrendByUser[]
): Array<Record<string, string | number>> {
  if (raw.length === 0) return [];

  // Get unique weeks and users
  const weeks = [...new Set(raw.map((r) => r.week))].sort((a, b) => a - b);
  const users = [...new Set(raw.map((r) => r.user_name))].sort();

  // Build cumulative ROI per user (running total)
  const cumulativeByUser = new Map<string, Map<number, number>>();
  for (const user of users) {
    cumulativeByUser.set(user, new Map());
  }
  for (const row of raw) {
    const userMap = cumulativeByUser.get(row.user_name)!;
    const prev = userMap.get(row.week - 1) ?? 0;
    userMap.set(row.week, prev + row.roi_dollars);
  }

  return weeks.map((week) => {
    const row: Record<string, string | number> = {
      week: `W${week}`,
      weekNum: week,
    };
    for (const user of users) {
      const cum = cumulativeByUser.get(user)?.get(week);
      row[user] = cum ?? 0;
    }
    return row;
  });
}

interface RoiTrendsChartMultiProps {
  data?: RoiTrendByUser[];
}

export default function RoiTrendsChartMulti({ data = [] }: RoiTrendsChartMultiProps) {
  const chartData = useMemo(
    () => transformToChartData(data),
    [data]
  );
  const users = useMemo(
    () => [...new Set(data.map((r) => r.user_name))].sort(),
    [data]
  );

  if (chartData.length === 0) {
    return (
      <div className="w-full h-[250px] mt-4 font-mono flex items-center justify-center text-[#78716c] text-sm">
        No ROI data yet
      </div>
    );
  }

  return (
    <div className="w-full h-[250px] mt-4 font-mono">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={chartData}>
          <CartesianGrid
            strokeDasharray="2 2"
            stroke="#234058"
            vertical={true}
            opacity={0.15}
          />
          <XAxis
            dataKey="week"
            axisLine={false}
            tickLine={false}
            tick={{
              fill: "#234058",
              fontSize: 10,
              fontWeight: "bold",
              fontFamily: "monospace",
              opacity: 0.8,
            }}
            dy={10}
          />
          <YAxis hide={true} domain={["auto", "auto"]} />
          <Tooltip
            contentStyle={{
              backgroundColor: "#F1EEE6",
              border: "2px solid #234058",
              borderRadius: "0px",
              color: "#234058",
            }}
            itemStyle={{
              fontSize: "12px",
              fontFamily: "monospace",
              color: "#234058",
              fontWeight: "bold",
            }}
            labelStyle={{ color: "#A2877D", marginBottom: "5px" }}
            cursor={{
              stroke: "#234058",
              strokeWidth: 1,
              strokeDasharray: "4 4",
            }}
          />
          <ReferenceLine y={0} stroke="#94a3b8" strokeWidth={2} />
          {users.map((user, i) => (
            <Line
              key={user}
              type="step"
              dataKey={user}
              name={user}
              stroke={CHART_COLORS[i % CHART_COLORS.length]}
              strokeWidth={i === 0 ? 3 : 2}
              dot={i === 0 ? { r: 3, fill: CHART_COLORS[0] } : false}
              activeDot={
                i === 0
                  ? { r: 6, stroke: "#F1EEE6", strokeWidth: 2 }
                  : { r: 4 }
              }
              opacity={i === 0 ? 1 : 0.8}
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
