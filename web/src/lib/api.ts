import { getCache, setCache } from "./cache";

const TIMEOUT_MS = 8_000;
const CACHE_TTL_MS = 60_000;
const AUTH_STORAGE_KEY = "fast6_auth_token";

function getBaseUrl(): string {
  return process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";
}

function getStoredToken(): string | null {
  try {
    if (typeof window === "undefined") return null;
    return localStorage.getItem(AUTH_STORAGE_KEY);
  } catch {
    return null;
  }
}

export function setStoredToken(token: string): void {
  try {
    if (typeof window === "undefined") return;
    localStorage.setItem(AUTH_STORAGE_KEY, token);
  } catch {
    // Silently fail if localStorage is unavailable
  }
}

export type ApiError = { ok: false; error: { message: string; status?: number } };

function normalizeError(status?: number, detail?: string): ApiError {
  const message =
    detail && typeof detail === "string" && detail.length > 0
      ? detail
      : status === 401
        ? "Session expired. Please sign in again."
        : status === 403
          ? "Access denied."
          : "Request failed. Ensure the backend is running and reachable.";
  return {
    ok: false,
    error: { message, status },
  };
}
export type ApiSuccess<T> = { ok: true; data: T };
export type ApiResponse<T> = ApiSuccess<T> | ApiError;

function buildUrl(path: string): string {
  if (path.startsWith("http://") || path.startsWith("https://")) {
    return path;
  }
  const fullPath = path.startsWith("/api/v1/") ? path : path.replace("/api/", "/api/v1/");
  return `${getBaseUrl()}${fullPath}`;
}

async function fetchWithTimeout(
  url: string,
  options?: RequestInit,
  timeoutMs: number = TIMEOUT_MS
): Promise<Response> {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

  try {
    return await fetch(url, { ...options, signal: controller.signal });
  } finally {
    clearTimeout(timeoutId);
  }
}

export async function request<T>(path: string, serverToken?: string): Promise<ApiResponse<T>> {
  const url = buildUrl(path);
  const cached = getCache<ApiSuccess<T>>(url);
  if (cached) {
    return cached;
  }

  const token = serverToken ?? getStoredToken();
  const headers: HeadersInit = {};

  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  let response: Response | null = null;

  for (let attempt = 0; attempt < 2; attempt += 1) {
    try {
      response = await fetchWithTimeout(url, { headers });
    } catch {
      return normalizeError();
    }

    if (response.ok) {
      try {
        const data = (await response.json()) as T;
        const success: ApiSuccess<T> = { ok: true, data };
        setCache(url, success, CACHE_TTL_MS);
        return success;
      } catch {
        return normalizeError(response.status);
      }
    }

    if (response.status >= 500 && response.status < 600 && attempt === 0) {
      continue;
    }

    let detail: string | undefined;
    try {
      const errBody = (await response.json()) as { detail?: string; error?: string; message?: string };
      const d = errBody?.detail ?? errBody?.error ?? errBody?.message;
      detail = typeof d === "string" ? d : undefined;
    } catch {
      detail = undefined;
    }
    return normalizeError(response.status, detail);
  }

  return normalizeError(response?.status);
}

export type LeaderboardEntry = {
  rank: number;
  user_id: number;
  user_name: string;
  weeks_participated: number;
  total_picks: number;
  correct_picks: number;
  total_points: number;
  roi_dollars: number;
  win_percentage: number;
};

export type WeekLeaderboardEntry = {
  rank: number;
  user_id: number;
  user_name: string;
  picks_count: number;
  correct_count: number;
  total_points: number;
  roi_dollars: number;
};

export type SeasonStats = {
  season: number;
  total_players: number;
  total_weeks: number;
  total_picks: number;
  total_correct: number;
  overall_accuracy: number;
};

export type RoiTrend = {
  week: number;
  picks_count: number;
  correct_count: number;
  accuracy: number;
  roi_dollars: number;
};

export type OddsAccuracy = {
  odds_range: string;
  picks_count: number;
  correct_count: number;
  accuracy: number;
  avg_odds: number;
};

