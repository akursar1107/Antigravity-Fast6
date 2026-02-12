"use client";

import { useMemo, useState } from "react";
import type { Pick, User } from "@/lib/api";

type SortColumn = "user" | "week" | "team" | null;

type AdminPicksTableProps = {
  picks: Pick[];
  users: User[];
};

export default function AdminPicksTable({ picks, users }: AdminPicksTableProps) {
  const [sortColumn, setSortColumn] = useState<SortColumn>(null);
  const [sortAsc, setSortAsc] = useState(true);
  const [weekFilter, setWeekFilter] = useState<string>("all");
  const [userFilter, setUserFilter] = useState<string>("all");

  const userMap = useMemo(() => new Map(users.map((u) => [u.id, u.name])), [users]);

  const uniqueWeeks = useMemo(() => {
    const ids = [...new Set(picks.map((p) => p.week_id))].sort((a, b) => a - b);
    return ids;
  }, [picks]);

  const filteredAndSorted = useMemo(() => {
    let list = [...picks];

    if (weekFilter !== "all") {
      const weekId = parseInt(weekFilter, 10);
      list = list.filter((p) => p.week_id === weekId);
    }

    if (userFilter !== "all") {
      const userId = parseInt(userFilter, 10);
      list = list.filter((p) => p.user_id === userId);
    }

    if (sortColumn) {
      list.sort((a, b) => {
        let cmp = 0;
        if (sortColumn === "user") {
          const nameA = userMap.get(a.user_id) ?? "";
          const nameB = userMap.get(b.user_id) ?? "";
          cmp = nameA.localeCompare(nameB);
        } else if (sortColumn === "week") {
          cmp = a.week_id - b.week_id;
        } else if (sortColumn === "team") {
          cmp = (a.team ?? "").localeCompare(b.team ?? "");
        }
        return sortAsc ? cmp : -cmp;
      });
    }

    return list;
  }, [picks, weekFilter, userFilter, sortColumn, sortAsc, userMap]);

  const handleSort = (col: SortColumn) => {
    if (sortColumn === col) {
      setSortAsc((prev) => !prev);
    } else {
      setSortColumn(col);
      setSortAsc(true);
    }
  };

  const SortHeader = ({
    label,
    column,
  }: {
    label: string;
    column: SortColumn;
  }) => (
    <th
      className="cursor-pointer select-none px-4 py-3 font-bold uppercase tracking-[0.15em] text-[#64748b] text-[10px] hover:text-[#234058] transition-colors"
      onClick={() => handleSort(column)}
    >
      <span className="inline-flex items-center gap-1">
        {label}
        {sortColumn === column && (
          <span className="text-[#234058]">{sortAsc ? "↑" : "↓"}</span>
        )}
      </span>
    </th>
  );

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center gap-3">
        <label className="flex items-center gap-2 text-sm font-mono text-[#44403c]">
          Week:
          <select
            value={weekFilter}
            onChange={(e) => setWeekFilter(e.target.value)}
            className="rounded border border-[#d1d5db] bg-white px-3 py-1.5 text-sm font-mono text-[#234058] focus:border-[#234058] focus:outline-none focus:ring-1 focus:ring-[#234058]"
          >
            <option value="all">All weeks</option>
            {uniqueWeeks.map((w) => (
              <option key={w} value={w}>
                Week {w}
              </option>
            ))}
          </select>
        </label>
        <label className="flex items-center gap-2 text-sm font-mono text-[#44403c]">
          User:
          <select
            value={userFilter}
            onChange={(e) => setUserFilter(e.target.value)}
            className="rounded border border-[#d1d5db] bg-white px-3 py-1.5 text-sm font-mono text-[#234058] focus:border-[#234058] focus:outline-none focus:ring-1 focus:ring-[#234058]"
          >
            <option value="all">All users</option>
            {users.map((u) => (
              <option key={u.id} value={u.id}>
                {u.name}
              </option>
            ))}
          </select>
        </label>
        <span className="text-xs font-mono text-[#78716c]">
          {filteredAndSorted.length} of {picks.length} picks
        </span>
      </div>

      <div className="overflow-x-auto rounded-lg border-2 border-[#d1d5db] bg-[#fff] shadow-sm">
        <table className="w-full text-left text-sm font-mono" aria-label="All picks">
          <thead className="bg-[#f8fafc] border-b-2 border-[#d1d5db]">
            <tr>
              <th className="px-4 py-3 font-bold uppercase tracking-[0.15em] text-[#64748b] text-[10px]">
                ID
              </th>
              <SortHeader label="User" column="user" />
              <SortHeader label="Week" column="week" />
              <SortHeader label="Team" column="team" />
              <th className="px-4 py-3 font-bold uppercase tracking-[0.15em] text-[#64748b] text-[10px]">
                Player
              </th>
              <th className="px-4 py-3 text-right font-bold uppercase tracking-[0.15em] text-[#64748b] text-[10px]">
                Odds
              </th>
            </tr>
          </thead>
          <tbody>
            {filteredAndSorted.map((pick) => (
              <tr
                key={pick.id}
                className="border-b border-dashed border-[#e5e7eb] hover:bg-[#fff7ed] transition-colors"
              >
                <td className="px-4 py-3 text-[#78716c]">{pick.id}</td>
                <td className="px-4 py-3 font-bold text-[#234058]">
                  {userMap.get(pick.user_id) ?? `User #${pick.user_id}`}
                </td>
                <td className="px-4 py-3 text-[#44403c]">Week {pick.week_id}</td>
                <td className="px-4 py-3 text-[#44403c]">{pick.team}</td>
                <td className="px-4 py-3 font-medium text-[#234058]">
                  {pick.player_name}
                </td>
                <td className="px-4 py-3 text-right text-[#44403c]">
                  {pick.odds != null ? `+${pick.odds}` : "—"}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
