"use client";

import type { GradedPick } from "@/lib/api";

interface ReceiptPicksListProps {
  picks: GradedPick[];
  userName: string;
  season: number;
}

function formatTicketId(id: number): string {
  const s = String(id).padStart(6, "0");
  return `${s.slice(0, 2)}-${s.slice(2, 4)}-${s.slice(4)}`;
}

function BetslipTicket({
  picks,
  type,
  userName,
  season,
}: {
  picks: GradedPick[];
  type: "wins" | "losses";
  userName: string;
  season: number;
}) {
  const isWin = type === "wins";
  const header = isWin ? "WINNING TICKETS" : "LOSING TICKETS";

  if (picks.length === 0) {
    return (
      <div className="flex min-h-[200px] flex-col bg-white px-4 py-6 shadow-[2px_4px_12px_rgba(0,0,0,0.08)]">
        <p className="text-center text-[10px] font-bold uppercase tracking-widest text-[#9ca3af]">
          {header}
        </p>
        <p className="mt-4 flex-1 text-center text-xs text-[#9ca3af]">
          No {type} yet
        </p>
        <BarcodeStrip />
      </div>
    );
  }

  return (
    <div className="relative flex flex-col bg-white shadow-[2px_4px_12px_rgba(0,0,0,0.08)]">
      {/* Perforated right edge */}
      <div
        className="absolute top-0 right-0 h-full w-3"
        style={{
          background: `repeating-linear-gradient(
            90deg,
            transparent 0,
            transparent 1px,
            #e5e7eb 1px,
            #e5e7eb 2px
          )`,
        }}
      />

      <div className="border-b border-dashed border-[#e5e7eb] px-4 py-3">
        <p className="text-[10px] font-bold uppercase tracking-[0.25em] text-[#374151]">
          Fast6 ticket office
        </p>
        <p className="mt-0.5 text-[9px] font-medium uppercase tracking-wider text-[#6b7280]">
          {header}
        </p>
        <p className="mt-0.5 text-[9px] text-[#9ca3af]">
          {userName} · Season {season} · {picks.length} {type}
        </p>
      </div>

      <div className="flex-1">
        {picks.map((pick) => (
          <div
            key={pick.pick_id}
            className="border-b border-dashed border-[#e5e7eb] px-4 py-3 last:border-0 font-mono text-[11px] text-[#111827]"
          >
            <p className="text-[9px] text-[#9ca3af]">
              #{formatTicketId(pick.pick_id)}
            </p>
            <p className="mt-1 font-bold">
              First TD · {pick.player_name}
            </p>
            <p className="mt-0.5 text-[10px] text-[#6b7280]">
              {pick.team} · W{pick.week} · {pick.odds != null ? `+${pick.odds}` : "—"}
            </p>
            <p className="mt-1.5 text-[10px] text-[#6b7280]">
              Ticket Cost $1.00
            </p>
            <p
              className={`mt-1.5 font-bold ${
                isWin ? "text-[#15803d]" : "text-[#dc2626]"
              }`}
            >
              {isWin
                ? `Win $${pick.roi.toFixed(2)} to pay $${(pick.roi + 1).toFixed(2)}`
                : `Ticket Lost $${Math.abs(pick.roi).toFixed(2)}`}
            </p>
          </div>
        ))}
      </div>

      <BarcodeStrip />
    </div>
  );
}

function BarcodeStrip() {
  return (
    <div className="mt-auto border-t border-dashed border-[#e5e7eb] px-4 py-2">
      <div className="flex gap-0.5">
        {[...Array(24)].map((_, i) => (
          <div
            key={i}
            className="h-4 w-px bg-[#111827]"
            style={{ opacity: 0.3 + (i % 3) * 0.2 }}
          />
        ))}
      </div>
    </div>
  );
}

export default function ReceiptPicksList({
  picks,
  userName,
  season,
}: ReceiptPicksListProps) {
  if (picks.length === 0) {
    return (
      <div className="rounded border border-dashed border-[#e5e7eb] bg-[#f9fafb] px-4 py-8 text-center font-mono text-sm text-[#9ca3af]">
        No graded picks yet for this season
      </div>
    );
  }

  const wins = picks.filter((p) => p.is_correct);
  const losses = picks.filter((p) => !p.is_correct);

  return (
    <div className="grid gap-6 sm:grid-cols-2">
      <BetslipTicket
        picks={wins}
        type="wins"
        userName={userName}
        season={season}
      />
      <BetslipTicket
        picks={losses}
        type="losses"
        userName={userName}
        season={season}
      />
    </div>
  );
}