export type PlayerStat = {
  player_name: string;
  team: string;
  first_td_count: number;
  any_time_td_rate: number;
  accuracy: number;
};

export type DefenseStat = {
  team: string;
  total_picks: number;
  correct_picks: number;
  accuracy: number;
};

export type GradingStatus = {
  season: number;
  total_picks: number;
  graded_picks: number;
  ungraded_picks: number;
  grading_progress: number;
};

export type MatchupTeamStat = {
  team: string;
  picks_count: number;
  correct_count: number;
  accuracy: number;
};

export type TdScorer = {
  player_name: string;
  team: string;
  is_first_td?: boolean;
};

export type MatchupPick = {
  id: number;
  user_name: string;
  team: string;
  player_name: string;
  odds: number;
  is_correct: boolean | null;
  actual_scorer: string | null;
  any_time_td: boolean | null;
};

export type MatchupResponse = {
  game_id: string;
  status?: string | null;
  teams: MatchupTeamStat[];
  td_scorers?: TdScorer[];
  picks?: MatchupPick[];
};

export type WeekPick = {
  id: number;
  user_id: number;
  user_name: string;
  team: string;
  player_name: string;
  odds: number;
  graded: boolean;
  is_correct: boolean | null;
  actual_scorer: string | null;
};

export type WeekPicksResponse = {
  week_id: number;
  picks: WeekPick[];
};

export async function getLeaderboard(
  season: number
): Promise<ApiResponse<LeaderboardEntry[]>> {
  return request(`/api/leaderboard/season/${season}`);
}

export async function getWeekLeaderboard(
  weekId: number
): Promise<ApiResponse<WeekLeaderboardEntry[]>> {
  return request(`/api/leaderboard/week/${weekId}`);
}

export async function getRoiTrends(
  season: number
): Promise<ApiResponse<RoiTrend[]>> {
  return request(`/api/analytics/roi-trends?season=${season}`);
}

export type Game = {
  id: string;
  season: number;
  week: number;
  game_date: string;
  home_team: string;
  away_team: string;
  home_score: number | null;
  away_score: number | null;
  status: 'scheduled' | 'in_progress' | 'final';
};

// Server-side helper
export async function getGamesServer(
  season: number,
  token: string,
  week?: number,
  status?: "scheduled" | "in_progress" | "final"
): Promise<ApiResponse<Game[]>> {
  let path = `/api/games?season=${season}`;
  if (week) path += `&week=${week}`;
  if (status) path += `&status=${status}`;
  return request(path, token);
}

export async function getGamesWeeksServer(
  season: number,
  token: string
): Promise<ApiResponse<number[]>> {
  return request(`/api/games/weeks?season=${season}`, token);
}

// Authentication

export type LoginRequest = { username: string };
export type TokenResponse = { access_token: string; token_type: string };

export async function login(username: string): Promise<ApiResponse<TokenResponse>> {
  const url = buildUrl("/api/auth/login");
  const response = await fetchWithTimeout(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username }),
  });

  if (response.ok) {
    try {
      const data = (await response.json()) as TokenResponse;
      setStoredToken(data.access_token);
      return { ok: true, data };
    } catch {
      return normalizeError(response.status);
    }
  }

  return normalizeError(response.status);
}

export function logout(): void {
  try {
    if (typeof window === "undefined") return;
    localStorage.removeItem(AUTH_STORAGE_KEY);
  } catch {
    // Silently fail
  }
}

export function isAuthenticated(): boolean {
  return getStoredToken() !== null;
}

export function getToken(): string | null {
  return getStoredToken();
}

// Server-side API helpers that accept a token
export async function getLeaderboardServer(
  season: number,
  token: string
): Promise<ApiResponse<LeaderboardEntry[]>> {
  return request(`/api/leaderboard/season/${season}`, token);
}

export async function getWeekLeaderboardServer(
  weekId: number,
  token: string
): Promise<ApiResponse<WeekLeaderboardEntry[]>> {
  return request(`/api/leaderboard/week/${weekId}`, token);
}

