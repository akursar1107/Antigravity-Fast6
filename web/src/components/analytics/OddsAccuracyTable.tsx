import type { OddsAccuracy } from "@/lib/api";

interface OddsAccuracyTableProps {
  data: OddsAccuracy[];
}

export default function OddsAccuracyTable({ data }: OddsAccuracyTableProps) {
  if (data.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center gap-3 rounded-lg border-2 border-[#d1d5db] bg-[#F1EEE6] py-16 text-center font-mono">
        <div className="text-4xl">📊</div>
        <div>
          <p className="text-lg font-bold text-[#234058]">No data yet</p>
          <p className="mt-1 text-sm text-[#78716c]">
            Odds accuracy will populate once picks with odds are graded
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="overflow-x-auto rounded-lg border-2 border-[#d1d5db] bg-[#fff] shadow-sm">
      <table
        className="w-full text-left text-sm font-mono"
        aria-label="Accuracy by odds range"
      >
        <thead className="bg-[#f8fafc] border-b-2 border-[#d1d5db]">
          <tr>
            <th
              scope="col"
              className="px-4 py-3 font-bold uppercase tracking-[0.15em] text-[#64748b] text-[10px]"
            >
              Odds range
            </th>
            <th
              scope="col"
              className="px-4 py-3 text-right font-bold uppercase tracking-[0.15em] text-[#64748b] text-[10px]"
            >
              Picks
            </th>
            <th
              scope="col"
              className="px-4 py-3 text-right font-bold uppercase tracking-[0.15em] text-[#64748b] text-[10px]"
            >
              Correct
            </th>
            <th
              scope="col"
              className="px-4 py-3 text-right font-bold uppercase tracking-[0.15em] text-[#64748b] text-[10px]"
            >
              Accuracy
            </th>
            <th
              scope="col"
              className="px-4 py-3 text-right font-bold uppercase tracking-[0.15em] text-[#64748b] text-[10px]"
            >
              Avg odds
            </th>
          </tr>
        </thead>
        <tbody>
          {data.map((row, index) => (
            <tr
              key={`${row.odds_range}-${index}`}
              className="border-b border-dashed border-[#e5e7eb] hover:bg-[#fff7ed] transition-colors"
            >
              <td className="px-4 py-4">
                <span className="font-bold text-[#234058]">{row.odds_range}</span>
              </td>
              <td className="px-4 py-4 text-right">
                <span className="text-[#44403c]">{row.picks_count}</span>
              </td>
              <td className="px-4 py-4 text-right">
                <span className="text-[#44403c]">{row.correct_count}</span>
              </td>
              <td className="px-4 py-4 text-right">
                <span
                  className={`font-bold ${
                    row.accuracy >= 50 ? "text-[#15803d]" : "text-[#78716c]"
                  }`}
                >
                  {row.accuracy.toFixed(0)}%
                </span>
              </td>
              <td className="px-4 py-4 text-right">
                <span className="text-[#44403c]">
                  {row.avg_odds >= 0 ? "+" : ""}{row.avg_odds}
                </span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
