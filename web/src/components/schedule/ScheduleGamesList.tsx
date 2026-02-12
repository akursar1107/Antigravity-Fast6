import Link from "next/link";
import TicketStub from "@/components/ui/TicketStub";
import TeamLogo from "@/components/ui/TeamLogo";
import type { Game } from "@/lib/api";

interface ScheduleGamesListProps {
  games: Game[];
}

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

function getWinner(game: Game): "away" | "home" | null {
  if (game.status?.toLowerCase() !== "final") return null;
  const away = game.away_score;
  const home = game.home_score;
  if (away == null || home == null) return null;
  if (away > home) return "away";
  if (home > away) return "home";
  return null;
}

export default function ScheduleGamesList({ games }: ScheduleGamesListProps) {
  if (games.length === 0) {
    return (
      <TicketStub compact>
        <div className="p-12 text-center font-mono">
          <p className="text-[#78716c]">No games scheduled for this week.</p>
        </div>
      </TicketStub>
    );
  }

  return (
    <div className="space-y-3">
      {games.map((game) => {
        const statusNorm = game.status?.toLowerCase() ?? "scheduled";
        return (
          <Link key={game.id} href={`/matchups/${game.id}`} className="block">
            <TicketStub compact>
              <div className="p-4 font-mono">
                <div className="flex flex-wrap items-center justify-between gap-4">
                  <div className="flex items-center gap-4">
                    <TeamLogo team={game.away_team} size="sm" />
                    <span
                      className={`text-lg font-black ${
                        getWinner(game) === "away"
                          ? "text-[#15803d]"
                          : "text-[#234058]"
                      }`}
                    >
                      {game.away_team}
                    </span>
                    {getWinner(game) === "away" && (
                      <span className="rounded bg-[#15803d]/20 px-1.5 py-0.5 text-[10px] font-bold text-[#15803d]">
                        W
                      </span>
                    )}
                    <span className="text-[9px] font-bold uppercase tracking-widest text-[#A2877D]">
                      @
                    </span>
                    <TeamLogo team={game.home_team} size="sm" />
                    <span
                      className={`text-lg font-black ${
                        getWinner(game) === "home"
                          ? "text-[#15803d]"
                          : "text-[#234058]"
                      }`}
                    >
                      {game.home_team}
                    </span>
                    {getWinner(game) === "home" && (
                      <span className="rounded bg-[#15803d]/20 px-1.5 py-0.5 text-[10px] font-bold text-[#15803d]">
                        W
                      </span>
                    )}
                  </div>
                  <div className="flex items-center gap-4">
                    <span className="text-xs text-[#78716c]">
                      {formatGameDate(game.game_date)}
                    </span>
                    <span
                      className={`rounded px-2 py-1 text-[10px] font-bold tracking-wider ${
                        statusNorm === "final"
                          ? "bg-[#15803d]/20 text-[#15803d]"
                          : statusNorm === "in_progress"
                            ? "bg-[#8C302C]/20 text-[#8C302C]"
                            : "bg-[#234058]/10 text-[#234058]"
                      }`}
                    >
                      {formatStatus(game.status)}
                    </span>
                    {(game.home_score !== null || game.away_score !== null) && (
                      <span className="text-sm font-bold text-[#234058]">
                        {game.away_score ?? 0}–{game.home_score ?? 0}
                      </span>
                    )}
                  </div>
                </div>
              </div>
            </TicketStub>
          </Link>
        );
      })}
    </div>
  );
}