export async function getSeasonStatsServer(
  season: number,
  token: string
): Promise<ApiResponse<SeasonStats>> {
  return request(`/api/leaderboard/season/${season}/stats`, token);
}

export async function getRoiTrendsServer(
  season: number,
  token: string
): Promise<ApiResponse<RoiTrend[]>> {
  return request(`/api/analytics/roi-trends?season=${season}`, token);
}

export type RoiTrendByUser = {
  week: number;
  user_name: string;
  roi_dollars: number;
};

export async function getRoiTrendsByUserServer(
  season: number,
  token: string
): Promise<ApiResponse<RoiTrendByUser[]>> {
  return request(`/api/analytics/roi-trends-by-user?season=${season}`, token);
}

export async function getPlayerStatsServer(
  season: number,
  token: string,
  limit = 50
): Promise<ApiResponse<PlayerStat[]>> {
  return request(
    `/api/analytics/player-stats?season=${season}&limit=${limit}`,
    token
  );
}

export async function getOddsAccuracyServer(
  season: number,
  token: string
): Promise<ApiResponse<OddsAccuracy[]>> {
  return request(`/api/analytics/odds-accuracy?season=${season}`, token);
}

export async function getTeamDefenseServer(
  season: number,
  token: string
): Promise<ApiResponse<DefenseStat[]>> {
  return request(`/api/analytics/team-defense?season=${season}`, token);
}

export type TouchdownRow = {
  game_id: string;
  player_name: string;
  team: string;
  is_first_td: boolean;
  play_id: number | null;
  season: number;
};

export async function getAllTouchdownsServer(
  season: number,
  token: string,
  opts?: { week?: number; team?: string; first_td_only?: boolean }
): Promise<ApiResponse<TouchdownRow[]>> {
  let path = `/api/analytics/all-touchdowns?season=${season}`;
  if (opts?.week != null) path += `&week=${opts.week}`;
  if (opts?.team) path += `&team=${encodeURIComponent(opts.team)}`;
  if (opts?.first_td_only) path += "&first_td_only=true";
  return request(path, token);
}

export type UserStatsPerformance = {
  user_id: number;
  user_name: string;
  season: number;
  total_picks: number;
  wins: number;
  losses: number;
  win_rate: number;
  brier_score: number;
  current_streak: number;
  longest_win_streak: number;
  is_hot: boolean;
};

export async function getUserStatsPerformanceServer(
  season: number,
  token: string
): Promise<ApiResponse<UserStatsPerformance>> {
  return request(`/api/analytics/user-stats?season=${season}`, token);
}

export type PerformanceBreakdownRow = {
  user_id: number;
  user_name: string;
  total_picks: number;
  wins: number;
  losses: number;
  win_rate: number;
  brier_score: number;
  current_streak: number;
  is_hot: boolean;
};

export async function getPerformanceBreakdownServer(
  season: number,
  token: string
): Promise<ApiResponse<PerformanceBreakdownRow[]>> {
  return request(`/api/analytics/performance-breakdown?season=${season}`, token);
}

export type UserStats = {
  user_id: number;
  user_name: string;
  weeks_participated: number;
  total_picks: number;
  correct_picks: number;
  any_time_td_hits: number;
  total_points: number;
  roi_dollars: number;
  win_percentage: number;
  avg_points_per_pick: number;
};

export async function getUserStatsServer(
  userId: number,
  token: string
): Promise<ApiResponse<UserStats>> {
  return request(`/api/leaderboard/user/${userId}/stats`, token);
}

export type GradedPick = {
  pick_id: number;
  player_name: string;
  team: string;
  odds: number | null;
  week: number;
  season: number;
  is_correct: boolean;
  any_time_td: boolean;
  actual_scorer: string | null;
  roi: number;
};

export async function getUserGradedPicksServer(
  userId: number,
  token: string,
  season?: number
): Promise<ApiResponse<GradedPick[]>> {
  const path = season
    ? `/api/leaderboard/user/${userId}/picks?season=${season}&limit=100`
    : `/api/leaderboard/user/${userId}/picks?limit=100`;
  return request(path, token);
}

