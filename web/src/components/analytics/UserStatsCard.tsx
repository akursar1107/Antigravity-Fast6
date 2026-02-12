import type { UserStatsPerformance } from "@/lib/api";

interface UserStatsCardProps {
  data: UserStatsPerformance | null;
}

export default function UserStatsCard({ data }: UserStatsCardProps) {
  if (!data) {
    return (
      <div className="flex flex-col items-center justify-center gap-3 rounded-lg border-2 border-[#d1d5db] bg-[#F1EEE6] py-16 text-center font-mono">
        <div className="text-4xl">👤</div>
        <p className="text-lg font-bold text-[#234058]">No stats yet</p>
        <p className="text-sm text-[#5c5a57]">Make picks and get them graded to see your performance</p>
      </div>
    );
  }

  if (data.total_picks === 0) {
    return (
      <div className="flex flex-col items-center justify-center gap-3 rounded-lg border-2 border-[#d1d5db] bg-[#F1EEE6] py-16 text-center font-mono">
        <div className="text-4xl">👤</div>
        <p className="text-lg font-bold text-[#234058]">No picks this season</p>
        <p className="text-sm text-[#5c5a57]">Submit picks to track your performance</p>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4">
      <div className="rounded-lg border-2 border-[#d1d5db] bg-[#fff] p-4 shadow-sm">
        <p className="text-[10px] font-bold uppercase tracking-wider text-[#5c5a57] font-mono">
          Win rate
        </p>
        <p className="mt-1 text-2xl font-black text-[#234058] font-mono">
          {data.win_rate.toFixed(1)}%
        </p>
        <p className="mt-0.5 text-xs text-[#5c5a57] font-mono">
          {data.wins}W / {data.losses}L
        </p>
      </div>
      <div className="rounded-lg border-2 border-[#d1d5db] bg-[#fff] p-4 shadow-sm">
        <p className="text-[10px] font-bold uppercase tracking-wider text-[#5c5a57] font-mono">
          Brier score
        </p>
        <p className="mt-1 text-2xl font-black text-[#234058] font-mono">
          {data.brier_score.toFixed(3)}
        </p>
        <p className="mt-0.5 text-xs text-[#5c5a57] font-mono">
          Lower is better (0 = perfect)
        </p>
      </div>
      <div className="rounded-lg border-2 border-[#d1d5db] bg-[#fff] p-4 shadow-sm">
        <p className="text-[10px] font-bold uppercase tracking-wider text-[#5c5a57] font-mono">
          Total picks
        </p>
        <p className="mt-1 text-2xl font-black text-[#234058] font-mono">{data.total_picks}</p>
      </div>
      <div className="rounded-lg border-2 border-[#d1d5db] bg-[#fff] p-4 shadow-sm">
        <p className="text-[10px] font-bold uppercase tracking-wider text-[#5c5a57] font-mono">
          Streak
        </p>
        <p className="mt-1 text-2xl font-black text-[#234058] font-mono">
          {data.current_streak > 0 ? "+" : ""}
          {data.current_streak}
        </p>
        <p className="mt-0.5 text-xs text-[#5c5a57] font-mono">
          Best: {data.longest_win_streak} {data.is_hot && "🔥"}
        </p>
      </div>
    </div>
  );
}
