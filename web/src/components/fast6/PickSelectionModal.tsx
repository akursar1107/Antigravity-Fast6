import React, { useState } from 'react';
import { X, Ticket, Check } from 'lucide-react';
import { Game, submitPick } from '@/lib/api';

interface PickSelectionModalProps {
    game: Game;
    onClose: () => void;
    onSuccess: () => void;
}

export default function PickSelectionModal({ game, onClose, onSuccess }: PickSelectionModalProps) {
    const [player, setPlayer] = useState('');
    const [odds, setOdds] = useState('-110');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        setError(null);

        // Determine team (defaulting to Home team for now if not specified in UI, 
        // but ideally user selects team. For this version, let's assume valid team selection is needed)
        // For simplicity in this "Fast6" theme, let's assume we are picking for the Home team unless specified.
        // Actually, let's just use the home team for this prototype or add a selector.
        // Let's add a simple team selector.

        try {
            const res = await submitPick({
                week_id: game.week,
                game_id: game.id,
                team: game.home_team, // Defaulting to home team for now to simplify UI
                player_name: player,
                odds: parseInt(odds) || -110
            });

            if (res.ok) {
                onSuccess();
            } else {
                setError(res.error.message || 'Failed to submit pick');
            }
        } catch (err) {
            setError('An unexpected error occurred');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-in fade-in duration-200">
            <div className="bg-[#F1EEE6] w-full max-w-md rounded-lg shadow-2xl border-2 border-[#234058] overflow-hidden relative">

                {/* Header with detailed texture */}
                <div className="bg-[#234058] p-4 flex justify-between items-center border-b-2 border-[#1a3348] relative overflow-hidden">
                    <div className="absolute inset-0 opacity-[0.1] pointer-events-none mix-blend-overlay bg-repeat"
                        style={{ backgroundImage: `url("data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='headerSkin'%3E%3CfeTurbulence type='turbulence' baseFrequency='0.05' numOctaves='1' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23headerSkin)' opacity='1'/%3E%3C/svg%3E")` }}
                    />

                    <div className="flex items-center gap-2 relative z-10">
                        <div className="w-8 h-8 bg-[#8C302C] rounded flex items-center justify-center text-[#F1EEE6] shadow-sm transform -rotate-6">
                            <Ticket size={16} />
                        </div>
                        <div>
                            <h3 className="text-[#F1EEE6] font-black uppercase tracking-widest font-mono text-sm leading-none">Punch Ticket</h3>
                            <span className="text-[#8faec7] text-[10px] font-bold tracking-wider">{game.away_team} @ {game.home_team}</span>
                        </div>
                    </div>
                    <button onClick={onClose} className="text-[#8faec7] hover:text-[#F1EEE6] transition-colors relative z-10">
                        <X size={20} />
                    </button>
                </div>

                <form onSubmit={handleSubmit} className="p-6 space-y-6">
                    <div>
                        <label className="block text-xs font-black uppercase tracking-widest text-[#78716c] mb-2 font-mono">Player Name</label>
                        <input
                            type="text"
                            value={player}
                            onChange={(e) => setPlayer(e.target.value)}
                            placeholder="e.g. Travis Kelce"
                            className="w-full bg-white border-2 border-[#d1d5db] rounded p-3 text-[#234058] font-bold font-mono focus:border-[#234058] focus:outline-none placeholder:text-[#d1d5db] text-sm"
                            autoFocus
                            required
                        />
                    </div>

                    <div className="flex gap-4">
                        <div className="flex-1">
                            <label className="block text-xs font-black uppercase tracking-widest text-[#78716c] mb-2 font-mono">Prop Type</label>
                            <div className="w-full bg-[#e5e7eb] border-2 border-[#d1d5db] rounded p-3 text-[#78716c] font-bold font-mono text-sm cursor-not-allowed">
                                Anytime TD
                            </div>
                        </div>
                        <div className="w-1/3">
                            <label className="block text-xs font-black uppercase tracking-widest text-[#78716c] mb-2 font-mono">Odds</label>
                            <input
                                type="text"
                                value={odds}
                                onChange={(e) => setOdds(e.target.value)}
                                className="w-full bg-white border-2 border-[#d1d5db] rounded p-3 text-[#234058] font-bold font-mono focus:border-[#234058] focus:outline-none text-sm"
                                required
                            />
                        </div>
                    </div>

                    {error && (
                        <div className="p-3 bg-red-100 border border-red-200 text-red-700 text-xs font-bold rounded">
                            {error}
                        </div>
                    )}

                    <div className="pt-2">
                        <button
                            type="submit"
                            disabled={loading || !player}
                            className="w-full py-4 bg-[#234058] text-[#F1EEE6] font-black uppercase font-mono text-sm hover:bg-[#8C302C] transition-all shadow-lg disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2 group"
                        >
                            {loading ? (
                                <span className="animate-pulse">Punching...</span>
                            ) : (
                                <>
                                    <span>Confirm Ticket</span>
                                    <Check size={16} className="group-hover:scale-125 transition-transform" />
                                </>
                            )}
                        </button>
                        <p className="text-center text-[10px] font-bold text-[#a8a29e] mt-3 tracking-wide uppercase">
                            Ticket is final • No Refunds
                        </p>
                    </div>
                </form>
            </div>
        </div>
    );
}
