"use client";

import type { ReactNode } from "react";

interface ChartCardProps {
  title: string;
  subtitle?: string;
  children: ReactNode;
}

export default function ChartCard({ title, subtitle, children }: ChartCardProps) {
  return (
    <div className="relative bg-[#fff] border-2 border-[#d1d5db] p-6 shadow-sm">
      {/* Paper holes decoration */}
      <div className="absolute top-0 left-0 w-full h-4 flex justify-between px-2 -mt-2">
        {[...Array(6)].map((_, i) => (
          <div key={i} className="w-3 h-3 bg-[#F1EEE6] rounded-full" />
        ))}
      </div>
      <div className="mt-2 mb-4">
        <h3 className="text-sm font-black tracking-widest uppercase text-[#234058] font-mono">
          {title}
        </h3>
        {subtitle ? (
          <p className="mt-1 text-xs text-[#78716c] font-mono">{subtitle}</p>
        ) : null}
      </div>
      <div className="text-[#234058] font-mono">{children}</div>
    </div>
  );
}
