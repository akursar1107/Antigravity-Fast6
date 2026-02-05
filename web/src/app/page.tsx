import DashboardLayout from "@/components/layout/DashboardLayout";
import Badge from "@/components/ui/Badge";
import ChartCard from "@/components/ui/ChartCard";
import StatCard from "@/components/ui/StatCard";
import ErrorBanner from "@/components/ui/ErrorBanner";
import { getLeaderboardServer, getSeasonStatsServer } from "@/lib/api";
import { getServerToken } from "@/lib/server-token";

export default async function Home() {
  const season = parseInt(process.env.NEXT_PUBLIC_CURRENT_SEASON ?? "2025", 10);
  const testUsername = process.env.NEXT_PUBLIC_TEST_USERNAME ?? "Phil";

  const token = await getServerToken(testUsername);
  if (!token) {
    return (
      <DashboardLayout>
        <ErrorBanner message="Failed to authenticate with backend" />
      </DashboardLayout>
    );
  }

  const [leaderboardRes, statsRes] = await Promise.all([
    getLeaderboardServer(season, token),
    getSeasonStatsServer(season, token),
  ]);

  const leaderboard = leaderboardRes.ok ? leaderboardRes.data : [];
  const stats = statsRes.ok ? statsRes.data : null;

  const totalPicks =
    stats?.total_picks ??
    leaderboard.reduce((sum, e) => sum + e.total_picks, 0);
  const accuracy =
    stats?.overall_accuracy ??
    (leaderboard.length > 0
      ? leaderboard.reduce((sum, e) => sum + e.win_percentage, 0) /
        leaderboard.length
      : 0);
  const topPerformer = leaderboard.length > 0 ? leaderboard[0] : null;
  const totalPlayers = stats?.total_players ?? leaderboard.length;

  const hasError = !leaderboardRes.ok && !statsRes.ok;

  return (
    <DashboardLayout>
      <header className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <p className="text-xs uppercase tracking-[0.3em] text-slate-500">
            fast6 analytics
          </p>
          <h1 className="mt-2 text-3xl font-semibold text-slate-50">
            Weekly overview
          </h1>
          <p className="mt-2 text-sm text-slate-400">
            Track picks, ROI, and player trends in one place.
          </p>
        </div>
        <Badge label={`Season ${season}`} tone="info" />
      </header>

      {hasError && (
        <ErrorBanner
          title="API unavailable"
          message="Could not reach the backend. Showing cached or empty data."
        />
      )}

      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <StatCard label="Total picks" value={totalPicks} helper="All active weeks" />
        <StatCard
          label="Accuracy"
          value={`${accuracy.toFixed(1)}%`}
          helper="Across graded picks"
        />
        <StatCard label="Players" value={totalPlayers} helper="Active this season" />
        <StatCard
          label="Top performer"
          value={topPerformer?.user_name ?? "\u2014"}
          helper={
            topPerformer
              ? `${topPerformer.total_points} pts \u00b7 ${topPerformer.win_percentage.toFixed(0)}% win rate`
              : "No data yet"
          }
        />
      </section>

      <section className="grid gap-6 lg:grid-cols-[2fr,1fr]">
        <ChartCard title="Leaderboard snapshot" subtitle="Current season standings">
          {leaderboard.length === 0 ? (
            <p className="py-8 text-center text-sm text-slate-500">
              No leaderboard data yet
            </p>
          ) : (
            <ul className="space-y-3 text-sm text-slate-300">
              {leaderboard.slice(0, 5).map((entry) => (
                <li
                  key={entry.user_id}
                  className="flex items-center justify-between"
                >
                  <span className="flex items-center gap-2">
                    <span className="font-medium text-slate-200">
                      {entry.rank === 1 && "\ud83e\uddc5 "}
                      {entry.rank === 2 && "\ud83e\uddc6 "}
                      {entry.rank === 3 && "\ud83e\uddc7 "}
                      {entry.user_name}
                    </span>
                  </span>
                  <span className="flex items-center gap-4">
                    <span className="text-slate-400">
                      {entry.total_points} pts
                    </span>
                    <span
                      className={
                        entry.roi_dollars >= 0
                          ? "text-emerald-400"
                          : "text-red-400"
                      }
                    >
                      ${entry.roi_dollars.toFixed(1)}
                    </span>
                  </span>
                </li>
              ))}
            </ul>
          )}
        </ChartCard>
        <ChartCard title="Quick stats" subtitle="Season at a glance">
          <ul className="space-y-3 text-sm text-slate-300">
            <li className="flex items-center justify-between">
              <span>Total weeks</span>
              <span className="text-slate-400">
                {stats?.total_weeks ?? "\u2014"}
              </span>
            </li>
            <li className="flex items-center justify-between">
              <span>Total correct</span>
              <span className="text-slate-400">
                {stats?.total_correct ?? "\u2014"}
              </span>
            </li>
            <li className="flex items-center justify-between">
              <span>Best ROI</span>
              <span className="text-emerald-400">
                {topPerformer
                  ? `$${topPerformer.roi_dollars.toFixed(1)}`
                  : "\u2014"}
              </span>
            </li>
          </ul>
        </ChartCard>
      </section>
    </DashboardLayout>
  );
}