export async function getWeekPicksServer(
  weekId: number,
  token: string
): Promise<ApiResponse<WeekPicksResponse>> {
  return request(`/api/weeks/${weekId}/picks`, token);
}

export async function getMatchupAnalysisServer(
  gameId: string,
  token: string
): Promise<ApiResponse<MatchupResponse>> {
  return request(`/api/analytics/matchup/${gameId}`, token);
}

// Admin types
export type AdminStats = {
  system_stats: {
    total_users: number;
    total_picks: number;
    graded_picks: number;
    ungraded_picks: number;
    grading_progress: number;
    total_seasons: number;
  };
};

export type User = {
  id: number;
  name: string;
  email: string | null;
  is_admin: boolean;
  base_bet?: number | null;
};

export type CurrentUser = {
  id: number;
  name: string;
  role: string;
};

export async function getCurrentUserServer(
  token: string
): Promise<ApiResponse<CurrentUser>> {
  return request("/api/auth/me", token);
}

export async function updateUserBaseBet(
  userId: number,
  baseBet: number,
  token?: string
): Promise<ApiResponse<User>> {
  const path = `/api/users/${userId}/base-bet`;
  const url = buildUrl(path);
  const t = token ?? getStoredToken();
  const headers: HeadersInit = { "Content-Type": "application/json" };
  if (t) headers["Authorization"] = `Bearer ${t}`;
  try {
    const response = await fetchWithTimeout(url, {
      method: "PATCH",
      headers,
      body: JSON.stringify({ base_bet: baseBet }),
    });
    if (!response.ok) {
      const errBody = (await response.json()) as { detail?: string };
      return normalizeError(response.status, errBody?.detail);
    }
    const data = (await response.json()) as User;
    return { ok: true, data };
  } catch {
    return normalizeError();
  }
}

export type Week = {
  id: number;
  season: number;
  week: number;
  started_at: string | null;
  ended_at: string | null;
};

export type Pick = {
  id: number;
  user_id: number;
  week_id: number;
  team: string;
  player_name: string;
  odds: number | null;
  game_id: string | null;
};

export type PickWithResult = Pick & {
  result_id: number | null;
  is_correct: boolean | null;
  any_time_td: boolean | null;
};

// Admin server-side helpers
export async function getAdminStatsServer(
  token: string
): Promise<ApiResponse<AdminStats>> {
  return request("/api/admin/stats", token);
}

export async function getUsersServer(
  token: string
): Promise<ApiResponse<User[]>> {
  return request("/api/users", token);
}

export async function getUserServer(
  userId: number,
  token: string
): Promise<ApiResponse<User>> {
  return request(`/api/users/${userId}`, token);
}

export async function getAdminUserPicksWithResultsServer(
  userId: number,
  token: string
): Promise<ApiResponse<PickWithResult[]>> {
  const path = `/api/admin/users/${userId}/picks-with-results`;
  const url = buildUrl(path);
  try {
    const response = await fetchWithTimeout(url, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!response.ok) {
      const errBody = (await response.json()) as { detail?: string };
      return normalizeError(response.status, errBody?.detail);
    }
    const data = (await response.json()) as PickWithResult[];
    return { ok: true, data };
  } catch {
    return normalizeError();
  }
}

export async function getWeeksServer(
  season: number,
  token: string
): Promise<ApiResponse<Week[]>> {
  const res = await request<Week[]>(`/api/weeks?season=${season}`, token);
  if (res.ok) return res;
  return request<Week[]>(`/api/weeks/season/${season}/weeks`, token);
}

export async function getPicksServer(
  token: string,
  weekId?: number,
  userId?: number
): Promise<ApiResponse<Pick[]>> {
  const params = new URLSearchParams();
  if (weekId != null) params.set("week_id", String(weekId));
  if (userId != null) params.set("user_id", String(userId));
  const qs = params.toString();
  const path = qs ? `/api/picks?${qs}` : "/api/picks";

  // Bypass cache for filtered requests (user_id/week_id) to avoid stale cross-user data
  if (qs) {
    const url = buildUrl(path);
    const headers: HeadersInit = { Authorization: `Bearer ${token}` };
    try {
      const response = await fetchWithTimeout(url, { headers });
      if (!response.ok) {
        const errBody = (await response.json()) as { detail?: string };
        return normalizeError(response.status, errBody?.detail);
      }
      const data = (await response.json()) as Pick[];
      return { ok: true, data };
    } catch {
      return normalizeError();
    }
  }

  return request(path, token);
}

