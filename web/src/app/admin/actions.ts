"use server";

import { getServerToken } from "@/lib/server-token";

const BACKEND_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";
const SYNC_TIMEOUT_MS = 120_000;

export type SyncResult = {
  success: boolean;
  season: number;
  inserted: number;
  errors: number;
};

export type SyncTouchdownsResult = {
  success: boolean;
  season: number;
  games_synced: number;
  inserted: number;
  errors: number;
};

async function fetchSync(path: string, token: string): Promise<Response> {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), SYNC_TIMEOUT_MS);
  try {
    return await fetch(path, {
      method: "POST",
      headers: { Authorization: `Bearer ${token}` },
      signal: controller.signal,
    });
  } finally {
    clearTimeout(timeoutId);
  }
}

export async function syncGamesAction(season: number): Promise<{ ok: boolean; data?: SyncResult; error?: string }> {
  const token = await getServerToken();
  if (!token) return { ok: false, error: "Not authenticated" };
  try {
    const path = `${BACKEND_URL}/api/v1/admin/sync-games?season=${season}`;
    const res = await fetchSync(path, token);
    const data = (await res.json().catch(() => ({}))) as SyncResult & { detail?: string | string[] };
    if (!res.ok) {
      const d = data.detail;
      const errMsg = Array.isArray(d) ? d.join("; ") : d ?? (data as { error?: string }).error ?? `HTTP ${res.status}`;
      return { ok: false, error: errMsg };
    }
    return { ok: true, data };
  } catch (err) {
    const msg = err instanceof Error && err.name === "AbortError"
      ? "Sync timed out. Try again."
      : err instanceof Error ? err.message : "Failed to reach backend.";
    return { ok: false, error: msg };
  }
}

export async function syncRostersAction(season: number): Promise<{ ok: boolean; data?: SyncResult; error?: string }> {
  const token = await getServerToken();
  if (!token) return { ok: false, error: "Not authenticated" };
  try {
    const path = `${BACKEND_URL}/api/v1/admin/sync-rosters?season=${season}`;
    const res = await fetchSync(path, token);
    const data = (await res.json().catch(() => ({}))) as SyncResult & { detail?: string | string[] };
    if (!res.ok) {
      const d = data.detail;
      const errMsg = Array.isArray(d) ? d.join("; ") : d ?? (data as { error?: string }).error ?? `HTTP ${res.status}`;
      return { ok: false, error: errMsg };
    }
    return { ok: true, data };
  } catch (err) {
    const msg = err instanceof Error && err.name === "AbortError"
      ? "Sync timed out. Try again."
      : err instanceof Error ? err.message : "Failed to reach backend.";
    return { ok: false, error: msg };
  }
}

export async function syncTouchdownsAction(season: number): Promise<{
  ok: boolean;
  data?: SyncTouchdownsResult;
  error?: string;
}> {
  const token = await getServerToken();
  if (!token) return { ok: false, error: "Not authenticated" };
  try {
    const path = `${BACKEND_URL}/api/v1/admin/sync-touchdowns?season=${season}`;
    const res = await fetchSync(path, token);
    const data = (await res.json().catch(() => ({}))) as SyncTouchdownsResult & { detail?: string | string[] };
    if (!res.ok) {
      const d = data.detail;
      const errMsg = Array.isArray(d) ? d.join("; ") : d ?? (data as { error?: string }).error ?? `HTTP ${res.status}`;
      return { ok: false, error: errMsg };
    }
    return { ok: true, data };
  } catch (err) {
    const msg = err instanceof Error && err.name === "AbortError"
      ? "Sync timed out. Try again."
      : err instanceof Error ? err.message : "Failed to reach backend.";
    return { ok: false, error: msg };
  }
}

export type SyncMetadata = {
  target: string;
  season: number | null;
  last_sync_at: string | null;
  status: string;
};

export async function getHealthSyncAction(): Promise<{
  ok: boolean;
  data?: { sync?: SyncMetadata[] };
  error?: string;
}> {
  const token = await getServerToken();
  if (!token) return { ok: false, error: "Not authenticated" };
  try {
    const path = `${BACKEND_URL}/health`;
    const res = await fetch(path, {
      headers: { Authorization: `Bearer ${token}` },
    });
    const data = (await res.json().catch(() => ({}))) as { sync?: SyncMetadata[] };
    return { ok: true, data };
  } catch {
    return { ok: false, error: "Could not fetch health" };
  }
}

export async function clearGamesAndTouchdownsAction(): Promise<{
  ok: boolean;
  data?: { success: boolean; games_deleted: number; touchdowns_deleted: number };
  error?: string;
}> {
  const token = await getServerToken();
  if (!token) return { ok: false, error: "Not authenticated" };
  try {
    const path = `${BACKEND_URL}/api/v1/admin/clear-games-and-touchdowns`;
    const res = await fetch(path, {
      method: "POST",
      headers: { Authorization: `Bearer ${token}` },
    });
    const data = (await res.json().catch(() => ({}))) as { success?: boolean; games_deleted?: number; touchdowns_deleted?: number; detail?: string };
    if (!res.ok) {
      const errMsg = data.detail ?? (data as { error?: string }).error ?? `HTTP ${res.status}`;
      return { ok: false, error: String(errMsg) };
    }
    return { ok: true, data: { success: data.success ?? true, games_deleted: data.games_deleted ?? 0, touchdowns_deleted: data.touchdowns_deleted ?? 0 } };
  } catch (err) {
    return { ok: false, error: err instanceof Error ? err.message : "Failed to reach backend." };
  }
}

