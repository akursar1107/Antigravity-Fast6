import type { PlayerStat } from "@/lib/api";

interface PlayerStatsTableProps {
  data: PlayerStat[];
}

export default function PlayerStatsTable({ data }: PlayerStatsTableProps) {
  if (data.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center gap-3 rounded-2xl border border-slate-800 bg-slate-900/60 py-16 text-center">
        <div className="text-4xl">👤</div>
        <div>
          <p className="text-lg font-semibold text-slate-300">No data yet</p>
          <p className="mt-1 text-sm text-slate-500">
            Player stats will populate once picks are graded
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="overflow-x-auto rounded-2xl border border-slate-800 bg-slate-900/60">
      <table className="w-full text-left text-sm" aria-label="Player performance statistics">
        <thead className="border-b border-slate-800 bg-slate-900/80">
          <tr>
            <th scope="col" className="px-4 py-3 font-semibold uppercase tracking-[0.15em] text-slate-400">
              Player
            </th>
            <th scope="col" className="px-4 py-3 font-semibold uppercase tracking-[0.15em] text-slate-400">
              Team
            </th>
            <th scope="col" className="px-4 py-3 text-right font-semibold uppercase tracking-[0.15em] text-slate-400">
              First TD
            </th>
            <th scope="col" className="px-4 py-3 text-right font-semibold uppercase tracking-[0.15em] text-slate-400">
              Any-Time TD
            </th>
            <th scope="col" className="px-4 py-3 text-right font-semibold uppercase tracking-[0.15em] text-slate-400">
              Accuracy
            </th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-800">
          {data.map((player, index) => {
            return (
              <tr
                key={`${player.player_name}-${player.team}-${index}`}
                className="transition hover:bg-slate-800/40"
              >
                <td className="px-4 py-4">
                  <span className="font-medium text-slate-100">
                    {player.player_name}
                  </span>
                </td>
                <td className="px-4 py-4">
                  <span className="text-slate-300">{player.team}</span>
                </td>
                <td className="px-4 py-4 text-right">
                  <span className="font-semibold text-slate-200">
                    {player.first_td_count}
                  </span>
                </td>
                <td className="px-4 py-4 text-right">
                  <span className="font-medium text-slate-300">
                    {(player.any_time_td_rate * 100).toFixed(0)}%
                  </span>
                </td>
                <td className="px-4 py-4 text-right">
                  <span
                    className={`font-medium ${
                      player.accuracy >= 50 ? "text-emerald-400" : "text-slate-400"
                    }`}
                  >
                    {player.accuracy.toFixed(0)}%
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
