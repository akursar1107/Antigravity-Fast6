import DashboardLayoutWrapper from "@/components/layout/DashboardLayoutWrapper";
import ErrorBanner from "@/components/ui/ErrorBanner";
import Badge from "@/components/ui/Badge";
import RoiChart from "@/components/analytics/RoiChart";
import PlayerStatsTable from "@/components/analytics/PlayerStatsTable";
import OddsAccuracyTable from "@/components/analytics/OddsAccuracyTable";
import TeamDefenseTable from "@/components/analytics/TeamDefenseTable";
import {
  getRoiTrendsServer,
  getPlayerStatsServer,
  getOddsAccuracyServer,
  getTeamDefenseServer,
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
  ] = await Promise.all([
    getRoiTrendsServer(season, token),
    getPlayerStatsServer(season, token),
    getOddsAccuracyServer(season, token),
    getTeamDefenseServer(season, token),
  ]);

  return (
    <DashboardLayoutWrapper>
      <header className="flex flex-wrap items-center justify-between gap-4 mb-8">
        <div>
          <p className="text-xs font-bold uppercase tracking-[0.3em] text-[#78716c] font-mono">
            advanced analytics
          </p>
          <h1 className="mt-2 text-2xl font-black tracking-widest text-[#234058] uppercase font-mono">
            Performance insights
          </h1>
          <p className="mt-2 text-sm text-[#78716c] font-mono">
            ROI trends and player statistics across the season.
          </p>
        </div>
        <Badge label={`Season ${season}`} tone="info" />
      </header>

      <section className="flex flex-col gap-6">
        <div className="rounded-lg border-2 border-[#d1d5db] bg-[#fff] p-6 shadow-sm">
          <div className="mb-4">
            <h2 className="text-sm font-black tracking-widest uppercase text-[#234058] font-mono">
              ROI by week
            </h2>
            <p className="mt-1 text-xs text-[#78716c] font-mono">
              Return on investment over the season
            </p>
          </div>
          {!roiTrendsResponse.ok ? (
            <ErrorBanner
              title="Failed to load ROI trends"
              message={roiTrendsResponse.error.message}
            />
          ) : (
            <RoiChart data={roiTrendsResponse.data} />
          )}
        </div>

        <div className="rounded-lg border-2 border-[#d1d5db] bg-[#fff] p-6 shadow-sm">
          <div className="mb-4">
            <h2 className="text-sm font-black tracking-widest uppercase text-[#234058] font-mono">
              Player performance
            </h2>
            <p className="mt-1 text-xs text-[#78716c] font-mono">
              Top players by first touchdown frequency
            </p>
          </div>
          {!playerStatsResponse.ok ? (
            <ErrorBanner
              title="Failed to load player stats"
              message={playerStatsResponse.error.message}
            />
          ) : (
            <PlayerStatsTable data={playerStatsResponse.data} />
          )}
        </div>

        <div className="rounded-lg border-2 border-[#d1d5db] bg-[#fff] p-6">
          <div className="mb-4">
            <h2 className="text-sm font-black tracking-widest uppercase text-[#234058] font-mono">
              Accuracy by odds range
            </h2>
            <p className="mt-1 text-xs text-[#78716c] font-mono">
              How well favorites vs longshots hit
            </p>
          </div>
          {!oddsAccuracyResponse.ok ? (
            <ErrorBanner
              title="Failed to load odds accuracy"
              message={oddsAccuracyResponse.error.message}
            />
          ) : (
            <OddsAccuracyTable data={oddsAccuracyResponse.data} />
          )}
        </div>

        <div className="rounded-lg border-2 border-[#d1d5db] bg-[#fff] p-6">
          <div className="mb-4">
            <h2 className="text-sm font-black tracking-widest uppercase text-[#234058] font-mono">
              Team matchup accuracy
            </h2>
            <p className="mt-1 text-xs text-[#78716c] font-mono">
              Accuracy when picking against each team
            </p>
          </div>
          {!teamDefenseResponse.ok ? (
            <ErrorBanner
              title="Failed to load team defense"
              message={teamDefenseResponse.error.message}
            />
          ) : (
            <TeamDefenseTable data={teamDefenseResponse.data} />
          )}
        </div>
      </section>
    </DashboardLayoutWrapper>
  );
}
