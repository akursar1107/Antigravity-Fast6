import type { PerformanceBreakdownRow } from "@/lib/api";

interface PerformanceBreakdownTableProps {
  data: PerformanceBreakdownRow[];
}

export default function PerformanceBreakdownTable({ data }: PerformanceBreakdownTableProps) {
  if (data.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center gap-3 rounded-lg border-2 border-[#d1d5db] bg-[#F1EEE6] py-16 text-center font-mono">
        <div className="text-4xl">📊</div>
        <div>
          <p className="text-lg font-bold text-[#234058]">No data yet</p>
          <p className="mt-1 text-sm text-[#5c5a57]">
            Add users and grade picks to see performance by picker
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="overflow-x-auto rounded-lg border-2 border-[#d1d5db] bg-[#fff] shadow-sm">
      <table
        className="w-full text-left text-sm font-mono"
        aria-label="Performance breakdown by picker"
      >
        <thead className="border-b-2 border-[#d1d5db] bg-[#f8fafc]">
          <tr>
            <th className="px-4 py-3 font-bold uppercase tracking-[0.15em] text-[#64748b] text-[10px]">
              Picker
            </th>
            <th className="px-4 py-3 font-bold uppercase tracking-[0.15em] text-[#64748b] text-[10px]">
              Picks
            </th>
            <th className="px-4 py-3 font-bold uppercase tracking-[0.15em] text-[#64748b] text-[10px]">
              W–L
            </th>
            <th className="px-4 py-3 font-bold uppercase tracking-[0.15em] text-[#64748b] text-[10px]">
              Win rate
            </th>
            <th className="px-4 py-3 font-bold uppercase tracking-[0.15em] text-[#64748b] text-[10px]">
              Brier
            </th>
            <th className="px-4 py-3 font-bold uppercase tracking-[0.15em] text-[#64748b] text-[10px]">
              Streak
            </th>
          </tr>
        </thead>
        <tbody>
          {data.map((row) => (
            <tr
              key={row.user_id}
              className="border-b border-dashed border-[#e5e7eb] transition-colors hover:bg-[#fff7ed]"
            >
              <td className="px-4 py-4 font-bold text-[#234058]">
                {row.user_name}
                {row.is_hot && " 🔥"}
              </td>
              <td className="px-4 py-4 font-mono text-[#44403c]">{row.total_picks}</td>
              <td className="px-4 py-4 font-mono text-[#44403c]">
                {row.wins}–{row.losses}
              </td>
              <td className="px-4 py-4 font-mono font-bold text-[#234058]">
                {row.win_rate.toFixed(1)}%
              </td>
              <td className="px-4 py-4 font-mono text-[#44403c]">
                {row.brier_score.toFixed(3)}
              </td>
              <td className="px-4 py-4 font-mono">
                <span
                  className={
                    row.current_streak > 0 ? "font-bold text-[#15803d]" : "text-[#5c5a57]"
                  }
                >
                  {row.current_streak > 0 ? "+" : ""}
                  {row.current_streak}
                </span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
