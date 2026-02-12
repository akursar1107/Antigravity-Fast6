import DashboardLayoutWrapper from "@/components/layout/DashboardLayoutWrapper";
import ErrorBanner from "@/components/ui/ErrorBanner";
import Badge from "@/components/ui/Badge";
import AnalyticsTabs from "@/components/analytics/AnalyticsTabs";
import {
  getRoiTrendsServer,
  getPlayerStatsServer,
  getOddsAccuracyServer,
  getTeamDefenseServer,
  getAllTouchdownsServer,
  getUserStatsPerformanceServer,
  getPerformanceBreakdownServer,
} from "@/lib/api";
import { getServerToken } from "@/lib/server-token";

export default async function AnalyticsPage() {
  const season = parseInt(process.env.NEXT_PUBLIC_CURRENT_SEASON ?? "2025", 10);
  const testUsername = process.env.NEXT_PUBLIC_TEST_USERNAME ?? "Phil";

  const token = await getServerToken(testUsername);
  if (!token) {
    return (
      <DashboardLayoutWrapper>
        <ErrorBanner message="Failed to authenticate with backend" />
      </DashboardLayoutWrapper>
    );
  }

  const [
    roiTrendsResponse,
    playerStatsResponse,
    oddsAccuracyResponse,
    teamDefenseResponse,
    allTouchdownsResponse,
    userStatsResponse,
    performanceBreakdownResponse,
  ] = await Promise.all([
    getRoiTrendsServer(season, token),
    getPlayerStatsServer(season, token),
    getOddsAccuracyServer(season, token),
    getTeamDefenseServer(season, token),
    getAllTouchdownsServer(season, token),
    getUserStatsPerformanceServer(season, token),
    getPerformanceBreakdownServer(season, token),
  ]);

  const allTouchdowns = allTouchdownsResponse.ok ? allTouchdownsResponse.data : [];
  const userStats = userStatsResponse.ok ? userStatsResponse.data : null;

  return (
    <DashboardLayoutWrapper>
      <header className="flex flex-wrap items-center justify-between gap-4 mb-8">
        <div>
          <p className="text-xs font-bold uppercase tracking-[0.3em] text-[#5c5a57] font-mono">
            advanced analytics
          </p>
          <h1 className="mt-2 text-2xl font-black tracking-widest text-[#234058] uppercase font-mono">
            Performance insights
          </h1>
          <p className="mt-2 text-sm text-[#5c5a57] font-mono">
            ROI trends and player statistics across the season.
          </p>
        </div>
        <Badge label={`Season ${season}`} tone="info" />
      </header>

      <section>
        <AnalyticsTabs
          season={season}
          roiTrendsResponse={roiTrendsResponse}
          playerStatsResponse={playerStatsResponse}
          oddsAccuracyResponse={oddsAccuracyResponse}
          teamDefenseResponse={teamDefenseResponse}
          performanceBreakdownResponse={performanceBreakdownResponse}
          allTouchdowns={allTouchdowns}
          userStats={userStats}
        />
      </section>
    </DashboardLayoutWrapper>
  );
}
