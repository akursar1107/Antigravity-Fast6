"use client";

import type { ReactNode } from "react";

interface StatCardProps {
  label: string;
  value: string | number;
  helper?: string;
  icon?: ReactNode;
}

export default function StatCard({ label, value, helper, icon }: StatCardProps) {
  return (
    <div className="relative bg-[#F1EEE6] rounded-lg overflow-hidden border-y-2 border-l-2 border-r-2 border-[#d1d5db] shadow-sm group hover:-translate-y-0.5 transition-transform duration-300">
      {/* Pigskin texture */}
      <div
        className="absolute inset-0 opacity-[0.08] pointer-events-none z-0 mix-blend-multiply bg-repeat"
        style={{
          backgroundImage: `url("data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='cardSkin'%3E%3CfeTurbulence type='turbulence' baseFrequency='0.06' numOctaves='1' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23cardSkin)' opacity='1'/%3E%3C/svg%3E")`,
        }}
      />
      <div className="relative z-10 p-5">
        <div className="flex items-center justify-between">
          <p className="text-[10px] font-bold uppercase tracking-[0.2em] text-[#78716c] font-mono">
            {label}
          </p>
          {icon ? <span className="text-[#8faec7]">{icon}</span> : null}
        </div>
        <div className="mt-4 text-3xl font-black text-[#234058] font-mono tracking-tight">
          {value}
        </div>
        {helper ? (
          <p className="mt-2 text-sm text-[#78716c] font-mono">{helper}</p>
        ) : null}
      </div>
    </div>
  );
}
