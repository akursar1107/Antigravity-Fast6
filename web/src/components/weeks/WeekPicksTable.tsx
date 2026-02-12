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
      <div className="text-center py-12 text-[#78716c] font-mono">
        <p className="text-lg">📋 No picks for this week yet</p>
      </div>
    );
  }

  return (
    <div className="overflow-x-auto rounded-lg border-2 border-[#d1d5db] bg-[#fff] shadow-sm">
      <table
        className="w-full text-left text-sm font-mono"
        aria-label="Week picks table"
      >
        <thead className="bg-[#f8fafc] border-b-2 border-[#d1d5db]">
          <tr>
            <th
              scope="col"
              className="px-4 py-3 font-bold uppercase tracking-[0.15em] text-[#64748b] text-[10px]"
            >
              User
            </th>
            <th
              scope="col"
              className="px-4 py-3 font-bold uppercase tracking-[0.15em] text-[#64748b] text-[10px]"
            >
              Team
            </th>
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
              Odds
            </th>
            <th
              scope="col"
              className="px-4 py-3 font-bold uppercase tracking-[0.15em] text-[#64748b] text-[10px]"
            >
              Status
            </th>
            <th
              scope="col"
              className="px-4 py-3 font-bold uppercase tracking-[0.15em] text-[#64748b] text-[10px]"
            >
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
                className="border-b border-dashed border-[#e5e7eb] hover:bg-[#fff7ed] transition-colors"
              >
                <td className="px-4 py-3 font-bold text-[#234058]">
                  {pick.user_name}
                </td>
                <td className="px-4 py-3 text-[#44403c]">{pick.team}</td>
                <td className="px-4 py-3 font-medium text-[#234058]">
                  {pick.player_name}
                </td>
                <td className="px-4 py-3 text-[#78716c]">
                  {formatOdds(pick.odds)}
                </td>
                <td className="px-4 py-3">
                  <span
                    className={`inline-block px-2 py-1 rounded-sm text-[10px] font-bold uppercase tracking-wider ${
                      status === "Correct"
                        ? "bg-[#15803d]/10 text-[#15803d] border border-[#15803d]/30"
                        : status === "Incorrect"
                          ? "bg-[#8C302C]/10 text-[#8C302C] border border-[#8C302C]/30"
                          : "bg-[#d1d5db]/30 text-[#78716c] border border-[#d1d5db]"
                    }`}
                  >
                    {status}
                  </span>
                </td>
                <td className="px-4 py-3 text-[#44403c]">
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
