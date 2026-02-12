"use client";

import { useState, useEffect } from "react";
import { List, LayoutGrid } from "lucide-react";
import type { Game } from "@/lib/api";
import ScheduleGamesList from "./ScheduleGamesList";
import ScheduleGameCard from "./ScheduleGameCard";

const STORAGE_KEY = "fast6_schedule_view";

type ViewMode = "list" | "card";

interface ScheduleGamesSectionProps {
  games: Game[];
}

export default function ScheduleGamesSection({ games }: ScheduleGamesSectionProps) {
  const [viewMode, setViewMode] = useState<ViewMode>("list");

  useEffect(() => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY) as ViewMode | null;
      if (stored === "list" || stored === "card") setViewMode(stored);
    } catch {
      // Ignore localStorage errors
    }
  }, []);

  const handleToggle = (mode: ViewMode) => {
    setViewMode(mode);
    try {
      localStorage.setItem(STORAGE_KEY, mode);
    } catch {
      // Ignore
    }
  };

  if (games.length === 0) {
    return (
      <ScheduleGamesList games={[]} />
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <span className="text-xs font-mono text-[#78716c]">
          {games.length} game{games.length === 1 ? "" : "s"}
        </span>
        <div className="flex rounded-lg border-2 border-[#d1d5db] bg-white p-0.5">
          <button
            type="button"
            onClick={() => handleToggle("list")}
            className={`flex items-center gap-2 rounded-md px-3 py-1.5 text-sm font-mono font-bold transition-colors ${
              viewMode === "list"
                ? "bg-[#234058] text-[#F1EEE6]"
                : "text-[#78716c] hover:bg-[#f8fafc]"
            }`}
            aria-pressed={viewMode === "list"}
          >
            <List size={16} />
            List
          </button>
          <button
            type="button"
            onClick={() => handleToggle("card")}
            className={`flex items-center gap-2 rounded-md px-3 py-1.5 text-sm font-mono font-bold transition-colors ${
              viewMode === "card"
                ? "bg-[#234058] text-[#F1EEE6]"
                : "text-[#78716c] hover:bg-[#f8fafc]"
            }`}
            aria-pressed={viewMode === "card"}
          >
            <LayoutGrid size={16} />
            Card
          </button>
        </div>
      </div>

      {viewMode === "list" ? (
        <ScheduleGamesList games={games} />
      ) : (
        <div className="space-y-4">
          {games.map((game) => (
            <ScheduleGameCard key={game.id} game={game} />
          ))}
        </div>
      )}
    </div>
  );
}
