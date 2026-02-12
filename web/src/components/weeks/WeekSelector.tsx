"use client";

import { useRouter } from "next/navigation";
import type { Week } from "@/lib/api";

type WeekSelectorProps = {
  weeks: Week[];
  currentWeekId: number;
  season: number;
};

export default function WeekSelector({
  weeks,
  currentWeekId,
  season,
}: WeekSelectorProps) {
  const router = useRouter();

  const handleChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const value = e.target.value;
    if (value) {
      router.push(`/weeks/${value}`);
    }
  };

  if (weeks.length === 0) {
    return null;
  }

  return (
    <label className="flex items-center gap-2">
      <span className="text-xs font-bold uppercase tracking-wider text-[#78716c] font-mono">
        View:
      </span>
      <select
        value={currentWeekId}
        onChange={handleChange}
        className="rounded border-2 border-[#1a3348] bg-[#234058] px-4 py-2.5 text-sm font-bold tracking-widest uppercase text-[#F1EEE6] font-mono shadow-md cursor-pointer hover:bg-[#1a3348] focus:border-[#A2877D] focus:outline-none focus:ring-2 focus:ring-[#A2877D]/50"
        aria-label="Select week to view"
      >
        {weeks.map((w) => (
          <option key={w.id} value={w.id}>
            Week {w.week}
          </option>
        ))}
      </select>
    </label>
  );
}
