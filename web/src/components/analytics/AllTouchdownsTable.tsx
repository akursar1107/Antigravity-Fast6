"use client";

import { useState, useEffect } from "react";
import type { TouchdownRow } from "@/lib/api";
import { request } from "@/lib/api";

function parseWeekFromGameId(gameId: string): number | null {
  const parts = gameId.split("_");
  if (parts.length >= 2) {
    const w = parseInt(parts[1], 10);
    return isNaN(w) ? null : w;
  }
  return null;
}

type ViewMode = "all" | "first_td_only";

interface AllTouchdownsTableProps {
  season: number;
  initialData: TouchdownRow[];
}

export default function AllTouchdownsTable({ season, initialData }: AllTouchdownsTableProps) {
  const [data, setData] = useState<TouchdownRow[]>(initialData);
  const [filterWeek, setFilterWeek] = useState<number | "">("");
  const [filterTeam, setFilterTeam] = useState("");
  const [viewMode, setViewMode] = useState<ViewMode>("all");
  const [loading, setLoading] = useState(false);

  const weeks = Array.from(
    new Set(
      data.map((r) => parseWeekFromGameId(r.game_id)).filter((w): w is number => w != null)
    )
  ).sort((a, b) => a - b);

  const teams = Array.from(new Set(data.map((r) => r.team))).sort();

  const needsRefetch = viewMode === "first_td_only" || filterWeek !== "" || !!filterTeam;

  useEffect(() => {
    if (!needsRefetch) {
      setData(initialData);
      return;
    }
    setLoading(true);
    request<TouchdownRow[]>(
      `/api/analytics/all-touchdowns?season=${season}` +
        (filterWeek !== "" ? `&week=${filterWeek}` : "") +
        (filterTeam ? `&team=${encodeURIComponent(filterTeam)}` : "") +
        (viewMode === "first_td_only" ? "&first_td_only=true" : "")
    ).then((res) => {
      setLoading(false);
      if (res.ok) setData(res.data);
    });
  }, [season, filterWeek, filterTeam, viewMode, needsRefetch, initialData]);

  const filtered = data;
  const showFirstTdColumn = viewMode === "all";

  if (initialData.length === 0 && !loading) {
    return (
      <div className="flex flex-col items-center justify-center gap-3 rounded-lg border-2 border-[#d1d5db] bg-[#F1EEE6] py-16 text-center font-mono">
        <div className="text-4xl">🏈</div>
        <div>
          <p className="text-lg font-bold text-[#234058]">No touchdown data</p>
          <p className="mt-1 text-sm text-[#5c5a57]">
            Sync touchdowns from Admin to populate this view
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap gap-3 items-center">
        <select
          value={viewMode}
          onChange={(e) => setViewMode(e.target.value as ViewMode)}
          className="min-h-[44px] w-full sm:w-auto rounded border-2 border-[#d1d5db] bg-white px-3 py-2 text-sm font-mono text-[#234058]"
          aria-label="View mode"
        >
          <option value="all">All touchdowns</option>
          <option value="first_td_only">First TD only</option>
        </select>
        <select
          value={filterWeek}
          onChange={(e) => setFilterWeek(e.target.value === "" ? "" : Number(e.target.value))}
          className="min-h-[44px] w-full sm:w-auto rounded border-2 border-[#d1d5db] bg-white px-3 py-2 text-sm font-mono text-[#234058]"
          aria-label="Filter by week"
        >
          <option value="">All weeks</option>
          {weeks.map((w) => (
            <option key={w} value={w}>
              Week {w}
            </option>
          ))}
        </select>
        <select
          value={filterTeam}
          onChange={(e) => setFilterTeam(e.target.value)}
          className="min-h-[44px] w-full sm:w-auto rounded border-2 border-[#d1d5db] bg-white px-3 py-2 text-sm font-mono text-[#234058]"
          aria-label="Filter by team"
        >
          <option value="">All teams</option>
          {teams.map((t) => (
            <option key={t} value={t}>
              {t}
            </option>
          ))}
        </select>
        {loading && (
          <span className="self-center text-xs font-mono text-[#5c5a57]">Loading…</span>
        )}
      </div>
      <div className="overflow-x-auto rounded-lg border-2 border-[#d1d5db] bg-[#fff] shadow-sm">
        <table
          className="w-full text-left text-sm font-mono"
          aria-label={viewMode === "first_td_only" ? "First touchdown of each game" : "All touchdowns"}
        >
          <thead className="border-b-2 border-[#d1d5db] bg-[#f8fafc]">
            <tr>
              <th className="px-4 py-3 font-bold uppercase tracking-[0.15em] text-[#64748b] text-[10px]">
                Game
              </th>
              <th className="px-4 py-3 font-bold uppercase tracking-[0.15em] text-[#64748b] text-[10px]">
                Week
              </th>
              <th className="px-4 py-3 font-bold uppercase tracking-[0.15em] text-[#64748b] text-[10px]">
                Player
              </th>
              <th className="px-4 py-3 font-bold uppercase tracking-[0.15em] text-[#64748b] text-[10px]">
                Team
              </th>
              {showFirstTdColumn && (
                <th className="px-4 py-3 font-bold uppercase tracking-[0.15em] text-[#64748b] text-[10px]">
                  First TD
                </th>
              )}
            </tr>
          </thead>
          <tbody>
            {filtered.map((row, idx) => (
              <tr
                key={`${row.game_id}-${row.player_name}-${idx}`}
                className="border-b border-dashed border-[#e5e7eb] transition-colors hover:bg-[#fff7ed]"
              >
                <td className="px-4 py-4 font-mono text-[10px] text-[#5c5a57]">
                  {row.game_id}
                </td>
                <td className="px-4 py-4">
                  {parseWeekFromGameId(row.game_id) ?? "—"}
                </td>
                <td className="px-4 py-4 font-bold text-[#234058]">{row.player_name}</td>
                <td className="px-4 py-4 text-[#44403c]">{row.team}</td>
                {showFirstTdColumn && (
                  <td className="px-4 py-4">
                    {row.is_first_td ? (
                      <span className="font-bold text-[#15803d]">Yes</span>
                    ) : (
                      <span className="text-[#5c5a57]">—</span>
                    )}
                  </td>
                )}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
