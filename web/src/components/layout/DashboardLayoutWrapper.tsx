import DashboardLayout from "./DashboardLayout";
import {
  getRoiTrendsByUserServer,
  getLeaderboardServer,
} from "@/lib/api";
import { getServerToken } from "@/lib/server-token";
import type { ReactNode } from "react";

interface DashboardLayoutWrapperProps {
  children: ReactNode;
}

export default async function DashboardLayoutWrapper({
  children,
}: DashboardLayoutWrapperProps) {
  const season = parseInt(process.env.NEXT_PUBLIC_CURRENT_SEASON ?? "2025", 10);
  const testUsername = process.env.NEXT_PUBLIC_TEST_USERNAME ?? "Phil";

  const token = await getServerToken(testUsername);

  const [roiRes, leaderboardRes] =
    token
      ? await Promise.all([
          getRoiTrendsByUserServer(season, token),
          getLeaderboardServer(season, token),
        ])
      : [null, null];

  const roiTrendsByUser = roiRes?.ok ? roiRes.data : [];
  const leaderboard = leaderboardRes?.ok ? leaderboardRes.data : [];

  return (
    <DashboardLayout
      roiTrendsByUser={roiTrendsByUser}
      leaderboard={leaderboard}
    >
      {children}
    </DashboardLayout>
  );
}