export async function gradePendingPicksAction(season: number): Promise<{
  ok: boolean;
  data?: { success: boolean; season: number; graded_picks: number; correct_first_td?: number; any_time_td?: number; error?: string };
  error?: string;
}> {
  const token = await getServerToken();
  if (!token) return { ok: false, error: "Not authenticated" };
  try {
    const path = `${BACKEND_URL}/api/v1/admin/grade-pending?season=${season}`;
    const res = await fetch(path, {
      method: "POST",
      headers: { Authorization: `Bearer ${token}` },
    });
    const data = (await res.json().catch(() => ({}))) as { success?: boolean; season?: number; graded_picks?: number; correct_first_td?: number; any_time_td?: number; error?: string; detail?: string };
    if (!res.ok) {
      const errMsg = data.error ?? data.detail ?? (data as { error?: string }).error ?? `HTTP ${res.status}`;
      const hint = res.status === 404
        ? " Ensure the backend is running and has been restarted since adding the grade-pending endpoint."
        : "";
      return { ok: false, error: String(errMsg) + hint };
    }
    return {
      ok: true,
      data: {
        success: data.success ?? true,
        season: data.season ?? season,
        graded_picks: data.graded_picks ?? 0,
        correct_first_td: data.correct_first_td,
        any_time_td: data.any_time_td,
      },
    };
  } catch (err) {
    return { ok: false, error: err instanceof Error ? err.message : "Failed to reach backend." };
  }
}

export async function regradeSeasonAction(season: number): Promise<{
  ok: boolean;
  data?: { success: boolean; season: number; results_cleared: number; graded_picks: number; correct_first_td?: number; any_time_td?: number; error?: string };
  error?: string;
}> {
  const token = await getServerToken();
  if (!token) return { ok: false, error: "Not authenticated" };
  try {
    const path = `${BACKEND_URL}/api/v1/admin/regrade-season?season=${season}`;
    const res = await fetch(path, {
      method: "POST",
      headers: { Authorization: `Bearer ${token}` },
    });
    const data = (await res.json().catch(() => ({}))) as { success?: boolean; season?: number; results_cleared?: number; graded_picks?: number; correct_first_td?: number; any_time_td?: number; error?: string; detail?: string };
    if (!res.ok) {
      const errMsg = data.error ?? data.detail ?? (data as { error?: string }).error ?? `HTTP ${res.status}`;
      return { ok: false, error: String(errMsg) };
    }
    return {
      ok: true,
      data: {
        success: data.success ?? true,
        season: data.season ?? season,
        results_cleared: data.results_cleared ?? 0,
        graded_picks: data.graded_picks ?? 0,
        correct_first_td: data.correct_first_td,
        any_time_td: data.any_time_td,
      },
    };
  } catch (err) {
    return { ok: false, error: err instanceof Error ? err.message : "Failed to reach backend." };
  }
}

export async function recalculateStatsAction(): Promise<{
  ok: boolean;
  data?: { success: boolean; results_updated: number; message?: string };
  error?: string;
}> {
  const token = await getServerToken();
  if (!token) return { ok: false, error: "Not authenticated" };
  try {
    const path = `${BACKEND_URL}/api/v1/admin/recalculate-stats`;
    const res = await fetch(path, {
      method: "POST",
      headers: { Authorization: `Bearer ${token}` },
    });
    const data = (await res.json().catch(() => ({}))) as { success?: boolean; results_updated?: number; message?: string; detail?: string };
    if (!res.ok) {
      const errMsg = data.detail ?? (data as { error?: string }).error ?? `HTTP ${res.status}`;
      return { ok: false, error: String(errMsg) };
    }
    return { ok: true, data: { success: data.success ?? true, results_updated: data.results_updated ?? 0, message: data.message } };
  } catch (err) {
    return { ok: false, error: err instanceof Error ? err.message : "Failed to reach backend." };
  }
}

export async function cleanupNonFinalGamesAction(): Promise<{
  ok: boolean;
  data?: { success: boolean; deleted: number };
  error?: string;
}> {
  const token = await getServerToken();
  if (!token) return { ok: false, error: "Not authenticated" };
  try {
    const path = `${BACKEND_URL}/api/v1/admin/cleanup-non-final-games`;
    const res = await fetch(path, {
      method: "POST",
      headers: { Authorization: `Bearer ${token}` },
    });
    const data = (await res.json().catch(() => ({}))) as { success?: boolean; deleted?: number; detail?: string };
    if (!res.ok) {
      const errMsg = data.detail ?? (data as { error?: string }).error ?? `HTTP ${res.status}`;
      return { ok: false, error: String(errMsg) };
    }
    return { ok: true, data: { success: data.success ?? true, deleted: data.deleted ?? 0 } };
  } catch (err) {
    return { ok: false, error: err instanceof Error ? err.message : "Failed to reach backend." };
  }
}