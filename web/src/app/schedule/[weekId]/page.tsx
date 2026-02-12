import DashboardLayoutWrapper from "@/components/layout/DashboardLayoutWrapper";
import ScheduleWeekSelector from "@/components/schedule/ScheduleWeekSelector";
import ScheduleGamesSection from "@/components/schedule/ScheduleGamesSection";
import ErrorBanner from "@/components/ui/ErrorBanner";
import Skeleton from "@/components/ui/Skeleton";
import type { Week } from "@/lib/api";
import { getWeeksServer, getGamesServer, getGamesWeeksServer } from "@/lib/api";
import { getServerToken } from "@/lib/server-token";
import { Suspense } from "react";

const CURRENT_SEASON = parseInt(process.env.NEXT_PUBLIC_CURRENT_SEASON ?? "2025", 10);
const TEST_USERNAME = process.env.NEXT_PUBLIC_TEST_USERNAME ?? "Phil";

interface PageProps {
  params: Promise<{
    weekId: string;
  }>;
}

async function ScheduleGamesData({
  weekId,
  weekNumber,
  token,
}: {
  weekId: number;
  weekNumber: number;
  token: string;
}) {
  const response = await getGamesServer(CURRENT_SEASON, token, weekNumber);

  if (!response.ok) {
    return (
      <ErrorBanner
        message={response.error.message || "Failed to load games"}
      />
    );
  }

  return <ScheduleGamesSection games={response.data} />;
}

function ScheduleSkeleton() {
  return (
    <div className="flex flex-col gap-3">
      <Skeleton className="h-16 w-full" />
      <Skeleton className="h-16 w-full" />
      <Skeleton className="h-16 w-full" />
      <Skeleton className="h-16 w-full" />
    </div>
  );
}

export default async function ScheduleWeekPage(props: PageProps) {
  const params = await props.params;
  const weekId = parseInt(params.weekId, 10);

  if (Number.isNaN(weekId)) {
    return (
      <DashboardLayoutWrapper>
        <ErrorBanner message="Invalid week. Please select a valid week." />
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

  const [weeksRes, gamesWeeksRes] = await Promise.all([
    getWeeksServer(CURRENT_SEASON, token),
    getGamesWeeksServer(CURRENT_SEASON, token),
  ]);

  let weeks: Week[];
  if (gamesWeeksRes.ok && gamesWeeksRes.data.length > 0) {
    weeks = gamesWeeksRes.data.map((weekNum) => ({
      id: weekNum,
      season: CURRENT_SEASON,
      week: weekNum,
      started_at: null,
      ended_at: null,
    }));
  } else if (weeksRes.ok && weeksRes.data.length > 0) {
    weeks = weeksRes.data;
  } else {
    weeks = Array.from({ length: 18 }, (_, i) => ({
      id: i + 1,
      season: CURRENT_SEASON,
      week: i + 1,
      started_at: null,
      ended_at: null,
    }));
  }

  const selectedWeek = weeks.find((w) => w.id === weekId);
  const weekNumber = selectedWeek?.week ?? weekId;

  return (
    <DashboardLayoutWrapper>
      <div className="flex flex-col gap-6">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <h1 className="text-2xl font-black tracking-widest text-[#234058] uppercase font-mono">
              Schedule
            </h1>
            <p className="mt-2 text-sm text-[#78716c] font-mono">
              Season {CURRENT_SEASON} — Week {weekNumber} games
            </p>
          </div>
          <ScheduleWeekSelector
            weeks={weeks}
            currentWeekId={weekId}
            season={CURRENT_SEASON}
          />
        </div>

        <div>
          <h2 className="mb-4 text-sm font-black tracking-widest uppercase text-[#234058] font-mono">
            Games
          </h2>
          <Suspense fallback={<ScheduleSkeleton />}>
            <ScheduleGamesData
              weekId={weekId}
              weekNumber={weekNumber}
              token={token}
            />
          </Suspense>
        </div>
      </div>
    </DashboardLayoutWrapper>
  );
}
