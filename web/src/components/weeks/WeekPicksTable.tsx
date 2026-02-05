import type { WeekPick } from "@/lib/api";

interface WeekPicksTableProps {
  picks: WeekPick[];
}

function getStatusDisplay(graded: boolean, isCorrect: boolean | null): string {
  if (!graded) return "Pending";
  return isCorrect ? "Correct" : "Incorrect";
}

function formatOdds(odds: number): string {
  if (odds > 0) {
    return `+${odds}`;
  }
  return `${odds}`;
}

export default function WeekPicksTable({ picks }: WeekPicksTableProps) {
  if (picks.length === 0) {
    return (
      <div className="text-center py-12 text-slate-400">
        <p className="text-lg">📋 No picks for this week yet</p>
      </div>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table
        className="w-full text-left text-sm"
        aria-label="Week picks table"
      >
        <thead>
          <tr className="border-b border-slate-700">
            <th scope="col" className="px-4 py-3 font-semibold text-slate-300">
              User
            </th>
            <th scope="col" className="px-4 py-3 font-semibold text-slate-300">
              Team
            </th>
            <th scope="col" className="px-4 py-3 font-semibold text-slate-300">
              Player
            </th>
            <th scope="col" className="px-4 py-3 font-semibold text-slate-300">
              Odds
            </th>
            <th scope="col" className="px-4 py-3 font-semibold text-slate-300">
              Status
            </th>
            <th scope="col" className="px-4 py-3 font-semibold text-slate-300">
              Result
            </th>
          </tr>
        </thead>
        <tbody>
          {picks.map((pick) => {
            const status = getStatusDisplay(pick.graded, pick.is_correct);
            return (
              <tr
                key={pick.id}
                className="border-b border-slate-800 hover:bg-slate-800/30 transition-colors"
              >
                <td className="px-4 py-3 text-slate-200">{pick.user_name}</td>
                <td className="px-4 py-3 text-slate-300">{pick.team}</td>
                <td className="px-4 py-3 text-slate-200">{pick.player_name}</td>
                <td className="px-4 py-3 text-slate-400">
                  {formatOdds(pick.odds)}
                </td>
                <td className="px-4 py-3">
                  <span
                    className={`inline-block px-2 py-1 rounded text-xs font-medium ${
                      status === "Correct"
                        ? "bg-emerald-500/20 text-emerald-400"
                        : status === "Incorrect"
                          ? "bg-red-500/20 text-red-400"
                          : "bg-slate-700/50 text-slate-400"
                    }`}
                  >
                    {status}
                  </span>
                </td>
                <td className="px-4 py-3 text-slate-300">
                  {pick.actual_scorer || "-"}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
