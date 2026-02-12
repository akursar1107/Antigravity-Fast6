"use client";

import { useState, useEffect, useCallback } from "react";
import { X, ChevronRight, Plus } from "lucide-react";
import type {
  User,
  Week,
  Game,
  Pick,
  RosterPlayer,
  AdminPickCreate,
} from "@/lib/api";
import {
  getUsersServer,
  getWeeksServer,
  getGamesServer,
  getRosterPlayers,
  createAdminPick,
} from "@/lib/api";

const CURRENT_SEASON = parseInt(
  process.env.NEXT_PUBLIC_CURRENT_SEASON ?? "2025",
  10
);

type AdminAddPickWorkflowProps = {
  onClose: () => void;
  onSuccess: (pick: Pick) => void;
  token: string;
};

const STEPS = [
  "User",
  "Week",
  "Game",
  "Team",
  "Player",
  "Odds",
] as const;

export default function AdminAddPickWorkflow({
  onClose,
  onSuccess,
  token,
}: AdminAddPickWorkflowProps) {
  const [step, setStep] = useState(0);
  const [users, setUsers] = useState<User[]>([]);
  const [weeks, setWeeks] = useState<Week[]>([]);
  const [games, setGames] = useState<Game[]>([]);
  const [players, setPlayers] = useState<RosterPlayer[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [selectedUserId, setSelectedUserId] = useState<number | null>(null);
  const [selectedWeek, setSelectedWeek] = useState<Week | null>(null);
  const [selectedGame, setSelectedGame] = useState<Game | null>(null);
  const [selectedTeam, setSelectedTeam] = useState<string | null>(null);
  const [selectedPlayer, setSelectedPlayer] = useState<string | null>(null);
  const [oddsInput, setOddsInput] = useState("");

  const fetchUsers = useCallback(async () => {
    const res = await getUsersServer(token);
    if (res.ok) setUsers(res.data);
  }, [token]);

  const fetchWeeks = useCallback(async () => {
    const res = await getWeeksServer(CURRENT_SEASON, token);
    if (res.ok) {
      // Deduplicate by (season, week) — keep first occurrence
      const seen = new Set<string>();
      const deduped = res.data.filter((w) => {
        const key = `${w.season}-${w.week}`;
        if (seen.has(key)) return false;
        seen.add(key);
        return true;
      });
      setWeeks(deduped.sort((a, b) => a.week - b.week));
    }
  }, [token]);

  const fetchGames = useCallback(async () => {
    if (!selectedWeek) return;
    const res = await getGamesServer(
      selectedWeek.season,
      token,
      selectedWeek.week
    );
    if (res.ok) setGames(res.data);
  }, [selectedWeek, token]);

  const fetchPlayers = useCallback(async () => {
    if (!selectedTeam || !selectedWeek) return;
    const res = await getRosterPlayers(
      selectedTeam,
      selectedWeek.season,
      token
    );
    if (res.ok) setPlayers(res.data);
  }, [selectedTeam, selectedWeek, token]);

  useEffect(() => {
    fetchUsers();
  }, [fetchUsers]);

  useEffect(() => {
    fetchWeeks();
  }, [fetchWeeks]);

  useEffect(() => {
    if (selectedWeek) fetchGames();
    else setGames([]);
  }, [selectedWeek, fetchGames]);

  useEffect(() => {
    if (selectedTeam && selectedWeek) fetchPlayers();
    else setPlayers([]);
  }, [selectedTeam, selectedWeek, fetchPlayers]);

  const canProceed = () => {
    switch (step) {
      case 0:
        return selectedUserId != null;
      case 1:
        return selectedWeek != null;
      case 2:
        return selectedGame != null;
      case 3:
        return selectedTeam != null;
      case 4:
        return selectedPlayer != null;
      case 5:
        return true;
      default:
        return false;
    }
  };

  const handleNext = () => {
    if (step < STEPS.length - 1 && canProceed()) {
      setStep(step + 1);
      setError(null);
    }
  };

  const handleBack = () => {
    if (step > 0) {
      setStep(step - 1);
      setError(null);
    }
  };

  const handleSubmit = async () => {
    if (
      !selectedUserId ||
      !selectedWeek ||
      !selectedGame ||
      !selectedTeam ||
      !selectedPlayer
    ) {
      setError("Please complete all steps.");
      return;
    }

    const odds =
      oddsInput.trim() === ""
        ? null
        : parseFloat(oddsInput.replace(/^\+/, ""));

    setLoading(true);
    setError(null);

    const pick: AdminPickCreate = {
      user_id: selectedUserId,
      week_id: selectedWeek.id,
      team: selectedTeam,
      player_name: selectedPlayer,
      odds,
      game_id: selectedGame.id,
    };

    const res = await createAdminPick(pick, token);

    setLoading(false);

    if (res.ok) {
      onSuccess(res.data);
      onClose();
    } else {
      setError(res.error?.message ?? "Failed to create pick.");
    }
  };

  const stepLabel = STEPS[step];

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="bg-[#F1EEE6] w-full max-w-lg rounded-lg shadow-2xl border-2 border-[#234058] overflow-hidden relative">
        <div className="bg-[#234058] p-4 flex justify-between items-center border-b-2 border-[#1a3348]">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 bg-[#8C302C] rounded flex items-center justify-center text-[#F1EEE6]">
              <Plus size={16} />
            </div>
            <div>
              <h3 className="text-[#F1EEE6] font-black uppercase tracking-widest font-mono text-sm">
                Add Pick
              </h3>
              <p className="text-[#8faec7] text-[10px] font-mono">
                Step {step + 1} of {STEPS.length}: {stepLabel}
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-[#8faec7] hover:text-[#F1EEE6] transition-colors"
          >
            <X size={20} />
          </button>
        </div>

        <div className="p-6 space-y-4 max-h-[60vh] overflow-y-auto">
          {error && (
            <div className="rounded bg-red-100 text-red-800 px-3 py-2 text-sm font-mono">
              {error}
            </div>
          )}

          {step === 0 && (
            <div>
              <label className="block text-xs font-black uppercase tracking-widest text-[#78716c] mb-2 font-mono">
                Select User
              </label>
              <select
                value={selectedUserId ?? ""}
                onChange={(e) =>
                  setSelectedUserId(e.target.value ? parseInt(e.target.value, 10) : null)
                }
                className="w-full rounded border-2 border-[#d1d5db] bg-white px-3 py-2 text-sm font-mono text-[#234058] focus:border-[#234058] focus:outline-none focus:ring-1 focus:ring-[#234058]"
              >
                <option value="">Choose user...</option>
                {users.map((u) => (
                  <option key={u.id} value={u.id}>
                    {u.name}
                  </option>
                ))}
              </select>
            </div>
          )}

          {step === 1 && (
            <div>
              <label className="block text-xs font-black uppercase tracking-widest text-[#78716c] mb-2 font-mono">
                Select Week
              </label>
              <select
                value={selectedWeek?.id ?? ""}
                onChange={(e) => {
                  const id = e.target.value ? parseInt(e.target.value, 10) : null;
                  setSelectedWeek(id ? weeks.find((w) => w.id === id) ?? null : null);
                }}
                className="w-full rounded border-2 border-[#d1d5db] bg-white px-3 py-2 text-sm font-mono text-[#234058] focus:border-[#234058] focus:outline-none focus:ring-1 focus:ring-[#234058]"
              >
                <option value="">Choose week...</option>
                {weeks.map((w) => (
                  <option key={w.id} value={w.id}>
                    Week {w.week} · {w.season}
                  </option>
                ))}
              </select>
            </div>
          )}

          {step === 2 && (
            <div>
              <label className="block text-xs font-black uppercase tracking-widest text-[#78716c] mb-2 font-mono">
                Select Game (primetime)
              </label>
              <select
                value={selectedGame?.id ?? ""}
                onChange={(e) => {
                  const id = e.target.value;
                  setSelectedGame(id ? games.find((g) => g.id === id) ?? null : null);
                }}
                className="w-full rounded border-2 border-[#d1d5db] bg-white px-3 py-2 text-sm font-mono text-[#234058] focus:border-[#234058] focus:outline-none focus:ring-1 focus:ring-[#234058]"
              >
                <option value="">Choose game...</option>
                {games.map((g) => (
                  <option key={g.id} value={g.id}>
                    {g.away_team} @ {g.home_team} · {g.game_date}
                  </option>
                ))}
              </select>
              {games.length === 0 && selectedWeek && (
                <p className="mt-2 text-xs text-[#78716c] font-mono">
                  No games for this week. Sync games first.
                </p>
              )}
            </div>
          )}

          {step === 3 && selectedGame && (
            <div>
              <label className="block text-xs font-black uppercase tracking-widest text-[#78716c] mb-2 font-mono">
                Select Team
              </label>
              <div className="flex gap-2">
                <button
                  type="button"
                  onClick={() => setSelectedTeam(selectedGame.home_team)}
                  className={`flex-1 rounded border-2 px-3 py-2 text-sm font-mono font-bold transition-colors ${
                    selectedTeam === selectedGame.home_team
                      ? "border-[#234058] bg-[#234058] text-[#F1EEE6]"
                      : "border-[#d1d5db] bg-white text-[#234058] hover:border-[#234058]"
                  }`}
                >
                  {selectedGame.home_team} (Home)
                </button>
                <button
                  type="button"
                  onClick={() => setSelectedTeam(selectedGame.away_team)}
                  className={`flex-1 rounded border-2 px-3 py-2 text-sm font-mono font-bold transition-colors ${
                    selectedTeam === selectedGame.away_team
                      ? "border-[#234058] bg-[#234058] text-[#F1EEE6]"
                      : "border-[#d1d5db] bg-white text-[#234058] hover:border-[#234058]"
                  }`}
                >
                  {selectedGame.away_team} (Away)
                </button>
              </div>
            </div>
          )}

          {step === 4 && (
            <div>
              <label className="block text-xs font-black uppercase tracking-widest text-[#78716c] mb-2 font-mono">
                Select Player
              </label>
              <select
                value={selectedPlayer ?? ""}
                onChange={(e) =>
                  setSelectedPlayer(e.target.value || null)
                }
                className="w-full rounded border-2 border-[#d1d5db] bg-white px-3 py-2 text-sm font-mono text-[#234058] focus:border-[#234058] focus:outline-none focus:ring-1 focus:ring-[#234058]"
              >
                <option value="">Choose player...</option>
                {players.map((p) => (
                  <option key={p.player_name} value={p.player_name}>
                    {p.player_name} · {p.position}
                  </option>
                ))}
              </select>
              {players.length === 0 && selectedTeam && (
                <p className="mt-2 text-xs text-[#78716c] font-mono">
                  No roster for this team. Sync rosters first.
                </p>
              )}
            </div>
          )}

          {step === 5 && (
            <div>
              <label className="block text-xs font-black uppercase tracking-widest text-[#78716c] mb-2 font-mono">
                Odds (optional, e.g. +350 or 350)
              </label>
              <input
                type="text"
                value={oddsInput}
                onChange={(e) => setOddsInput(e.target.value)}
                placeholder="+350"
                className="w-full rounded border-2 border-[#d1d5db] bg-white px-3 py-2 text-sm font-mono text-[#234058] focus:border-[#234058] focus:outline-none focus:ring-1 focus:ring-[#234058]"
              />
            </div>
          )}
        </div>

        <div className="flex justify-between gap-2 p-4 border-t-2 border-[#d1d5db] bg-[#f8fafc]">
          <button
            type="button"
            onClick={handleBack}
            disabled={step === 0}
            className="rounded border-2 border-[#d1d5db] bg-white px-4 py-2 text-sm font-mono font-bold text-[#234058] disabled:opacity-40 disabled:cursor-not-allowed hover:border-[#234058] transition-colors"
          >
            Back
          </button>
          {step < STEPS.length - 1 ? (
            <button
              type="button"
              onClick={handleNext}
              disabled={!canProceed()}
              className="rounded border-2 border-[#234058] bg-[#234058] px-4 py-2 text-sm font-mono font-bold text-[#F1EEE6] disabled:opacity-40 disabled:cursor-not-allowed hover:bg-[#1a3348] transition-colors inline-flex items-center gap-1"
            >
              Next <ChevronRight size={16} />
            </button>
          ) : (
            <button
              type="button"
              onClick={handleSubmit}
              disabled={loading}
              className="rounded border-2 border-[#234058] bg-[#234058] px-4 py-2 text-sm font-mono font-bold text-[#F1EEE6] disabled:opacity-40 hover:bg-[#1a3348] transition-colors inline-flex items-center gap-1"
            >
              {loading ? "Creating…" : "Create Pick"}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
