import { getCache, setCache } from "./cache";

const TIMEOUT_MS = 8_000;
const CACHE_TTL_MS = 60_000;
const AUTH_STORAGE_KEY = "fast6_auth_token";

function getBaseUrl(): string {
  return process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";
}

function getStoredToken(): string | null {
  try {
    if (typeof window === "undefined") return null;
    return localStorage.getItem(AUTH_STORAGE_KEY);
  } catch {
    return null;
  }
}

function setStoredToken(token: string): void {
  try {
    if (typeof window === "undefined") return;
    localStorage.setItem(AUTH_STORAGE_KEY, token);
  } catch {
    // Silently fail if localStorage is unavailable
  }
}

export type ApiError = { ok: false; error: { message: string; status?: number } };

function normalizeError(status?: number): ApiError {
  return {
    ok: false,
    error: {
      message: "Request failed",
      status,
    },
  };
}
export type ApiSuccess<T> = { ok: true; data: T };
export type ApiResponse<T> = ApiSuccess<T> | ApiError;

function buildUrl(path: string): string {
  if (path.startsWith("http://") || path.startsWith("https://")) {
    return path;
  }

  return `${getBaseUrl()}${path}`;
}

async function fetchWithTimeout(url: string, options?: RequestInit): Promise<Response> {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), TIMEOUT_MS);

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
    } catch (error) {
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

    return normalizeError(response.status);
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

export type MatchupResponse = {
  game_id: string;
  teams: MatchupTeamStat[];
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

export async function getSeasonStats(
  season: number
): Promise<ApiResponse<SeasonStats>> {
  return request(`/api/leaderboard/season/${season}/stats`);
}

export async function getRoiTrends(
  season: number
): Promise<ApiResponse<RoiTrend[]>> {
  return request(`/api/analytics/roi-trends?season=${season}`);
}

export async function getOddsAccuracy(
  season: number
): Promise<ApiResponse<OddsAccuracy[]>> {
  return request(`/api/analytics/odds-accuracy?season=${season}`);
}

export async function getPlayerStats(
  season: number,
  limit = 50
): Promise<ApiResponse<PlayerStat[]>> {
  return request(`/api/analytics/player-stats?season=${season}&limit=${limit}`);
}

export async function getDefenseStats(
  season: number
): Promise<ApiResponse<DefenseStat[]>> {
  return request(`/api/analytics/team-defense?season=${season}`);
}

export async function getGradingStatus(
  season: number
): Promise<ApiResponse<GradingStatus>> {
  return request(`/api/analytics/grading-status?season=${season}`);
}

export async function getWeekPicks(
  weekId: number
): Promise<ApiResponse<WeekPicksResponse>> {
  return request(`/api/weeks/${weekId}/picks`);
}

export async function getMatchupAnalysis(
  gameId: string
): Promise<ApiResponse<MatchupResponse>> {
  return request(`/api/analytics/matchup/${gameId}`);
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
};

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

export async function getWeeksServer(
  season: number,
  token: string
): Promise<ApiResponse<Week[]>> {
  return request(`/api/weeks/season/${season}`, token);
}

export async function getPicksServer(
  token: string,
  weekId?: number
): Promise<ApiResponse<Pick[]>> {
  const path = weekId ? `/api/picks?week_id=${weekId}` : "/api/picks";
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

export async function deleteRequest<T>(
  path: string,
  token: string
): Promise<ApiResponse<T>> {
  const url = buildUrl(path);
  try {
    const response = await fetchWithTimeout(url, {
      method: "DELETE",
      headers: { Authorization: `Bearer ${token}` },
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
