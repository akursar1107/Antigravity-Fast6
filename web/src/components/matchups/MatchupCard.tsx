import type { MatchupResponse } from "@/lib/api";

interface MatchupCardProps {
  data: MatchupResponse;
}

export default function MatchupCard({ data }: MatchupCardProps) {
  if (!data.teams || data.teams.length < 2) {
    return (
      <div className="text-center py-12 text-[#78716c] font-mono">
        <p className="text-lg">🏈 No matchup data available</p>
      </div>
    );
  }

  const [homeTeam, awayTeam] = data.teams;
  const totalPicks = homeTeam.picks_count + awayTeam.picks_count;
  const hasNoPicks = totalPicks === 0;

  return (
    <div
      className="rounded-lg border-2 border-[#d1d5db] bg-[#fff] p-6 shadow-sm font-mono"
      aria-label="Matchup details card"
    >
      {data.status && (
        <p className="mb-2 text-center text-[10px] font-bold uppercase tracking-widest text-[#78716c]">
          Status: {data.status.replace("_", " ")}
        </p>
      )}
      {hasNoPicks && (
        <p className="mb-4 text-center text-sm text-[#78716c]">
          No picks submitted yet for this game.
        </p>
      )}
      {data.status === "final" && (
        <div className="mb-4 rounded-lg border border-[#d1d5db] bg-[#f8fafc] p-4">
          <h4 className="mb-2 text-[10px] font-bold uppercase tracking-widest text-[#78716c]">
            Touchdown scorers
          </h4>
          {data.td_scorers && data.td_scorers.length > 0 ? (
            <ul className="space-y-1 text-sm text-[#234058]">
              {data.td_scorers.map((s, i) => (
                <li
                  key={i}
                  className={`flex items-center gap-2 ${
                    s.is_first_td
                      ? "rounded-md border-2 border-[#15803d] bg-[#15803d]/10 px-2 py-1 font-semibold"
                      : ""
                  }`}
                >
                  {s.is_first_td && (
                    <span className="text-[10px] font-bold uppercase tracking-wider text-[#15803d]">
                      First TD
                    </span>
                  )}
                  <span className="font-medium">{s.player_name}</span>
                  {s.team && (
                    <span className="rounded bg-[#234058]/10 px-1.5 py-0.5 text-[10px] font-mono">
                      {s.team}
                    </span>
                  )}
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-sm text-[#78716c]">
              No touchdown data available for this game.
            </p>
          )}
        </div>
      )}
      <div className="grid grid-cols-1 gap-8 md:grid-cols-3">
        {/* Home Team */}
        <div className="space-y-4 rounded-lg border-2 border-[#d1d5db] bg-[#f8fafc] p-4">
          <h3 className="text-[10px] font-bold uppercase tracking-widest text-[#78716c]">
            Home
          </h3>
          <div className="text-2xl font-black text-[#234058]">{homeTeam.team}</div>
          <div className="space-y-2 pt-2">
            <div className="flex justify-between text-sm">
              <span className="text-[#78716c]">Picks:</span>
              <span className="font-bold text-[#234058]">
                {homeTeam.picks_count}
              </span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-[#78716c]">Correct:</span>
              <span className="font-bold text-[#15803d]">
                {homeTeam.correct_count}
              </span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-[#78716c]">Accuracy:</span>
              <span className="font-bold text-[#234058]">
                {homeTeam.accuracy.toFixed(0)}%
              </span>
            </div>
          </div>
        </div>

        {/* VS Badge */}
        <div className="flex items-center justify-center">
          <div className="rounded-sm border-2 border-[#A2877D] bg-[#A2877D]/10 px-4 py-2 text-center">
            <span className="font-black uppercase tracking-widest text-[#A2877D]">
              VS
            </span>
          </div>
        </div>

        {/* Away Team */}
        <div className="space-y-4 rounded-lg border-2 border-[#d1d5db] bg-[#f8fafc] p-4">
          <h3 className="text-[10px] font-bold uppercase tracking-widest text-[#78716c]">
            Away
          </h3>
          <div className="text-2xl font-black text-[#234058]">{awayTeam.team}</div>
          <div className="space-y-2 pt-2">
            <div className="flex justify-between text-sm">
              <span className="text-[#78716c]">Picks:</span>
              <span className="font-bold text-[#234058]">
                {awayTeam.picks_count}
              </span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-[#78716c]">Correct:</span>
              <span className="font-bold text-[#15803d]">
                {awayTeam.correct_count}
              </span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-[#78716c]">Accuracy:</span>
              <span className="font-bold text-[#234058]">
                {awayTeam.accuracy.toFixed(0)}%
              </span>
            </div>
          </div>
        </div>
      </div>

      {data.picks && data.picks.length > 0 && (
        <div className="mt-6 rounded-lg border border-[#d1d5db] bg-[#f8fafc] p-4">
          <h4 className="mb-3 text-[10px] font-bold uppercase tracking-widest text-[#78716c]">
            User picks
          </h4>
          <ul className="space-y-2">
            {data.picks.map((pick) => (
              <li
                key={pick.id}
                className="flex flex-wrap items-center justify-between gap-2 rounded-md border border-[#d1d5db] bg-white px-3 py-2 text-sm"
              >
                <div className="flex items-center gap-2">
                  <span className="font-bold text-[#234058]">{pick.user_name}</span>
                  <span className="text-[#78716c]">→</span>
                  <span className="font-medium">{pick.player_name}</span>
                  <span className="rounded bg-[#234058]/10 px-1.5 py-0.5 text-[10px] font-mono">
                    {pick.team}
                  </span>
                </div>
                <div className="flex items-center gap-3">
                  <span className="text-[10px] text-[#78716c]">+{pick.odds}</span>
                  {pick.is_correct === true && (
                    <span className="rounded bg-[#15803d]/20 px-1.5 py-0.5 text-[10px] font-bold text-[#15803d]">
                      ✓ Correct
                    </span>
                  )}
                  {pick.is_correct === false && (
                    <span className="rounded bg-[#dc2626]/20 px-1.5 py-0.5 text-[10px] text-[#dc2626]">
                      {pick.actual_scorer ? `Actual: ${pick.actual_scorer}` : "Miss"}
                    </span>
                  )}
                  {pick.is_correct === false && pick.any_time_td && (
                    <span className="text-[10px] text-[#78716c]">ATTD</span>
                  )}
                  {pick.is_correct === null && (
                    <span className="text-[10px] text-[#78716c]">Pending</span>
                  )}
                </div>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
