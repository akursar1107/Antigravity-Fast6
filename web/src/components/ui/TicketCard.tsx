"use client";

import type { ReactNode } from "react";

interface TicketCardProps {
  children: ReactNode;
  active?: boolean;
  /** Tear line position 0–100 (percent from left). 0 = hidden. Default 70. Use 50 to split between away/home. */
  tearLine?: number;
  /** Smaller notches for tighter layouts (e.g. schedule list). */
  compact?: boolean;
  /** Accent color for border and left strip (e.g. #15803d for final, #8C302C for live). */
  accentColor?: string;
}

export default function TicketCard({
  children,
  active,
  tearLine = 70,
  compact = false,
  accentColor,
}: TicketCardProps) {
  const borderColor = accentColor ?? (active ? "#A2877D" : "#d1d5db");
  const showTear = tearLine > 0 && tearLine < 100;

  return (
    <div
      className={`relative group transition-all duration-300 ${active ? "scale-[1.01]" : "hover:-translate-y-1"}`}
    >
      {/* Shadow Layer */}
      <div className="absolute top-2 left-2 w-full h-full bg-[#234058]/10 rounded-lg -z-10" />

      {/* Main Card */}
      <div
        className="relative bg-[#F1EEE6] rounded-lg overflow-hidden border-y-2 border-l-2 border-r-2 isolate"
        style={{ borderColor }}
      >
        {/* Texture: CARD PIGSKIN - Smoother (0.06) */}
        <div
          className="absolute inset-0 opacity-[0.08] pointer-events-none z-0 mix-blend-multiply bg-repeat"
          style={{
            backgroundImage: `url("data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='cardSkin'%3E%3CfeTurbulence type='turbulence' baseFrequency='0.06' numOctaves='1' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23cardSkin)' opacity='1'/%3E%3C/svg%3E")`,
          }}
        />

        {/* Notches */}
        <div
          className={`absolute top-1/2 -translate-y-1/2 ${compact ? "-left-3 w-6 h-6" : "-left-4 w-8 h-8"} bg-[#F1EEE6] rounded-full z-20`}
          style={{ border: `2px solid ${borderColor}` }}
        />
        <div
          className={`absolute top-1/2 -translate-y-1/2 ${compact ? "-right-3 w-6 h-6" : "-right-4 w-8 h-8"} bg-[#F1EEE6] rounded-full z-20`}
          style={{ border: `2px solid ${borderColor}` }}
        />

        {/* Dashed Tear Line */}
        {showTear && (
          <div
            className="absolute top-0 bottom-0 w-0 border-l-2 border-dashed border-[#d1d5db] z-10 hidden md:block"
            style={{ left: `${tearLine}%` }}
          />
        )}

        {/* Colored left accent */}
        {accentColor && (
          <div
            className="absolute left-0 top-0 bottom-0 w-1.5 z-10"
            style={{ backgroundColor: accentColor }}
          />
        )}

        <div className="relative z-10">{children}</div>
      </div>
    </div>
  );
}
