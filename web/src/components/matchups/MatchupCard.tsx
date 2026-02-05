import type { MatchupResponse } from "@/lib/api";

interface MatchupCardProps {
  data: MatchupResponse;
}

export default function MatchupCard({ data }: MatchupCardProps) {
  if (!data.teams || data.teams.length < 2) {
    return (
      <div className="text-center py-12 text-slate-400">
        <p className="text-lg">🏈 No matchup data available</p>
      </div>
    );
  }

  const [homeTeam, awayTeam] = data.teams;

  return (
    <div
      className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6"
      aria-label="Matchup details card"
    >
      <div className="grid grid-cols-1 gap-8 md:grid-cols-3">
        {/* Home Team */}
        <div className="space-y-4 rounded-lg border border-slate-800/50 bg-slate-800/20 p-4">
          <h3 className="text-sm font-semibold uppercase tracking-widest text-slate-400">
            Home
          </h3>
          <div className="text-3xl font-bold text-slate-100">{homeTeam.team}</div>
          <div className="space-y-2 pt-2">
            <div className="flex justify-between">
              <span className="text-slate-400">Picks:</span>
              <span className="font-semibold text-slate-200">
                {homeTeam.picks_count}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">Correct:</span>
              <span className="font-semibold text-emerald-400">
                {homeTeam.correct_count}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">Accuracy:</span>
              <span className="font-semibold text-slate-200">
                {(homeTeam.accuracy * 100).toFixed(0)}%
              </span>
            </div>
          </div>
        </div>

        {/* VS Badge */}
        <div className="flex items-center justify-center">
          <div className="rounded-full bg-indigo-500/20 px-4 py-2 text-center">
            <span className="font-bold uppercase tracking-widest text-indigo-400">
              VS
            </span>
          </div>
        </div>

        {/* Away Team */}
        <div className="space-y-4 rounded-lg border border-slate-800/50 bg-slate-800/20 p-4">
          <h3 className="text-sm font-semibold uppercase tracking-widest text-slate-400">
            Away
          </h3>
          <div className="text-3xl font-bold text-slate-100">{awayTeam.team}</div>
          <div className="space-y-2 pt-2">
            <div className="flex justify-between">
              <span className="text-slate-400">Picks:</span>
              <span className="font-semibold text-slate-200">
                {awayTeam.picks_count}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">Correct:</span>
              <span className="font-semibold text-emerald-400">
                {awayTeam.correct_count}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">Accuracy:</span>
              <span className="font-semibold text-slate-200">
                {(awayTeam.accuracy * 100).toFixed(0)}%
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
