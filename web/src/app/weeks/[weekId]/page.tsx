import DashboardLayoutWrapper from "@/components/layout/DashboardLayoutWrapper";
import WeekPicksTable from "@/components/weeks/WeekPicksTable";
import WeekSelector from "@/components/weeks/WeekSelector";
import ErrorBanner from "@/components/ui/ErrorBanner";
import Skeleton from "@/components/ui/Skeleton";
import { getWeekPicksServer, getWeekLeaderboardServer, getWeeksServer } from "@/lib/api";
import { getServerToken } from "@/lib/server-token";
import { Suspense } from "react";

const CURRENT_SEASON = parseInt(process.env.NEXT_PUBLIC_CURRENT_SEASON ?? "2025", 10);
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
    <div className="overflow-x-auto rounded-lg border-2 border-[#d1d5db] bg-[#fff] shadow-sm">
      <table
        className="w-full text-left text-sm font-mono"
        aria-label="Week leaderboard standings"
      >
        <thead className="bg-[#f8fafc] border-b-2 border-[#d1d5db]">
          <tr>
            <th
              scope="col"
              className="px-4 py-3 font-bold uppercase tracking-[0.15em] text-[#64748b] text-[10px]"
            >
              #
            </th>
            <th
              scope="col"
              className="px-4 py-3 font-bold uppercase tracking-[0.15em] text-[#64748b] text-[10px]"
            >
              Agent
            </th>
            <th
              scope="col"
              className="px-4 py-3 text-right font-bold uppercase tracking-[0.15em] text-[#64748b] text-[10px]"
            >
              Picks
            </th>
            <th
              scope="col"
              className="px-4 py-3 text-right font-bold uppercase tracking-[0.15em] text-[#64748b] text-[10px]"
            >
              Correct
            </th>
            <th
              scope="col"
              className="px-4 py-3 text-right font-bold uppercase tracking-[0.15em] text-[#64748b] text-[10px]"
            >
              Points
            </th>
            <th
              scope="col"
              className="px-4 py-3 text-right font-bold uppercase tracking-[0.15em] text-[#64748b] text-[10px]"
            >
              ROI
            </th>
          </tr>
        </thead>
        <tbody>
          {data.map((entry) => (
            <tr
              key={entry.user_id}
              className="border-b border-dashed border-[#e5e7eb] hover:bg-[#fff7ed] transition-colors"
            >
              <td className="px-4 py-3 font-bold text-[#A2877D]">
                {String(entry.rank).padStart(2, "0")}
              </td>
              <td className="px-4 py-3 font-bold text-[#234058]">
                {entry.user_name}
              </td>
              <td className="px-4 py-3 text-right text-[#44403c]">
                {entry.picks_count}
              </td>
              <td className="px-4 py-3 text-right">
                <span className="font-bold text-[#15803d]">
                  {entry.correct_count}
                </span>
              </td>
              <td className="px-4 py-3 text-right font-bold text-[#234058]">
                +{entry.total_points}
              </td>
              <td className="px-4 py-3 text-right font-bold">
                <span
                  className={
                    entry.roi_dollars >= 0
                      ? "text-[#15803d]"
                      : "text-[#8C302C]"
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
      <DashboardLayoutWrapper>
        <ErrorBanner message="Invalid week ID. Please provide a valid numeric week ID." />
      </DashboardLayoutWrapper>
    );
  }

  const token = await getServerToken(TEST_USERNAME);
  if (!token) {
    return (
      <DashboardLayoutWrapper>
        <ErrorBanner message="Failed to authenticate with backend" />
      </DashboardLayoutWrapper>
    );
  }

  const weeksRes = await getWeeksServer(CURRENT_SEASON, token);
  let weeks = weeksRes.ok ? weeksRes.data : [];
  if (weeks.length === 0) {
    weeks = [{ id: weekId, season: CURRENT_SEASON, week: weekId, started_at: null, ended_at: null }];
  }

  return (
    <DashboardLayoutWrapper>
      <div className="flex flex-col gap-6">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <h1 className="text-2xl font-black tracking-widest text-[#234058] uppercase font-mono">
              Week {weekId}
            </h1>
            <p className="mt-2 text-sm text-[#78716c] font-mono">
              Season {CURRENT_SEASON} picks and standings
            </p>
          </div>
          <WeekSelector
            weeks={weeks}
            currentWeekId={weekId}
            season={CURRENT_SEASON}
          />
        </div>

        <div className="space-y-6">
          <div>
            <h2 className="mb-4 text-sm font-black tracking-widest uppercase text-[#234058] font-mono">
              All Picks
            </h2>
            <Suspense fallback={<WeekPicksSkeleton />}>
              <WeekPicksData weekId={weekId} token={token} />
            </Suspense>
          </div>

          <div>
            <h2 className="mb-4 text-sm font-black tracking-widest uppercase text-[#234058] font-mono">
              Week Leaderboard
            </h2>
            <Suspense fallback={<WeekPicksSkeleton />}>
              <WeekLeaderboardData weekId={weekId} token={token} />
            </Suspense>
          </div>
        </div>
      </div>
    </DashboardLayoutWrapper>
  );
}
