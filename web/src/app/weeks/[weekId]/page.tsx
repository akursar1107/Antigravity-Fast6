import DashboardLayout from "@/components/layout/DashboardLayout";
import WeekPicksTable from "@/components/weeks/WeekPicksTable";
import ErrorBanner from "@/components/ui/ErrorBanner";
import Skeleton from "@/components/ui/Skeleton";
import { getWeekPicksServer, getWeekLeaderboardServer } from "@/lib/api";
import { getServerToken } from "@/lib/server-token";
import { Suspense } from "react";

const CURRENT_SEASON = parseInt(process.env.NEXT_PUBLIC_CURRENT_SEASON ?? '2025', 10);
const TEST_USERNAME = process.env.NEXT_PUBLIC_TEST_USERNAME ?? "Phil";

interface PageProps {
  params: Promise<{
    weekId: string;
  }>;
}

async function WeekPicksData({ weekId, token }: { weekId: number; token: string }) {
  const response = await getWeekPicksServer(weekId, token);

  if (!response.ok) {
    return (
      <ErrorBanner
        message={response.error.message || "Failed to load week picks"}
      />
    );
  }

  return <WeekPicksTable picks={response.data.picks} />;
}

async function WeekLeaderboardData({ weekId, token }: { weekId: number; token: string }) {
  const response = await getWeekLeaderboardServer(weekId, token);

  if (!response.ok) {
    return null;
  }

  const data = response.data;

  if (data.length === 0) {
    return null;
  }

  return (
    <div className="overflow-x-auto rounded-2xl border border-slate-800 bg-slate-900/60">
      <table
        className="w-full text-left text-sm"
        aria-label="Week leaderboard standings"
      >
        <thead className="border-b border-slate-800 bg-slate-900/80">
          <tr>
            <th
              scope="col"
              className="px-4 py-3 font-semibold uppercase tracking-[0.15em] text-slate-400"
            >
              Rank
            </th>
            <th
              scope="col"
              className="px-4 py-3 font-semibold uppercase tracking-[0.15em] text-slate-400"
            >
              User
            </th>
            <th
              scope="col"
              className="px-4 py-3 text-right font-semibold uppercase tracking-[0.15em] text-slate-400"
            >
              Picks
            </th>
            <th
              scope="col"
              className="px-4 py-3 text-right font-semibold uppercase tracking-[0.15em] text-slate-400"
            >
              Correct
            </th>
            <th
              scope="col"
              className="px-4 py-3 text-right font-semibold uppercase tracking-[0.15em] text-slate-400"
            >
              Points
            </th>
            <th
              scope="col"
              className="px-4 py-3 text-right font-semibold uppercase tracking-[0.15em] text-slate-400"
            >
              ROI
            </th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-800">
          {data.map((entry) => (
            <tr key={entry.user_id} className="hover:bg-slate-800/30 transition-colors">
              <td className="px-4 py-3 font-bold text-indigo-400">
                #{entry.rank}
              </td>
              <td className="px-4 py-3 text-slate-100">
                <span className="font-medium">{entry.user_name}</span>
              </td>
              <td className="px-4 py-3 text-right text-slate-300">
                {entry.picks_count}
              </td>
              <td className="px-4 py-3 text-right">
                <span className="inline-flex items-center gap-1 font-semibold text-emerald-300">
                  {entry.correct_count}
                </span>
              </td>
              <td className="px-4 py-3 text-right font-bold text-indigo-300">
                +{entry.total_points}
              </td>
              <td className="px-4 py-3 text-right font-semibold">
                <span
                  className={
                    entry.roi_dollars >= 0
                      ? "text-emerald-400"
                      : "text-rose-400"
                  }
                >
                  ${entry.roi_dollars.toFixed(2)}
                </span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function WeekPicksSkeleton() {
  return (
    <div className="flex flex-col gap-3">
      <Skeleton className="h-12 w-full" />
      <Skeleton className="h-20 w-full" />
      <Skeleton className="h-20 w-full" />
      <Skeleton className="h-20 w-full" />
    </div>
  );
}

export default async function WeekPage(props: PageProps) {
  const params = await props.params;
  const weekId = parseInt(params.weekId, 10);

  if (Number.isNaN(weekId)) {
    return (
      <DashboardLayout>
        <ErrorBanner message="Invalid week ID. Please provide a valid numeric week ID." />
      </DashboardLayout>
    );
  }

  // Get server-side token
  const token = await getServerToken(TEST_USERNAME);
  if (!token) {
    return (
      <DashboardLayout>
        <ErrorBanner message="Failed to authenticate with backend" />
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout>
      <div className="flex flex-col gap-6">
        <div>
          <h1 className="text-3xl font-bold text-slate-50">
            Week {weekId}
          </h1>
          <p className="mt-2 text-sm text-slate-400">
            Season {CURRENT_SEASON} picks and standings
          </p>
        </div>

        <div className="space-y-6">
          {/* Picks Section */}
          <div>
            <h2 className="mb-4 text-xl font-semibold text-slate-50">
              All Picks
            </h2>
            <Suspense fallback={<WeekPicksSkeleton />}>
              <WeekPicksData weekId={weekId} token={token} />
            </Suspense>
          </div>

          {/* Leaderboard Section */}
          <div>
            <h2 className="mb-4 text-xl font-semibold text-slate-50">
              Week Leaderboard
            </h2>
            <Suspense fallback={<WeekPicksSkeleton />}>
              <WeekLeaderboardData weekId={weekId} token={token} />
            </Suspense>
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}
