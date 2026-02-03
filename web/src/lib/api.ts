import { getCache, setCache } from "./cache";

const TIMEOUT_MS = 8_000;
const CACHE_TTL_MS = 60_000;

function getBaseUrl(): string {
  return process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";
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

async function fetchWithTimeout(url: string): Promise<Response> {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), TIMEOUT_MS);

  try {
    return await fetch(url, { signal: controller.signal });
  } finally {
    clearTimeout(timeoutId);
  }
}

export async function request<T>(path: string): Promise<ApiResponse<T>> {
  const url = buildUrl(path);
  const cached = getCache<ApiSuccess<T>>(url);
  if (cached) {
    return cached;
  }

  let response: Response | null = null;

  for (let attempt = 0; attempt < 2; attempt += 1) {
    try {
      response = await fetchWithTimeout(url);
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

export async function getMatchup(
  gameId: string
): Promise<ApiResponse<MatchupResponse>> {
  return request(`/api/analytics/matchup/${gameId}`);
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