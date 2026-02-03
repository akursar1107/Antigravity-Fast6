import DashboardLayout from "@/components/layout/DashboardLayout";
import ErrorBanner from "@/components/ui/ErrorBanner";
import Skeleton from "@/components/ui/Skeleton";
import Badge from "@/components/ui/Badge";
import RoiChart from "@/components/analytics/RoiChart";
import PlayerStatsTable from "@/components/analytics/PlayerStatsTable";
import { getRoiTrends, getPlayerStats } from "@/lib/api";

export default async function AnalyticsPage() {
  const season = parseInt(process.env.NEXT_PUBLIC_CURRENT_SEASON ?? "2025", 10);

  const [roiTrendsResponse, playerStatsResponse] = await Promise.all([
    getRoiTrends(season),
    getPlayerStats(season),
  ]);

  return (
    <DashboardLayout>
      <header className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <p className="text-xs uppercase tracking-[0.3em] text-slate-500">
            advanced analytics
          </p>
          <h1 className="mt-2 text-3xl font-semibold text-slate-50">
            Performance insights
          </h1>
          <p className="mt-2 text-sm text-slate-400">
            ROI trends and player statistics across the season.
          </p>
        </div>
        <Badge label={`Season ${season}`} tone="info" />
      </header>

      <section className="flex flex-col gap-6">
        <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6">
          <div className="mb-4">
            <h2 className="text-lg font-semibold text-slate-100">
              ROI by week
            </h2>
            <p className="text-sm text-slate-400">
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

        <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6">
          <div className="mb-4">
            <h2 className="text-lg font-semibold text-slate-100">
              Player performance
            </h2>
            <p className="text-sm text-slate-400">
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
      </section>
    </DashboardLayout>
  );
}
