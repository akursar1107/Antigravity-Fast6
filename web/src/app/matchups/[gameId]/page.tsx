import DashboardLayout from "@/components/layout/DashboardLayout";
import MatchupCard from "@/components/matchups/MatchupCard";
import ErrorBanner from "@/components/ui/ErrorBanner";
import Skeleton from "@/components/ui/Skeleton";
import { getMatchupAnalysisServer } from "@/lib/api";
import { getServerToken } from "@/lib/server-token";
import { Suspense } from "react";

const TEST_USERNAME = process.env.NEXT_PUBLIC_TEST_USERNAME ?? "Phil";

interface PageProps {
  params: Promise<{
    gameId: string;
  }>;
}

async function MatchupData({ gameId, token }: { gameId: string; token: string }) {
  const response = await getMatchupAnalysisServer(gameId, token);

  if (!response.ok) {
    return (
      <ErrorBanner
        message={response.error.message || "Failed to load matchup data"}
      />
    );
  }

  return <MatchupCard data={response.data} />;
}

function MatchupSkeleton() {
  return (
    <div className="space-y-4">
      <Skeleton className="h-32 w-full" />
      <div className="grid grid-cols-2 gap-4">
        <Skeleton className="h-24 w-full" />
        <Skeleton className="h-24 w-full" />
      </div>
      <Skeleton className="h-24 w-full" />
    </div>
  );
}

export default async function MatchupPage(props: PageProps) {
  const params = await props.params;
  const gameId = params.gameId;

  if (!gameId || gameId.trim() === "") {
    return (
      <DashboardLayout>
        <ErrorBanner message="Invalid game ID. Please provide a valid game ID." />
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
            Matchup Analysis
          </h1>
          <p className="mt-2 text-sm text-slate-400">
            Game {gameId} - Team statistics and first TD probability
          </p>
        </div>

        <Suspense fallback={<MatchupSkeleton />}>
          <MatchupData gameId={gameId} token={token} />
        </Suspense>
      </div>
    </DashboardLayout>
  );
}
