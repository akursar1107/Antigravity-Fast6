"use client";

import Link from "next/link";
import TeamLogo from "@/components/ui/TeamLogo";
import type { Game } from "@/lib/api";

// Minimal stadium lookup for display (optional enhancement)
const STADIUM_MAP: Record<string, string> = {
  KC: "GEHA Field at Arrowhead Stadium",
  BAL: "M&T Bank Stadium",
  SF: "Levi's Stadium",
  BUF: "Highmark Stadium",
  PHI: "Lincoln Financial Field",
  DAL: "AT&T Stadium",
  MIA: "Hard Rock Stadium",
  // Add more as needed
};

function formatGameDate(dateStr: string): string {
  try {
    const hasTime = /[T\s]/.test(dateStr);
    const d = new Date(dateStr);
    return hasTime
      ? d.toLocaleDateString("en-US", {
          weekday: "short",
          month: "short",
          day: "numeric",
          hour: "numeric",
          minute: "2-digit",
        })
      : d.toLocaleDateString("en-US", {
          weekday: "short",
          month: "short",
          day: "numeric",
        });
  } catch {
    return dateStr;
  }
}

function formatStatus(status: string): string {
  const s = status?.toLowerCase() ?? "";
  if (s === "final") return "Final";
  if (s === "in_progress") return "In Progress";
  return "Scheduled";
}

interface ScheduleGameCardProps {
  game: Game;
}

function getWinner(game: Game): "away" | "home" | null {
  if (game.status?.toLowerCase() !== "final") return null;
  const away = game.away_score;
  const home = game.home_score;
  if (away == null || home == null) return null;
  if (away > home) return "away";
  if (home > away) return "home";
  return null;
}

export default function ScheduleGameCard({ game }: ScheduleGameCardProps) {
  const statusNorm = game.status?.toLowerCase() ?? "scheduled";
  const isLive = statusNorm === "in_progress";
  const isFinal = statusNorm === "final";
  const homeStadium = STADIUM_MAP[game.home_team] ?? null;
  const winner = getWinner(game);

  return (
    <Link href={`/matchups/${game.id}`} className="block">
      <div className="relative overflow-hidden rounded-xl border-2 border-[#1a3348] bg-[#234058] p-6 shadow-lg transition-all hover:border-[#8C302C]/60 hover:shadow-xl">
        {/* Live indicator */}
        {isLive && (
          <div className="mb-4 flex items-center gap-2">
            <span className="h-2 w-2 animate-pulse rounded-full bg-[#8C302C]" />
            <span className="text-xs font-bold uppercase tracking-widest text-[#8C302C]">
              Live action
            </span>
          </div>
        )}

        {/* Venue / date row */}
        <div className="mb-4 flex flex-wrap items-center justify-between gap-2 text-[#8faec7]">
          {homeStadium ? (
            <p className="text-xs font-mono">
              {homeStadium}
            </p>
          ) : (
            <p className="text-xs font-mono">
              {formatGameDate(game.game_date)}
            </p>
          )}
          <span
            className={`rounded px-2 py-1 text-[10px] font-bold tracking-wider ${
              isFinal
                ? "bg-[#15803d]/30 text-[#51CF66]"
                : isLive
                  ? "bg-[#8C302C]/30 text-[#8C302C]"
                  : "bg-[#8faec7]/20 text-[#8faec7]"
            }`}
          >
            {formatStatus(game.status)}
          </span>
        </div>

        {/* Teams and score */}
        <div className="mb-4 flex items-center justify-between gap-4">
          <div
            className={`flex flex-col items-center gap-2 rounded-lg p-2 transition-colors ${
              winner === "away" ? "ring-2 ring-[#51CF66] bg-[#15803d]/20" : ""
            }`}
          >
            <div className="relative">
              <TeamLogo team={game.away_team} size="lg" />
              {winner === "away" && (
                <span className="absolute -right-1 -top-1 rounded-full bg-[#15803d] px-1.5 py-0.5 text-[10px] font-bold text-white">
                  W
                </span>
              )}
            </div>
            <p className="text-xs font-bold uppercase tracking-widest text-[#8faec7]">
              Away
            </p>
            <p className="text-2xl font-black text-[#F1EEE6]">
              {game.away_team}
            </p>
          </div>
          <div className="flex flex-col items-center">
            <p className="text-3xl font-black text-[#F1EEE6] tabular-nums">
              {(game.away_score ?? game.home_score) !== null
                ? `${game.away_score ?? 0}–${game.home_score ?? 0}`
                : "–"}
            </p>
            <p className="mt-1 text-[10px] font-bold uppercase tracking-widest text-[#8faec7]">
              {isFinal ? "Final" : statusNorm === "in_progress" ? "Live" : "Score"}
            </p>
          </div>
          <div
            className={`flex flex-col items-center gap-2 rounded-lg p-2 transition-colors ${
              winner === "home" ? "ring-2 ring-[#51CF66] bg-[#15803d]/20" : ""
            }`}
          >
            <div className="relative">
              <TeamLogo team={game.home_team} size="lg" />
              {winner === "home" && (
                <span className="absolute -right-1 -top-1 rounded-full bg-[#15803d] px-1.5 py-0.5 text-[10px] font-bold text-white">
                  W
                </span>
              )}
            </div>
            <p className="text-xs font-bold uppercase tracking-widest text-[#8faec7]">
              Home
            </p>
            <p className="text-2xl font-black text-[#F1EEE6]">
              {game.home_team}
            </p>
          </div>
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between border-t border-[#1a3348] pt-4">
          <p className="text-[10px] font-mono text-[#8faec7]">
            {formatGameDate(game.game_date)}
          </p>
          <p className="text-[10px] font-mono text-[#8faec7]">
            {game.away_team} @ {game.home_team}
          </p>
        </div>
      </div>
    </Link>
  );
}
