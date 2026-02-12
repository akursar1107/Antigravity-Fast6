"use client";

import { useState, useEffect } from "react";
import {
  syncGamesAction,
  syncRostersAction,
  syncTouchdownsAction,
  cleanupNonFinalGamesAction,
  clearGamesAndTouchdownsAction,
  getHealthSyncAction,
  recalculateStatsAction,
} from "@/app/admin/actions";

const CURRENT_SEASON = parseInt(process.env.NEXT_PUBLIC_CURRENT_SEASON ?? "2025", 10);

export default function AdminSyncButtons() {
  const [gamesStatus, setGamesStatus] = useState<"idle" | "loading" | "success" | "error">("idle");
  const [rostersStatus, setRostersStatus] = useState<"idle" | "loading" | "success" | "error">("idle");
  const [touchdownsStatus, setTouchdownsStatus] = useState<"idle" | "loading" | "success" | "error">("idle");
  const [cleanupStatus, setCleanupStatus] = useState<"idle" | "loading" | "success" | "error">("idle");
  const [clearStatus, setClearStatus] = useState<"idle" | "loading" | "success" | "error">("idle");
  const [recalcStatus, setRecalcStatus] = useState<"idle" | "loading" | "success" | "error">("idle");
  const [gamesMsg, setGamesMsg] = useState("");
  const [rostersMsg, setRostersMsg] = useState("");
  const [touchdownsMsg, setTouchdownsMsg] = useState("");
  const [cleanupMsg, setCleanupMsg] = useState("");
  const [clearMsg, setClearMsg] = useState("");
  const [recalcMsg, setRecalcMsg] = useState("");
  const [syncMetadata, setSyncMetadata] = useState<{ target: string; season: number | null; last_sync_at: string | null; status: string }[]>([]);

  useEffect(() => {
    getHealthSyncAction().then((res) => {
      if (res.ok && res.data?.sync) setSyncMetadata(res.data.sync);
    });
  }, [gamesStatus, rostersStatus, touchdownsStatus, clearStatus]);

  async function handleSyncGames() {
    setGamesStatus("loading");
    setGamesMsg("");
    const res = await syncGamesAction(CURRENT_SEASON);
    if (res.ok && res.data) {
      setGamesStatus("success");
      const d = res.data as { inserted: number; errors: number; td_games_synced?: number; td_inserted?: number };
      let msg = `Synced ${d.inserted} games`;
      if (d.td_games_synced != null && d.td_inserted != null) {
        msg += `, ${d.td_games_synced} games with ${d.td_inserted} TDs`;
      }
      if (d.errors > 0) msg += ` (${d.errors} errors)`;
      setGamesMsg(msg);
    } else {
      setGamesStatus("error");
      setGamesMsg(res.error ?? "Sync failed");
    }
  }

  async function handleSyncRosters() {
    setRostersStatus("loading");
    setRostersMsg("");
    const res = await syncRostersAction(CURRENT_SEASON);
    if (res.ok && res.data) {
      setRostersStatus("success");
      setRostersMsg(
        `Synced ${res.data.inserted} roster entries${res.data.errors > 0 ? ` (${res.data.errors} errors)` : ""}`
      );
    } else {
      setRostersStatus("error");
      setRostersMsg(res.error ?? "Sync failed");
    }
  }

  async function handleSyncTouchdowns() {
    setTouchdownsStatus("loading");
    setTouchdownsMsg("");
    const res = await syncTouchdownsAction(CURRENT_SEASON);
    if (res.ok && res.data) {
      setTouchdownsStatus("success");
      setTouchdownsMsg(
        `Synced ${res.data.inserted} TDs across ${res.data.games_synced} games${res.data.errors > 0 ? ` (${res.data.errors} errors)` : ""}`
      );
    } else {
      setTouchdownsStatus("error");
      setTouchdownsMsg(res.error ?? "Sync failed");
    }
  }

  async function handleClearGamesAndTouchdowns() {
    setClearStatus("loading");
    setClearMsg("");
    const res = await clearGamesAndTouchdownsAction();
    if (res.ok && res.data) {
      setClearStatus("success");
      setClearMsg(`Cleared ${res.data.games_deleted} games and ${res.data.touchdowns_deleted} touchdowns (picks unchanged)`);
    } else {
      setClearStatus("error");
      setClearMsg(res.error ?? "Clear failed");
    }
  }

  async function handleRecalculateStats() {
    setRecalcStatus("loading");
    setRecalcMsg("");
    const res = await recalculateStatsAction();
    if (res.ok && res.data) {
      setRecalcStatus("success");
      setRecalcMsg(res.data.message ?? `Updated ${res.data.results_updated} results. Refresh the leaderboard to see changes.`);
    } else {
      setRecalcStatus("error");
      setRecalcMsg(res.error ?? "Recalculation failed");
    }
  }

  async function handleCleanupNonFinalGames() {
    setCleanupStatus("loading");
    setCleanupMsg("");
    const res = await cleanupNonFinalGamesAction();
    if (res.ok && res.data) {
      setCleanupStatus("success");
      setCleanupMsg(`Removed ${res.data.deleted} non-final games from database`);
    } else {
      setCleanupStatus("error");
      setCleanupMsg(res.error ?? "Cleanup failed");
    }
  }

  return (
    <div className="rounded-lg border-2 border-[#d1d5db] bg-[#fff] p-5 shadow-sm">
      <p className="text-xs font-bold uppercase tracking-[0.2em] text-[#78716c] font-mono">
        Data sync (nflreadpy)
      </p>
      <p className="mt-2 text-sm text-[#234058] font-mono">
        Pull games and rosters from nflverse/nflreadpy into the database.
      </p>
      <p className="mt-1 text-xs text-[#78716c] font-mono">
        Sync games also syncs touchdowns for final games. Use Sync touchdowns to refresh TD data only.
      </p>
      <p className="mt-1 text-xs text-[#78716c] font-mono">
        Use Remove non-final games to soft-delete scheduled/in-progress games (keeps only final).
      </p>
      <p className="mt-1 text-xs text-[#78716c] font-mono">
        Use Clear games and TDs to delete all games and touchdown data. Picks are kept.
      </p>
      <p className="mt-3 text-xs font-bold uppercase tracking-[0.2em] text-[#78716c] font-mono">
        Leaderboard & stats
      </p>
      <p className="mt-1 text-xs text-[#78716c] font-mono">
        Recalculate PTS, ROI, and REC from graded picks. Use after editing picks or manual grading.
      </p>
      <div className="mt-4 flex flex-wrap gap-3">
        <button
          type="button"
          onClick={handleSyncGames}
          disabled={gamesStatus === "loading"}
          className="rounded border-2 border-[#234058] bg-[#234058] px-4 py-2 text-sm font-bold uppercase tracking-wider text-[#F1EEE6] transition hover:bg-[#1a3348] disabled:opacity-50 disabled:cursor-not-allowed font-mono"
        >
          {gamesStatus === "loading" ? "Syncing…" : "Sync games"}
        </button>
        <button
          type="button"
          onClick={handleSyncRosters}
          disabled={rostersStatus === "loading"}
          className="rounded border-2 border-[#234058] bg-[#234058] px-4 py-2 text-sm font-bold uppercase tracking-wider text-[#F1EEE6] transition hover:bg-[#1a3348] disabled:opacity-50 disabled:cursor-not-allowed font-mono"
        >
          {rostersStatus === "loading" ? "Syncing…" : "Sync rosters"}
        </button>
        <button
          type="button"
          onClick={handleSyncTouchdowns}
          disabled={touchdownsStatus === "loading"}
          className="rounded border-2 border-[#15803d]/60 bg-[#15803d]/10 px-4 py-2 text-sm font-bold uppercase tracking-wider text-[#15803d] transition hover:bg-[#15803d]/20 disabled:opacity-50 disabled:cursor-not-allowed font-mono"
        >
          {touchdownsStatus === "loading" ? "Syncing…" : "Sync touchdowns"}
        </button>
        <button
          type="button"
          onClick={handleCleanupNonFinalGames}
          disabled={cleanupStatus === "loading"}
          className="rounded border-2 border-[#8C302C]/60 bg-[#8C302C]/10 px-4 py-2 text-sm font-bold uppercase tracking-wider text-[#8C302C] transition hover:bg-[#8C302C]/20 disabled:opacity-50 disabled:cursor-not-allowed font-mono"
        >
          {cleanupStatus === "loading" ? "Removing…" : "Remove non-final games"}
        </button>
        <button
          type="button"
          onClick={handleClearGamesAndTouchdowns}
          disabled={clearStatus === "loading"}
          className="rounded border-2 border-[#78716c]/60 bg-[#78716c]/10 px-4 py-2 text-sm font-bold uppercase tracking-wider text-[#78716c] transition hover:bg-[#78716c]/20 disabled:opacity-50 disabled:cursor-not-allowed font-mono"
        >
          {clearStatus === "loading" ? "Clearing…" : "Clear games & TDs"}
        </button>
        <button
          type="button"
          onClick={handleRecalculateStats}
          disabled={recalcStatus === "loading"}
          className="rounded border-2 border-[#15803d]/60 bg-[#15803d]/10 px-4 py-2 text-sm font-bold uppercase tracking-wider text-[#15803d] transition hover:bg-[#15803d]/20 disabled:opacity-50 disabled:cursor-not-allowed font-mono"
        >
          {recalcStatus === "loading" ? "Recalculating…" : "Recalculate stats"}
        </button>
      </div>
      {(gamesMsg || rostersMsg || touchdownsMsg || cleanupMsg || clearMsg || recalcMsg) && (
        <div className="mt-4 space-y-2">
          {gamesMsg && (
            <p
              className={`text-sm font-mono ${
                gamesStatus === "error" ? "text-[#8C302C]" : "text-[#15803d]"
              }`}
            >
              Games: {gamesMsg}
            </p>
          )}
          {rostersMsg && (
            <p
              className={`text-sm font-mono ${
                rostersStatus === "error" ? "text-[#8C302C]" : "text-[#15803d]"
              }`}
            >
              Rosters: {rostersMsg}
            </p>
          )}
          {touchdownsMsg && (
            <p
              className={`text-sm font-mono ${
                touchdownsStatus === "error" ? "text-[#8C302C]" : "text-[#15803d]"
              }`}
            >
              Touchdowns: {touchdownsMsg}
            </p>
          )}
          {cleanupMsg && (
            <p
              className={`text-sm font-mono ${
                cleanupStatus === "error" ? "text-[#8C302C]" : "text-[#15803d]"
              }`}
            >
              Cleanup: {cleanupMsg}
            </p>
          )}
          {clearMsg && (
            <p
              className={`text-sm font-mono ${
                clearStatus === "error" ? "text-[#8C302C]" : "text-[#15803d]"
              }`}
            >
              Clear: {clearMsg}
            </p>
          )}
          {recalcMsg && (
            <p
              className={`text-sm font-mono ${
                recalcStatus === "error" ? "text-[#8C302C]" : "text-[#15803d]"
              }`}
            >
              Stats: {recalcMsg}
            </p>
          )}
        </div>
      )}
      {syncMetadata.length > 0 && (
        <div className="mt-4 rounded border border-[#d1d5db] bg-[#f8fafc] p-3">
          <p className="text-[10px] font-bold uppercase tracking-widest text-[#78716c] font-mono">
            Last sync
          </p>
          <ul className="mt-2 space-y-1 text-xs font-mono text-[#234058]">
            {syncMetadata.map((s) => (
              <li key={s.target}>
                {s.target}: {s.last_sync_at ? new Date(s.last_sync_at).toLocaleString() : "—"} (season {s.season ?? "—"})
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
