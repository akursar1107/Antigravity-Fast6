import Link from "next/link";
import type { LeaderboardEntry } from "@/lib/api";

interface LeaderboardTableProps {
  data: LeaderboardEntry[];
}

export default function LeaderboardTable({ data }: LeaderboardTableProps) {
  if (data.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center gap-3 rounded-lg border-2 border-[#d1d5db] bg-[#F1EEE6] py-16 text-center">
        <div className="text-4xl">📊</div>
        <div>
          <p className="text-lg font-bold text-[#234058] font-mono">
            No data yet
          </p>
          <p className="mt-1 text-sm text-[#78716c] font-mono">
            Leaderboard will populate once picks are graded
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="overflow-x-auto rounded-lg border-2 border-[#d1d5db] bg-[#fff] shadow-sm">
      <table
        className="w-full text-left text-sm font-mono"
        aria-label="Season leaderboard standings"
      >
        <thead className="bg-[#f8fafc] border-b-2 border-[#d1d5db]">
          <tr>
            <th
              scope="col"
              className="px-4 py-3 font-bold uppercase tracking-[0.15em] text-[#64748b] text-[10px]"
            >
              #
            </th>
            <th
              scope="col"
              className="px-4 py-3 font-bold uppercase tracking-[0.15em] text-[#64748b] text-[10px]"
            >
              Agent
            </th>
            <th
              scope="col"
              className="px-4 py-3 text-right font-bold uppercase tracking-[0.15em] text-[#64748b] text-[10px]"
            >
              Pts
            </th>
            <th
              scope="col"
              className="px-4 py-3 text-right font-bold uppercase tracking-[0.15em] text-[#64748b] text-[10px]"
            >
              ROI
            </th>
            <th
              scope="col"
              className="px-4 py-3 text-right font-bold uppercase tracking-[0.15em] text-[#64748b] text-[10px]"
            >
              Rec
            </th>
          </tr>
        </thead>
        <tbody>
          {data.map((entry) => (
            <tr
              key={entry.user_id}
              className="border-b border-dashed border-[#e5e7eb] transition hover:bg-[#fff7ed]"
            >
              <td className="px-4 py-4">
                <div className="flex items-center gap-2">
                  {entry.rank === 1 && <span className="text-lg">🥇</span>}
                  {entry.rank === 2 && <span className="text-lg">🥈</span>}
                  {entry.rank === 3 && <span className="text-lg">🥉</span>}
                  <span className="font-bold text-[#A2877D]">
                    {String(entry.rank).padStart(2, "0")}
                  </span>
                </div>
              </td>
              <td className="px-4 py-4">
                <Link
                  href={`/users/${entry.user_id}`}
                  className="flex flex-col gap-0.5 hover:underline group"
                >
                  <span className="font-bold text-[#234058] group-hover:text-[#8C302C] transition">
                    {entry.user_name}
                  </span>
                  <span className="text-xs text-[#78716c]">
                    {entry.total_picks} picks · {entry.weeks_participated} weeks
                  </span>
                </Link>
              </td>
              <td className="px-4 py-4 text-right">
                <span className="font-bold text-[#234058]">
                  {entry.total_points}
                </span>
              </td>
              <td className="px-4 py-4 text-right">
                <span
                  className={`font-bold ${
                    entry.roi_dollars >= 0
                      ? "text-[#15803d]"
                      : "text-[#8C302C]"
                  }`}
                >
                  ${entry.roi_dollars.toFixed(1)}
                </span>
              </td>
              <td className="px-4 py-4 text-right">
                <span className="font-medium text-[#44403c]">
                  {entry.correct_picks}-{entry.total_picks - entry.correct_picks}
                </span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
