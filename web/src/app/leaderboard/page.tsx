import DashboardLayout from "@/components/layout/DashboardLayout";
import LeaderboardTable from "@/components/leaderboard/LeaderboardTable";
import ErrorBanner from "@/components/ui/ErrorBanner";
import Skeleton from "@/components/ui/Skeleton";
import { getLeaderboard } from "@/lib/api";
import { Suspense } from "react";

const CURRENT_SEASON = parseInt(process.env.NEXT_PUBLIC_CURRENT_SEASON ?? '2025', 10);

async function LeaderboardData() {
  const response = await getLeaderboard(CURRENT_SEASON);

  if (!response.ok) {
    return (
      <ErrorBanner
        message={response.error.message || "Failed to load leaderboard data"}
      />
    );
  }

  return <LeaderboardTable data={response.data} />;
}

function LeaderboardSkeleton() {
  return (
    <div className="flex flex-col gap-3">
      <Skeleton className="h-12 w-full" />
      <Skeleton className="h-20 w-full" />
      <Skeleton className="h-20 w-full" />
      <Skeleton className="h-20 w-full" />
      <Skeleton className="h-20 w-full" />
      <Skeleton className="h-20 w-full" />
    </div>
  );
}

export default function LeaderboardPage() {
  return (
    <DashboardLayout>
      <div className="flex flex-col gap-6">
        <div>
          <h1 className="text-3xl font-bold text-slate-50">Leaderboard</h1>
          <p className="mt-2 text-sm text-slate-400">
            Season {CURRENT_SEASON} standings
          </p>
        </div>

        <Suspense fallback={<LeaderboardSkeleton />}>
          <LeaderboardData />
        </Suspense>
      </div>
    </DashboardLayout>
  );
}
