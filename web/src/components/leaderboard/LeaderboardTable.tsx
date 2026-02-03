import type { LeaderboardEntry } from "@/lib/api";

interface LeaderboardTableProps {
  data: LeaderboardEntry[];
}

export default function LeaderboardTable({ data }: LeaderboardTableProps) {
  if (data.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center gap-3 rounded-2xl border border-slate-800 bg-slate-900/60 py-16 text-center">
        <div className="text-4xl">📊</div>
        <div>
          <p className="text-lg font-semibold text-slate-300">No data yet</p>
          <p className="mt-1 text-sm text-slate-500">
            Leaderboard will populate once picks are graded
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="overflow-x-auto rounded-2xl border border-slate-800 bg-slate-900/60">
      <table className="w-full text-left text-sm" aria-label="Season leaderboard standings">
        <thead className="border-b border-slate-800 bg-slate-900/80">
          <tr>
            <th scope="col" className="px-4 py-3 font-semibold uppercase tracking-[0.15em] text-slate-400">
              Rank
            </th>
            <th scope="col" className="px-4 py-3 font-semibold uppercase tracking-[0.15em] text-slate-400">
              User
            </th>
            <th scope="col" className="px-4 py-3 text-right font-semibold uppercase tracking-[0.15em] text-slate-400">
              Points
            </th>
            <th scope="col" className="px-4 py-3 text-right font-semibold uppercase tracking-[0.15em] text-slate-400">
              ROI
            </th>
            <th scope="col" className="px-4 py-3 text-right font-semibold uppercase tracking-[0.15em] text-slate-400">
              Win %
            </th>
            <th scope="col" className="px-4 py-3 text-right font-semibold uppercase tracking-[0.15em] text-slate-400">
              Recent Form
            </th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-800">
          {data.map((entry) => {
            return (
              <tr
                key={entry.user_id}
                className="transition hover:bg-slate-800/40"
              >
                <td className="px-4 py-4">
                  <div className="flex items-center gap-2">
                    {entry.rank === 1 && <span className="text-lg">🥇</span>}
                    {entry.rank === 2 && <span className="text-lg">🥈</span>}
                    {entry.rank === 3 && <span className="text-lg">🥉</span>}
                    <span className="font-semibold text-slate-200">
                      {entry.rank}
                    </span>
                  </div>
                </td>
                <td className="px-4 py-4">
                  <div className="flex flex-col gap-0.5">
                    <span className="font-medium text-slate-100">
                      {entry.user_name}
                    </span>
                    <span className="text-xs text-slate-500">
                      {entry.total_picks} picks · {entry.weeks_participated}{" "}
                      weeks
                    </span>
                  </div>
                </td>
                <td className="px-4 py-4 text-right">
                  <span className="font-semibold text-slate-200">
                    {entry.total_points}
                  </span>
                </td>
                <td className="px-4 py-4 text-right">
                  <span
                    className={`font-semibold ${
                      entry.roi_dollars >= 0
                        ? "text-green-400"
                        : "text-red-400"
                    }`}
                  >
                    ${entry.roi_dollars.toFixed(1)}
                  </span>
                </td>
                <td className="px-4 py-4 text-right">
                  <span className="font-medium text-slate-300">
                    {entry.win_percentage.toFixed(0)}%
                  </span>
                </td>
                <td className="px-4 py-4 text-right">
                  <span
                    className={`font-medium ${
                      entry.win_percentage >= 50 ? "text-emerald-400" : "text-slate-400"
                    }`}
                  >
                    {entry.win_percentage.toFixed(0)}%
                  </span>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
