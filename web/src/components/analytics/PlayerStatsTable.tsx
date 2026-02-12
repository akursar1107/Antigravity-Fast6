import type { PlayerStat } from "@/lib/api";

interface PlayerStatsTableProps {
  data: PlayerStat[];
}

export default function PlayerStatsTable({ data }: PlayerStatsTableProps) {
  if (data.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center gap-3 rounded-lg border-2 border-[#d1d5db] bg-[#F1EEE6] py-16 text-center font-mono">
        <div className="text-4xl">👤</div>
        <div>
          <p className="text-lg font-bold text-[#234058]">No data yet</p>
          <p className="mt-1 text-sm text-[#78716c]">
            Player stats will populate once picks are graded
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="overflow-x-auto rounded-lg border-2 border-[#d1d5db] bg-[#fff] shadow-sm">
      <table
        className="w-full text-left text-sm font-mono"
        aria-label="Player performance statistics"
      >
        <thead className="bg-[#f8fafc] border-b-2 border-[#d1d5db]">
          <tr>
            <th
              scope="col"
              className="px-4 py-3 font-bold uppercase tracking-[0.15em] text-[#64748b] text-[10px]"
            >
              Player
            </th>
            <th
              scope="col"
              className="px-4 py-3 font-bold uppercase tracking-[0.15em] text-[#64748b] text-[10px]"
            >
              Team
            </th>
            <th
              scope="col"
              className="px-4 py-3 text-right font-bold uppercase tracking-[0.15em] text-[#64748b] text-[10px]"
            >
              First TD
            </th>
            <th
              scope="col"
              className="px-4 py-3 text-right font-bold uppercase tracking-[0.15em] text-[#64748b] text-[10px]"
            >
              Any-Time TD
            </th>
            <th
              scope="col"
              className="px-4 py-3 text-right font-bold uppercase tracking-[0.15em] text-[#64748b] text-[10px]"
            >
              Accuracy
            </th>
          </tr>
        </thead>
        <tbody>
          {data.map((player, index) => (
            <tr
              key={`${player.player_name}-${player.team}-${index}`}
              className="border-b border-dashed border-[#e5e7eb] hover:bg-[#fff7ed] transition-colors"
            >
              <td className="px-4 py-4">
                <span className="font-bold text-[#234058]">
                  {player.player_name}
                </span>
              </td>
              <td className="px-4 py-4">
                <span className="text-[#44403c]">{player.team}</span>
              </td>
              <td className="px-4 py-4 text-right">
                <span className="font-bold text-[#234058]">
                  {player.first_td_count}
                </span>
              </td>
              <td className="px-4 py-4 text-right">
                <span className="font-medium text-[#44403c]">
                  {(player.any_time_td_rate * 100).toFixed(0)}%
                </span>
              </td>
              <td className="px-4 py-4 text-right">
                <span
                  className={`font-bold ${
                    player.accuracy >= 50 ? "text-[#15803d]" : "text-[#78716c]"
                  }`}
                >
                  {player.accuracy.toFixed(0)}%
                </span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
