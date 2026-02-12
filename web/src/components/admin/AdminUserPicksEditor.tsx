"use client";

import { useState, useMemo } from "react";
import Link from "next/link";
import type { PickWithResult, PickUpdate } from "@/lib/api";
import { updatePickServer, deletePickServer, updateResultServer } from "@/lib/api";

type SortColumn = "week" | "team" | "player" | "result" | null;

type AdminUserPicksEditorProps = {
  picks: PickWithResult[];
  userName: string;
  token: string;
};

export default function AdminUserPicksEditor({
  picks: initialPicks,
  userName,
  token,
}: AdminUserPicksEditorProps) {
  const [picks, setPicks] = useState<PickWithResult[]>(initialPicks);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [editValues, setEditValues] = useState<PickUpdate>({});
  const [status, setStatus] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [sortColumn, setSortColumn] = useState<SortColumn>("week");
  const [sortAsc, setSortAsc] = useState(true);

  const sortedPicks = useMemo(() => {
    const list = [...picks];
    if (sortColumn) {
      list.sort((a, b) => {
        let cmp = 0;
        if (sortColumn === "week") cmp = a.week_id - b.week_id;
        else if (sortColumn === "team") cmp = (a.team ?? "").localeCompare(b.team ?? "");
        else if (sortColumn === "player") cmp = (a.player_name ?? "").localeCompare(b.player_name ?? "");
        else if (sortColumn === "result") {
          const aVal = a.is_correct === true ? 2 : a.is_correct === false ? 1 : 0;
          const bVal = b.is_correct === true ? 2 : b.is_correct === false ? 1 : 0;
          cmp = aVal - bVal;
        }
        return sortAsc ? cmp : -cmp;
      });
    }
    return list;
  }, [picks, sortColumn, sortAsc]);

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

  const startEdit = (pick: PickWithResult) => {
    setEditingId(pick.id);
    setEditValues({
      team: pick.team,
      player_name: pick.player_name,
      odds: pick.odds ?? undefined,
    });
    setError(null);
    setStatus(null);
  };

  const cancelEdit = () => {
    setEditingId(null);
    setEditValues({});
  };

  const saveEdit = async () => {
    if (editingId == null) return;
    setError(null);
    setStatus(null);

    const res = await updatePickServer(editingId, editValues, token);
    if (res.ok) {
      setPicks((prev) =>
        prev.map((p) =>
          p.id === editingId
            ? { ...res.data, result_id: p.result_id, is_correct: p.is_correct, any_time_td: p.any_time_td }
            : p
        )
      );
      setEditingId(null);
      setEditValues({});
      setStatus("Pick updated");
    } else {
      setError(res.error.message);
    }
  };

  const handleChangeResult = async (pickId: number, newIsCorrect: boolean) => {
    setError(null);
    setStatus(null);
    const res = await updateResultServer(pickId, newIsCorrect, token);
    if (res.ok) {
      setPicks((prev) =>
        prev.map((p) =>
          p.id === pickId ? { ...p, is_correct: newIsCorrect } : p
        )
      );
      setStatus(`Result updated to ${newIsCorrect ? "Win" : "Loss"}`);
    } else {
      setError(res.error.message);
    }
  };

  const handleDelete = async (pickId: number, playerName: string) => {
    if (!confirm(`Delete pick for ${playerName}?`)) return;
    setError(null);
    setStatus(null);

    const res = await deletePickServer(pickId, token);
    if (res.ok) {
      setPicks((prev) => prev.filter((p) => p.id !== pickId));
      setStatus(`Deleted pick for ${playerName}`);
    } else {
      setError(res.error.message);
    }
  };

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <Link
          href="/admin/users"
          className="text-sm font-bold uppercase tracking-wider text-[#78716c] hover:text-[#234058] font-mono transition inline-flex items-center gap-2"
        >
          ← Manage Users
        </Link>
      </div>

      <div className="rounded-lg border-2 border-[#d1d5db] bg-[#fff] p-6 shadow-sm">
        <h2 className="text-lg font-black uppercase tracking-[0.15em] text-[#234058] font-mono">
          {userName} · {picks.length} {picks.length === 1 ? "Pick" : "Picks"}
        </h2>
        <p className="mt-2 text-sm text-[#78716c] font-mono">
          Update team, player, or odds. Change result for graded picks.
        </p>
      </div>

      {status && (
        <div className="rounded-lg border-2 border-[#15803d] bg-[#15803d]/10 px-4 py-3 text-sm font-mono text-[#15803d] font-bold">
          {status}
        </div>
      )}
      {error && (
        <div className="rounded-lg border-2 border-[#8C302C] bg-[#8C302C]/10 px-4 py-3 text-sm font-mono text-[#8C302C] font-bold">
          {error}
        </div>
      )}

      {picks.length === 0 ? (
        <div className="rounded-lg border-2 border-[#d1d5db] bg-[#fff] py-12 text-center shadow-sm">
          <p className="text-[#78716c] font-mono">No picks yet</p>
          <p className="mt-2 text-sm text-[#78716c] font-mono">
            Picks will appear here once the user submits them.
          </p>
        </div>
      ) : (
        <div className="overflow-x-auto rounded-lg border-2 border-[#d1d5db] bg-[#fff] shadow-sm">
          <table className="w-full text-left text-sm font-mono" aria-label="User picks">
            <thead className="bg-[#f8fafc] border-b-2 border-[#d1d5db]">
              <tr>
                <th className="px-4 py-3 font-bold uppercase tracking-[0.15em] text-[#64748b] text-[10px]">
                  ID
                </th>
                <SortHeader label="Week" column="week" />
                <SortHeader label="Team" column="team" />
                <SortHeader label="Player" column="player" />
                <th className="px-4 py-3 font-bold uppercase tracking-[0.15em] text-[#64748b] text-[10px]">
                  Odds
                </th>
                <SortHeader label="Result" column="result" />
                <th className="px-4 py-3 text-right font-bold uppercase tracking-[0.15em] text-[#64748b] text-[10px]">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody>
              {sortedPicks.map((pick) => (
                <tr
                  key={pick.id}
                  className="border-b border-dashed border-[#e5e7eb] hover:bg-[#fff7ed] transition-colors"
                >
                  <td className="px-4 py-3 text-[#78716c]">{pick.id}</td>
                  <td className="px-4 py-3 text-[#44403c]">Week {pick.week_id}</td>
                  {editingId === pick.id ? (
                    <>
                      <td className="px-4 py-3">
                        <input
                          type="text"
                          value={editValues.team ?? ""}
                          onChange={(e) =>
                            setEditValues((prev) => ({
                              ...prev,
                              team: e.target.value,
                            }))
                          }
                          className="w-24 rounded border border-[#d1d5db] bg-[#F1EEE6] px-2 py-1 text-xs font-mono text-[#234058] focus:border-[#234058] focus:outline-none"
                        />
                      </td>
                      <td className="px-4 py-3">
                        <input
                          type="text"
                          value={editValues.player_name ?? ""}
                          onChange={(e) =>
                            setEditValues((prev) => ({
                              ...prev,
                              player_name: e.target.value,
                            }))
                          }
                          className="min-w-[120px] rounded border border-[#d1d5db] bg-[#F1EEE6] px-2 py-1 text-xs font-mono text-[#234058] focus:border-[#234058] focus:outline-none"
                        />
                      </td>
                      <td className="px-4 py-3">
                        <input
                          type="number"
                          value={editValues.odds ?? ""}
                          onChange={(e) => {
                            const v = e.target.value;
                            setEditValues((prev) => ({
                              ...prev,
                              odds: v === "" ? undefined : parseFloat(v) || 0,
                            }));
                          }}
                          placeholder="—"
                          className="w-16 rounded border border-[#d1d5db] bg-[#F1EEE6] px-2 py-1 text-xs font-mono text-[#234058] focus:border-[#234058] focus:outline-none"
                        />
                      </td>
                      <td className="px-4 py-3">
                        {pick.is_correct != null ? (
                          <span className="text-[#78716c]">
                            {pick.is_correct ? "Win" : "Loss"}
                          </span>
                        ) : (
                          <span className="text-[#78716c]">—</span>
                        )}
                      </td>
                      <td className="px-4 py-3 text-right">
                        <button
                          type="button"
                          onClick={saveEdit}
                          className="mr-2 rounded border-2 border-[#15803d]/40 px-2 py-1 text-[10px] font-bold text-[#15803d] uppercase tracking-wider hover:bg-[#15803d]/10"
                        >
                          Save
                        </button>
                        <button
                          type="button"
                          onClick={cancelEdit}
                          className="rounded border-2 border-[#78716c]/40 px-2 py-1 text-[10px] font-bold text-[#78716c] uppercase tracking-wider hover:bg-[#78716c]/10"
                        >
                          Cancel
                        </button>
                      </td>
                    </>
                  ) : (
                    <>
                      <td className="px-4 py-3 text-[#44403c]">{pick.team}</td>
                      <td className="px-4 py-3 font-medium text-[#234058]">
                        {pick.player_name}
                      </td>
                      <td className="px-4 py-3 text-[#44403c]">
                        {pick.odds != null ? `+${pick.odds}` : "—"}
                      </td>
                      <td className="px-4 py-3">
                        {pick.is_correct === true ? (
                          <span className="inline-flex items-center gap-1">
                            <span className="font-bold text-[#15803d]">Win</span>
                            <button
                              type="button"
                              onClick={() => handleChangeResult(pick.id, false)}
                              className="rounded border border-[#78716c]/40 px-2 py-0.5 text-[9px] font-bold text-[#78716c] uppercase hover:bg-[#78716c]/10"
                            >
                              → Loss
                            </button>
                          </span>
                        ) : pick.is_correct === false ? (
                          <span className="inline-flex items-center gap-1">
                            <span className="font-bold text-[#8C302C]">Loss</span>
                            <button
                              type="button"
                              onClick={() => handleChangeResult(pick.id, true)}
                              className="rounded border border-[#78716c]/40 px-2 py-0.5 text-[9px] font-bold text-[#78716c] uppercase hover:bg-[#78716c]/10"
                            >
                              → Win
                            </button>
                          </span>
                        ) : (
                          <span className="text-[#78716c]">—</span>
                        )}
                      </td>
                      <td className="px-4 py-3 text-right">
                        <button
                          type="button"
                          onClick={() => startEdit(pick)}
                          className="mr-2 rounded border-2 border-[#234058]/40 px-2 py-1 text-[10px] font-bold text-[#234058] uppercase tracking-wider hover:bg-[#234058]/10"
                        >
                          Edit
                        </button>
                        <button
                          type="button"
                          onClick={() =>
                            handleDelete(pick.id, pick.player_name)
                          }
                          className="rounded border-2 border-[#8C302C]/40 px-2 py-1 text-[10px] font-bold text-[#8C302C] uppercase tracking-wider hover:bg-[#8C302C]/10"
                        >
                          Delete
                        </button>
                      </td>
                    </>
                  )}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
