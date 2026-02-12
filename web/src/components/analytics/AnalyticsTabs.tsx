"use client";

import type { ReactNode } from "react";
import Tabs from "@/components/ui/Tabs";
import ErrorBanner from "@/components/ui/ErrorBanner";
import RoiChart from "@/components/analytics/RoiChart";
import PlayerStatsTable from "@/components/analytics/PlayerStatsTable";
import OddsAccuracyTable from "@/components/analytics/OddsAccuracyTable";
import TeamDefenseTable from "@/components/analytics/TeamDefenseTable";
import AllTouchdownsTable from "@/components/analytics/AllTouchdownsTable";
import UserStatsCard from "@/components/analytics/UserStatsCard";
import PerformanceBreakdownTable from "@/components/analytics/PerformanceBreakdownTable";
import type {
  RoiTrend,
  PlayerStat,
  OddsAccuracy,
  DefenseStat,
  TouchdownRow,
  UserStatsPerformance,
  PerformanceBreakdownRow,
} from "@/lib/api";
import type { ApiResponse } from "@/lib/api";

interface AnalyticsTabsProps {
  season: number;
  roiTrendsResponse: ApiResponse<RoiTrend[]>;
  playerStatsResponse: ApiResponse<PlayerStat[]>;
  oddsAccuracyResponse: ApiResponse<OddsAccuracy[]>;
  teamDefenseResponse: ApiResponse<DefenseStat[]>;
  performanceBreakdownResponse: ApiResponse<PerformanceBreakdownRow[]>;
  allTouchdowns: TouchdownRow[];
  userStats: UserStatsPerformance | null;
}

function Card({
  title,
  description,
  children,
}: {
  title: string;
  description: string;
  children: ReactNode;
}) {
  return (
    <div className="rounded-lg border-2 border-[#d1d5db] bg-[#fff] p-6 shadow-sm">
      <div className="mb-4">
        <h2 className="text-sm font-black tracking-widest uppercase text-[#234058] font-mono">
          {title}
        </h2>
        <p className="mt-1 text-xs text-[#5c5a57] font-mono">{description}</p>
      </div>
      {children}
    </div>
  );
}

export default function AnalyticsTabs({
  season,
  roiTrendsResponse,
  playerStatsResponse,
  oddsAccuracyResponse,
  teamDefenseResponse,
  performanceBreakdownResponse,
  allTouchdowns,
  userStats,
}: AnalyticsTabsProps) {
  const tabs = [
    {
      id: "overview",
      label: "Overview",
      panel: (
        <div className="flex flex-col gap-6">
          <Card title="Your stats" description="Win rate, Brier score, and streaks">
            <UserStatsCard data={userStats} />
          </Card>
          <Card title="ROI by week" description="Return on investment over the season">
            {!roiTrendsResponse.ok ? (
              <ErrorBanner
                title="Failed to load ROI trends"
                message={roiTrendsResponse.error.message}
              />
            ) : (
              <RoiChart data={roiTrendsResponse.data} />
            )}
          </Card>
        </div>
      ),
    },
    {
      id: "performance",
      label: "Performance",
      panel: (
        <div className="flex flex-col gap-6">
          <Card
            title="Performance by picker"
            description="Multi-user comparison: win rate, Brier score, picks, streaks"
          >
            {!performanceBreakdownResponse.ok ? (
              <ErrorBanner
                title="Failed to load performance breakdown"
                message={performanceBreakdownResponse.error.message}
              />
            ) : (
              <PerformanceBreakdownTable data={performanceBreakdownResponse.data} />
            )}
          </Card>
          <Card
            title="Player performance"
            description="Top players by first touchdown frequency"
          >
            {!playerStatsResponse.ok ? (
              <ErrorBanner
                title="Failed to load player stats"
                message={playerStatsResponse.error.message}
              />
            ) : (
              <PlayerStatsTable data={playerStatsResponse.data} />
            )}
          </Card>
          <Card
            title="Accuracy by odds range"
            description="How well favorites vs longshots hit"
          >
            {!oddsAccuracyResponse.ok ? (
              <ErrorBanner
                title="Failed to load odds accuracy"
                message={oddsAccuracyResponse.error.message}
              />
            ) : (
              <OddsAccuracyTable data={oddsAccuracyResponse.data} />
            )}
          </Card>
          <Card
            title="Team matchup accuracy"
            description="Accuracy when picking against each team"
          >
            {!teamDefenseResponse.ok ? (
              <ErrorBanner
                title="Failed to load team defense"
                message={teamDefenseResponse.error.message}
              />
            ) : (
              <TeamDefenseTable data={teamDefenseResponse.data} />
            )}
          </Card>
        </div>
      ),
    },
    {
      id: "touchdowns",
      label: "Touchdowns",
      panel: (
        <Card
          title="Touchdowns"
          description="Toggle between all touchdowns or first TD of each game. Filter by week and team."
        >
          <AllTouchdownsTable season={season} initialData={allTouchdowns} />
        </Card>
      ),
    },
  ];

  return <Tabs tabs={tabs} defaultTab="overview" ariaLabel="Analytics sections" />;
}
