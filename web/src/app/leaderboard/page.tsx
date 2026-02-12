import DashboardLayoutWrapper from "@/components/layout/DashboardLayoutWrapper";
import LeaderboardTable from "@/components/leaderboard/LeaderboardTable";
import ErrorBanner from "@/components/ui/ErrorBanner";
import Skeleton from "@/components/ui/Skeleton";
import { getLeaderboardServer } from "@/lib/api";
import { getServerToken } from "@/lib/server-token";
import { Suspense } from "react";

const CURRENT_SEASON = parseInt(process.env.NEXT_PUBLIC_CURRENT_SEASON ?? "2025", 10);

async function LeaderboardData() {
  const testUsername = process.env.NEXT_PUBLIC_TEST_USERNAME ?? "Phil";

  const token = await getServerToken(testUsername);
  if (!token) {
    return <ErrorBanner message="Failed to authenticate with backend" />;
  }

  const response = await getLeaderboardServer(CURRENT_SEASON, token);

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
    <DashboardLayoutWrapper>
      <div className="flex flex-col gap-6">
        <div>
          <h1 className="text-2xl font-black tracking-widest text-[#234058] uppercase font-mono">
            Leaderboard
          </h1>
          <p className="mt-2 text-sm text-[#78716c] font-mono">
            Season {CURRENT_SEASON} standings
          </p>
        </div>

        <Suspense fallback={<LeaderboardSkeleton />}>
          <LeaderboardData />
        </Suspense>
      </div>
    </DashboardLayoutWrapper>
  );
}
