"use client";

import type { ReactNode } from "react";

interface TicketStubProps {
  children: ReactNode;
  /** Tear line position 0-100 (percent from left). Set to 0 to hide. Default 70. */
  tearLine?: number;
  /** Compact mode: smaller notches, no tear line. For small stat cards. */
  compact?: boolean;
}

export default function TicketStub({
  children,
  tearLine = 70,
  compact = false,
}: TicketStubProps) {
  const showTear = !compact && tearLine > 0 && tearLine < 100;

  return (
    <div className="relative group transition-transform duration-200 hover:-translate-y-0.5">
      {/* Offset shadow for paper depth */}
      <div
        className="absolute top-2 left-2 w-full h-full rounded-sm -z-10"
        style={{ backgroundColor: "rgba(35, 64, 88, 0.1)" }}
      />

      {/* Main stub */}
      <div className="relative overflow-hidden isolate rounded-sm border-2 border-[#8B7355] bg-[#F5F0E8] shadow-sm transition-shadow duration-200 group-hover:shadow-md">
        {/* Aged paper gradient */}
        <div
          className="absolute inset-0 opacity-100 pointer-events-none z-0"
          style={{
            background:
              "linear-gradient(180deg, rgba(255,251,245,0.4) 0%, transparent 30%, transparent 70%, rgba(139,115,85,0.03) 100%)",
          }}
        />

        {/* Paper texture - more visible */}
        <div
          className="absolute inset-0 opacity-[0.12] pointer-events-none z-0 mix-blend-multiply bg-repeat"
          style={{
            backgroundImage: `url("data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='stubSkin'%3E%3CfeTurbulence type='turbulence' baseFrequency='0.04' numOctaves='2' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23stubSkin)' opacity='1'/%3E%3C/svg%3E")`,
          }}
        />

        {/* Subtle top edge highlight */}
        <div
          className="absolute top-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-[#A2877D]/30 to-transparent z-10"
          aria-hidden
        />

        {/* Left notch */}
        <div
          className={`absolute top-1/2 -translate-y-1/2 -left-3 bg-[#F5F0E8] rounded-full z-20 ${
            compact ? "w-4 h-4" : "w-6 h-6"
          }`}
          style={{ border: "2px solid #8B7355", boxShadow: "inset 0 0 0 1px rgba(255,255,255,0.3)" }}
        />
        {/* Right notch */}
        <div
          className={`absolute top-1/2 -translate-y-1/2 -right-3 bg-[#F5F0E8] rounded-full z-20 ${
            compact ? "w-4 h-4" : "w-6 h-6"
          }`}
          style={{ border: "2px solid #8B7355", boxShadow: "inset 0 0 0 1px rgba(255,255,255,0.3)" }}
        />

        {/* Dashed tear line */}
        {showTear && (
          <div
            className="absolute top-0 bottom-0 w-0 border-l-2 border-dashed border-[#8B7355]/50 z-10 hidden sm:block"
            style={{ left: `${tearLine}%` }}
          />
        )}

        <div className="relative z-10">{children}</div>
      </div>
    </div>
  );
}
