import DashboardLayoutWrapper from "@/components/layout/DashboardLayoutWrapper";
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
      <DashboardLayoutWrapper>
        <ErrorBanner message="Failed to authenticate with backend" />
      </DashboardLayoutWrapper>
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
    <DashboardLayoutWrapper>
      <header className="flex flex-wrap items-center justify-between gap-4 mb-8">
        <div>
          <p className="text-xs font-bold uppercase tracking-[0.3em] text-[#78716c] font-mono">
            fast6 analytics
          </p>
          <h1 className="mt-2 text-2xl font-black tracking-widest text-[#234058] uppercase font-mono">
            Weekly overview
          </h1>
          <p className="mt-2 text-sm text-[#78716c] font-mono">
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

      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4 mb-8">
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
              ? `${topPerformer.total_points} pts · ${topPerformer.win_percentage.toFixed(0)}% win rate`
              : "No data yet"
          }
        />
      </section>

      <section className="grid gap-6 lg:grid-cols-[2fr,1fr]">
        <ChartCard title="Leaderboard snapshot" subtitle="Current season standings">
          {leaderboard.length === 0 ? (
            <p className="py-8 text-center text-sm text-[#78716c] font-mono">
              No leaderboard data yet
            </p>
          ) : (
            <ul className="space-y-3 text-sm font-mono">
              {leaderboard.slice(0, 5).map((entry) => (
                <li
                  key={entry.user_id}
                  className="flex items-center justify-between py-2 border-b border-dashed border-[#e5e7eb] last:border-0"
                >
                  <span className="flex items-center gap-2">
                    <span className="font-bold text-[#234058]">
                      {entry.rank === 1 && "🥇 "}
                      {entry.rank === 2 && "🥈 "}
                      {entry.rank === 3 && "🥉 "}
                      {entry.user_name}
                    </span>
                  </span>
                  <span className="flex items-center gap-4">
                    <span className="text-[#78716c]">
                      {entry.total_points} pts
                    </span>
                    <span
                      className={
                        entry.roi_dollars >= 0
                          ? "font-bold text-[#15803d]"
                          : "font-bold text-[#8C302C]"
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
          <ul className="space-y-3 text-sm font-mono">
            <li className="flex items-center justify-between py-2 border-b border-dashed border-[#e5e7eb] last:border-0">
              <span className="text-[#78716c]">Total weeks</span>
              <span className="font-bold text-[#234058]">
                {stats?.total_weeks ?? "\u2014"}
              </span>
            </li>
            <li className="flex items-center justify-between py-2 border-b border-dashed border-[#e5e7eb] last:border-0">
              <span className="text-[#78716c]">Total correct</span>
              <span className="font-bold text-[#234058]">
                {stats?.total_correct ?? "\u2014"}
              </span>
            </li>
            <li className="flex items-center justify-between py-2 border-b border-dashed border-[#e5e7eb] last:border-0">
              <span className="text-[#78716c]">Best ROI</span>
              <span className="font-bold text-[#15803d]">
                {topPerformer
                  ? `$${topPerformer.roi_dollars.toFixed(1)}`
                  : "\u2014"}
              </span>
            </li>
          </ul>
        </ChartCard>
      </section>
    </DashboardLayoutWrapper>
  );
}