export async function postRequest<T>(
  path: string,
  body: unknown,
  token: string
): Promise<ApiResponse<T>> {
  const url = buildUrl(path);
  try {
    const response = await fetchWithTimeout(url, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify(body),
    });
    if (response.ok) {
      const data = (await response.json()) as T;
      return { ok: true, data };
    }
    return normalizeError(response.status);
  } catch {
    return normalizeError();
  }
}

export type PickCreate = {
  week_id: number;
  team: string;
  player_name: string;
  odds: number;
  game_id: string;
};

export async function submitPick(
  pick: PickCreate
): Promise<ApiResponse<Pick>> {
  const token = getStoredToken();
  if (!token) return { ok: false, error: { message: "Not authenticated" } };
  return postRequest("/api/picks", pick, token);
}

export type PickUpdate = {
  team?: string;
  player_name?: string;
  odds?: number;
};

export async function updatePickServer(
  pickId: number,
  updates: PickUpdate,
  token: string
): Promise<ApiResponse<Pick>> {
  const url = buildUrl(`/api/picks/${pickId}`);
  try {
    const response = await fetchWithTimeout(url, {
      method: "PATCH",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify(updates),
    });
    if (response.ok) {
      const data = (await response.json()) as Pick;
      return { ok: true, data };
    }
    const errBody = (await response.json()) as { detail?: string };
    return normalizeError(response.status, errBody?.detail);
  } catch {
    return normalizeError();
  }
}

export async function updateResultServer(
  pickId: number,
  isCorrect: boolean,
  token: string
): Promise<ApiResponse<{ is_correct: boolean }>> {
  const url = buildUrl(`/api/results/by-pick/${pickId}`);
  try {
    const response = await fetchWithTimeout(url, {
      method: "PATCH",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({ is_correct: isCorrect }),
    });
    if (response.ok) {
      const data = (await response.json()) as { is_correct: boolean };
      return { ok: true, data };
    }
    const errBody = (await response.json()) as { detail?: string };
    return normalizeError(response.status, errBody?.detail);
  } catch {
    return normalizeError();
  }
}

export async function deletePickServer(
  pickId: number,
  token: string
): Promise<ApiResponse<void>> {
  const url = buildUrl(`/api/picks/${pickId}`);
  try {
    const response = await fetchWithTimeout(url, {
      method: "DELETE",
      headers: { Authorization: `Bearer ${token}` },
    });
    if (response.status === 204 || response.ok) {
      return { ok: true, data: undefined as void };
    }
    const errBody = (await response.json()) as { detail?: string };
    return normalizeError(response.status, errBody?.detail);
  } catch {
    return normalizeError();
  }
}

// Rosters
export type RosterPlayer = {
  player_name: string;
  team: string;
  position: string;
};

export async function getRosterPlayers(
  team: string,
  season: number,
  token?: string | null
): Promise<ApiResponse<RosterPlayer[]>> {
  const t = token ?? getStoredToken();
  if (!t) return { ok: false, error: { message: "Not authenticated" } };
  return request(
    `/api/rosters?team=${encodeURIComponent(team)}&season=${season}`,
    t
  );
}

// Admin create pick
export type AdminPickCreate = {
  user_id: number;
  week_id: number;
  team: string;
  player_name: string;
  odds: number | null;
  game_id: string | null;
};

export async function createAdminPick(
  pick: AdminPickCreate,
  token?: string | null
): Promise<ApiResponse<Pick>> {
  const t = token ?? getStoredToken();
  if (!t) return { ok: false, error: { message: "Not authenticated" } };
  return postRequest<Pick>("/api/admin/picks", pick, t);
}
