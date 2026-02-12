"use client";

import React, { useState, useEffect } from 'react';
import { Trophy, BarChart3, History, LayoutDashboard, Settings, Ticket, MapPin, Users, Wind, Menu } from 'lucide-react';
import RoiTrendsChart from './RoiTrendsChart';
import { NavItem, TicketCard, TeamLogo, AvatarGroup } from './Fast6Components';
import { LeaderboardEntry, RoiTrend, SeasonStats, Game, Pick, setStoredToken } from '@/lib/api';
import PickSelectionModal from './PickSelectionModal';

interface Fast6DashboardProps {
    leaderboard: LeaderboardEntry[];
    trends: RoiTrend[];
    stats: SeasonStats | null;
    games: Game[];
    userPicks: Pick[];
    authToken?: string;
}

export default function Fast6Dashboard({ leaderboard, trends, stats, games, userPicks, authToken }: Fast6DashboardProps) {
    const [selectedGame, setSelectedGame] = useState<Game | null>(null);

    // Sync server token to client storage for API calls
    useEffect(() => {
        if (authToken) {
            setStoredToken(authToken);
        }
    }, [authToken]);

    // Use real games if available, fallback to empty or processed
    const upcomingGames = games.map(g => {
        // Find if user has a pick for this game
        const userPick = userPicks.find(p => p.game_id === g.id);

        return {
            ...g, // Keep original game object for passing to modal
            t1: g.away_team,
            t2: g.home_team,
            time: new Date(g.game_date).toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' }),
            picked: userPick ? userPick.player_name : null,
            spread: userPick ? `(${userPick.odds})` : '', // Show odds if picked
            loc: 'Stadium', // Location not in Game model
            t1_ml: '',
            t2_ml: '',
            ou: '',
            status: g.status,
            home_score: g.home_score,
            away_score: g.away_score
        };
    });

    // Find a live game for the header ticket
    const liveGame = games.find(g => g.status === 'in_progress') || games[0];

    const totalPot = (stats?.total_picks || 0) * 10; // Mock pot calculation

    return (
        <div className="min-h-screen bg-[#F1EEE6] text-[#234058] font-sans selection:bg-[#8C302C]/30 overflow-x-hidden relative">

            {/* Modal */}
            {selectedGame && (
                <PickSelectionModal
                    game={selectedGame}
                    onClose={() => setSelectedGame(null)}
                    onSuccess={() => {
                        setSelectedGame(null);
                        // Ideally trigger a re-validate of the page data here
                        window.location.reload();
                    }}
                />
            )}

            {/* GLOBAL BACKGROUND: PIGSKIN TEXTURE */}
            <div className="fixed inset-0 opacity-[0.12] pointer-events-none z-0 mix-blend-multiply bg-repeat"
                style={{ backgroundImage: `url("data:image/svg+xml,%3Csvg viewBox='0 0 400 400' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='pigskin'%3E%3CfeTurbulence type='turbulence' baseFrequency='0.04' numOctaves='1' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23pigskin)' opacity='1'/%3E%3C/svg%3E")` }}
            ></div>

            <div className="max-w-[1600px] mx-auto flex relative z-10">

                {/* 1. LEFT SIDEBAR (Salty Dog #234058) */}
                <aside className="hidden lg:flex w-72 flex-col h-screen sticky top-0 border-r-2 border-[#1a3348] bg-[#234058] p-6 z-20 shadow-2xl relative overflow-hidden">

                    {/* Sidebar Leather Texture */}
                    <div className="absolute inset-0 opacity-[0.1] pointer-events-none z-0 mix-blend-overlay bg-repeat"
                        style={{ backgroundImage: `url("data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='sidebarSkin'%3E%3CfeTurbulence type='turbulence' baseFrequency='0.05' numOctaves='1' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23sidebarSkin)' opacity='1'/%3E%3C/svg%3E")` }}
                    ></div>

                    {/* Logo */}
                    <div className="flex items-center gap-3 mb-12 px-2 group cursor-pointer border-b border-[#1a3348] pb-6 relative z-10">
                        <div className="w-12 h-12 bg-[#8C302C] rounded-sm flex items-center justify-center shadow-lg transform -rotate-3 border-2 border-[#1a3348]">
                            <Ticket size={24} className="text-[#F1EEE6]" />
                        </div>
                        <div className="flex flex-col">
                            <span className="text-3xl font-black tracking-tighter text-[#F1EEE6] leading-none font-mono">
                                FAST<span className="text-[#8C302C]">6</span>
                            </span>
                            <span className="text-[9px] font-bold text-[#8faec7] uppercase tracking-[0.2em] ml-0.5">Ticket Office</span>
                        </div>
                    </div>

                    <nav className="space-y-1 flex-1 relative z-10">
                        <NavItem icon={<LayoutDashboard />} label="Board" active />
                        <NavItem icon={<Trophy />} label="Rankings" />
                        <NavItem icon={<History />} label="Stubs" />
                        <NavItem icon={<BarChart3 />} label="Analysis" />
                        <NavItem icon={<Settings />} label="Config" />
                    </nav>

                    <div className="mt-auto pt-6 border-t border-[#1a3348] relative z-10">
                        <div className="p-3 bg-[#1a3348] rounded-lg border border-[#234058] flex items-center gap-3 hover:border-[#8C302C] transition-colors cursor-pointer group">
                            <div className="w-10 h-10 bg-[#F1EEE6] text-[#234058] flex items-center justify-center font-bold font-mono text-sm shadow-lg">AK</div>
                            <div className="flex-1 min-w-0">
                                <div className="text-xs font-bold uppercase tracking-wider text-[#8faec7]">Member #001</div>
                                <div className="text-sm font-black text-[#F1EEE6] group-hover:text-[#8C302C] transition-colors">@akursar</div>
                            </div>
                        </div>
                    </div>
                </aside>

                {/* 2. CENTER FEED */}
                <main className="flex-1 min-w-0 border-r-2 border-[#d1d5db] relative z-10">

                    {/* Desktop Header */}
                    <div className="hidden lg:flex items-center justify-between px-8 py-6 sticky top-0 bg-[#F1EEE6]/95 backdrop-blur-sm z-40 border-b-2 border-[#d1d5db]">
                        <div className="flex flex-col">
                            <h1 className="text-xl font-black tracking-widest text-[#234058] uppercase font-mono flex items-center gap-2">
                        /// Week {stats?.total_weeks || '4'} Slate ///
                            </h1>
                        </div>

                        <div className="flex items-center gap-3 bg-[#234058] text-[#F1EEE6] px-5 py-2 rounded-sm shadow-md border border-[#1a3348]">
                            <span className="text-[10px] font-bold uppercase tracking-wider text-[#8faec7]">Pot Total</span>
                            <span className="text-lg font-mono font-bold">${totalPot.toFixed(2)}</span>
                        </div>
                    </div>

                    <div className="p-4 md:p-8 space-y-8 max-w-4xl mx-auto">

                        {/* LIVE TICKET */}
                        <section>
                            <div className="flex items-center gap-2 mb-3 px-1">
                                <span className="w-2 h-2 bg-[#8C302C] rounded-full animate-pulse" />
                                <h2 className="text-xs font-black tracking-widest text-[#8C302C] uppercase font-mono">Live Action</h2>
                            </div>

                            <div className="relative group">
                                {/* Salty Dog Ticket Container - Texture Added */}
                                <div className="relative bg-[#234058] text-[#F1EEE6] rounded-lg overflow-hidden shadow-xl border-y-2 border-l-2 border-r-2 border-[#1a3348]">
                                    {/* LEATHER HEADER TEXTURE */}
                                    <div className="absolute inset-0 opacity-[0.1] pointer-events-none z-0 mix-blend-overlay bg-repeat"
                                        style={{ backgroundImage: `url("data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='headerSkin'%3E%3CfeTurbulence type='turbulence' baseFrequency='0.05' numOctaves='1' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23headerSkin)' opacity='1'/%3E%3C/svg%3E")` }}
                                    />

                                    {/* Notches */}
                                    <div
                                        className="absolute top-1/2 -translate-y-1/2 -left-4 w-8 h-8 bg-[#F1EEE6] rounded-full z-20"
                                        style={{ border: '2px solid #1a3348' }}
                                    />
                                    <div
                                        className="absolute top-1/2 -translate-y-1/2 -right-4 w-8 h-8 bg-[#F1EEE6] rounded-full z-20"
                                        style={{ border: '2px solid #1a3348' }}
                                    />

                                    {/* Dashed Line */}
                                    <div className="absolute top-0 bottom-0 left-[65%] w-0 border-l-2 border-dashed border-[#1a3348] z-10 hidden md:block" />

                                    <div className="flex flex-col md:flex-row h-full relative z-10">
                                        {/* Left Side: Scoreboard */}
                                        <div className="flex-1 flex flex-col justify-between relative">
                                            <div className="px-8 pt-6 pb-4 border-b border-[#1a3348] flex justify-between items-start bg-[#1a3348]/30">
                                                <div className="flex flex-col gap-1">
                                                    <div className="flex items-center gap-2 text-[#8faec7]">
                                                        <MapPin size={12} />
                                                        <span className="text-[10px] font-bold uppercase tracking-wider font-mono">GEHA Field at Arrowhead</span>
                                                    </div>
                                                    <div className="text-[10px] font-bold text-[#cbd5e1] uppercase tracking-wider font-mono ml-5">
                                                        Kansas City, MO
                                                    </div>
                                                </div>
                                                <div className="flex flex-col items-end gap-1">
                                                    <div className="flex items-center gap-2 text-[#8faec7]">
                                                        <Users size={12} />
                                                        <span className="text-[10px] font-bold uppercase tracking-wider font-mono">76,416 / 76,416</span>
                                                    </div>
                                                    <span className="text-[9px] font-black uppercase tracking-widest border border-[#8C302C] text-[#8C302C] px-1 rounded-sm bg-[#8C302C]/10">SOLD OUT</span>
                                                </div>
                                            </div>

                                            <div className="p-8">
                                                <div className="flex justify-between items-start mb-6">
                                                    <div className="text-center w-1/3">
                                                        <span className="text-4xl font-black block leading-none font-mono text-white">{liveGame?.home_team || 'KC'}</span>
                                                        <span className="text-[10px] font-bold text-[#8faec7] uppercase tracking-widest block mb-1">Home</span>
                                                        <div className="inline-block bg-[#1a3348] px-2 py-0.5 rounded border border-[#0f1f2e]">
                                                            <span className="text-[10px] font-bold text-[#e2e8f0] font-mono">ML -110</span>
                                                        </div>
                                                    </div>
                                                    <div className="flex flex-col items-center w-1/3">
                                                        <div className="text-5xl font-black font-mono tracking-tighter text-[#F1EEE6] drop-shadow-[0_4px_0_rgba(0,0,0,0.2)]">
                                                            {liveGame?.home_score ?? 0}-{liveGame?.away_score ?? 0}
                                                        </div>
                                                        <div className="mt-2 flex flex-col items-center">
                                                            <span className="text-[10px] font-bold text-[#8faec7] uppercase tracking-wider">Status</span>
                                                            <span className="text-xs font-bold text-[#F1EEE6] font-mono">{liveGame?.status === 'in_progress' ? 'LIVE' : 'FINAL'}</span>
                                                        </div>
                                                    </div>
                                                    <div className="text-center w-1/3">
                                                        <span className="text-4xl font-black block leading-none font-mono text-white">{liveGame?.away_team || 'BAL'}</span>
                                                        <span className="text-[10px] font-bold text-[#8faec7] uppercase tracking-widest block mb-1">Away</span>
                                                        <div className="inline-block bg-[#1a3348] px-2 py-0.5 rounded border border-[#0f1f2e]">
                                                            <span className="text-[10px] font-bold text-[#e2e8f0] font-mono">ML -110</span>
                                                        </div>
                                                    </div>
                                                </div>
                                            </div>

                                            <div className="flex justify-between items-center pt-6 border-t border-[#1a3348]">
                                                <AvatarGroup count={6} label="Sector 101" />
                                                <div className="flex items-center gap-2 text-[#A2877D]">
                                                    <Wind size={12} />
                                                    <span className="text-xs font-mono font-bold">12 MPH NW</span>
                                                </div>
                                                <AvatarGroup count={2} label="Sector 102" />
                                            </div>
                                        </div>

                                        {/* Right Side Stub */}
                                        <div className="w-full md:w-[35%] bg-[#1a3348]/50 p-6 flex flex-col justify-center items-center relative">
                                            <div className="text-center space-y-2">
                                                <div className="text-[10px] font-bold text-[#8faec7] uppercase tracking-widest">Your Position</div>
                                                <div className="text-2xl font-black text-[#8C302C] font-mono drop-shadow-sm">CHIEFS</div>
                                                <div className="text-xs font-mono text-[#e2e8f0]">-3.5 Spread</div>
                                            </div>
                                            <div className="mt-6 w-full opacity-30">
                                                <div className="h-8 w-full bg-[repeating-linear-gradient(90deg,transparent,transparent_2px,#fff_2px,#fff_4px)]" />
                                                <div className="flex justify-between text-[8px] font-mono text-[#8faec7] mt-1">
                                                    <span>TICKET: #8493-29</span>
                                                    <span>NO REFUNDS</span>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </section>

                        {/* UPCOMING TICKETS */}
                        <section>
                            <div className="flex items-center justify-between mb-4 px-1">
                                <h2 className="text-xs font-black tracking-widest text-[#78716c] uppercase font-mono">Box Office</h2>
                            </div>

                            <div className="space-y-4">
                                {upcomingGames.map((game, i) => (
                                    <TicketCard key={i} active={!!game.picked}>
                                        <div className="flex flex-col md:flex-row min-h-[140px]">
                                            {/* Game Info */}
                                            <div className="flex-1 p-6 flex flex-col justify-center">
                                                <div className="flex justify-between items-start mb-6">
                                                    <div className="flex items-center gap-1.5 text-[#a8a29e]">
                                                        <MapPin size={10} />
                                                        <span className="text-[9px] font-bold uppercase tracking-wider font-mono text-[#78716c]">{game.loc}</span>
                                                    </div>
                                                    <span className="text-[9px] font-bold uppercase tracking-wider font-mono text-[#78716c]">{game.time} EST</span>
                                                </div>

                                                <div className="flex items-center justify-between">
                                                    {/* Team 1 */}
                                                    <div className="flex flex-col items-center gap-2 w-1/3">
                                                        <TeamLogo team={game.t1} />
                                                        <span className="text-[10px] font-bold text-[#234058] font-mono tracking-tighter bg-[#f3f4f6] px-1.5 py-0.5 rounded border border-[#e5e7eb]">
                                                            ML {game.t1_ml}
                                                        </span>
                                                    </div>

                                                    {/* Center */}
                                                    <div className="flex flex-col items-center gap-1 w-1/3">
                                                        <span className="text-lg font-black font-mono text-[#d1d5db]">VS</span>
                                                        <div className="flex flex-col items-center">
                                                            <span className="text-[8px] font-bold text-[#a8a29e] uppercase">Total</span>
                                                            <span className="text-[10px] font-bold text-[#234058] font-mono">O/U {game.ou}</span>
                                                        </div>
                                                    </div>

                                                    {/* Team 2 */}
                                                    <div className="flex flex-col items-center gap-2 w-1/3">
                                                        <TeamLogo team={game.t2} />
                                                        <span className="text-[10px] font-bold text-[#234058] font-mono tracking-tighter bg-[#f3f4f6] px-1.5 py-0.5 rounded border border-[#e5e7eb]">
                                                            ML {game.t2_ml}
                                                        </span>
                                                    </div>
                                                </div>
                                            </div>

                                            {/* Action Stub */}
                                            <div className="w-full md:w-[30%] bg-[#f8fafc] p-6 flex items-center justify-center border-t md:border-t-0 md:border-l border-dashed border-[#d1d5db]">
                                                {game.picked ? (
                                                    <div className="flex flex-col items-center">
                                                        <div className="w-16 h-16 rounded-full border-4 border-double border-[#8C302C] flex items-center justify-center text-[#8C302C] font-black -rotate-12 opacity-80 mix-blend-multiply bg-white shadow-sm">
                                                            PAID
                                                        </div>
                                                        <span className="text-xs font-bold mt-2 font-mono text-[#8C302C]">{game.picked} {game.spread}</span>
                                                    </div>
                                                ) : (
                                                    <button
                                                        onClick={() => setSelectedGame(game)}
                                                        className="w-full py-3 bg-[#234058] text-[#F1EEE6] font-black uppercase font-mono text-xs hover:bg-[#8C302C] transition-colors shadow-lg"
                                                    >
                                                        Punch Ticket
                                                    </button>
                                                )}
                                            </div>
                                        </div>
                                    </TicketCard>
                                ))}
                            </div>
                        </section>
                    </div>
                </main>

                {/* 3. RIGHT PANEL */}
                <aside className="hidden xl:block w-80 sticky top-0 h-screen p-6 border-l-2 border-[#d1d5db] bg-[#F1EEE6] z-20 overflow-y-auto">

                    {/* ROI Chart */}
                    <div className="mb-8">
                        <div className="flex justify-between items-center mb-4 px-1">
                            <span className="text-xs font-black tracking-widest text-[#78716c] uppercase font-mono">Yield Analysis</span>
                        </div>
                        <div className="bg-[#fff] border-2 border-[#d1d5db] p-4 relative shadow-sm">
                            {/* Paper holes decoration */}
                            <div className="absolute top-0 left-0 w-full h-4 flex justify-between px-2 -mt-2">
                                {[...Array(6)].map((_, i) => <div key={i} className="w-3 h-3 bg-[#F1EEE6] rounded-full" />)}
                            </div>

                            <div className="mt-2">
                                <div className="flex justify-between items-end mb-2">
                                    <span className="text-xs font-bold text-[#a8a29e] uppercase">Leader</span>
                                    <span className="text-xl font-black text-[#15803d] font-mono">
                                        {leaderboard.length > 0 ? `+${leaderboard[0].roi_dollars.toFixed(0)}$` : '$0'}
                                    </span>
                                </div>
                                <RoiTrendsChart data={trends} />
                            </div>
                        </div>
                    </div>

                    {/* Standings */}
                    <div className="mb-8">
                        <div className="flex justify-between items-center mb-4 px-1">
                            <span className="text-xs font-black tracking-widest text-[#78716c] uppercase font-mono">Leaderboard</span>
                        </div>
                        <div className="bg-[#fff] border-2 border-[#d1d5db] p-1 shadow-sm">
                            <div className="overflow-x-auto">
                                <table className="w-full text-left">
                                    <thead className="bg-[#f8fafc] border-b-2 border-[#d1d5db] text-[10px] uppercase text-[#64748b] font-bold">
                                        <tr>
                                            <th className="p-2">#</th>
                                            <th className="p-2">Agent</th>
                                            <th className="p-2 text-right">Rec</th>
                                        </tr>
                                    </thead>
                                    <tbody className="font-mono text-sm">
                                        {leaderboard.map((user, i) => (
                                            <tr key={i} className="border-b border-dashed border-[#e5e7eb] hover:bg-[#fff7ed]">
                                                <td className="p-2 font-bold text-[#A2877D]">0{i + 1}</td>
                                                <td className="p-2 font-bold text-[#234058]">{user.user_name}</td>
                                                <td className="p-2 text-right text-[#44403c]">{user.correct_picks}-{user.total_picks - user.correct_picks}</td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    </div>
                </aside>

            </div>

            {/* Mobile Nav */}
            <div className="md:hidden fixed bottom-6 left-1/2 -translate-x-1/2 w-[90%] bg-[#234058] border-2 border-[#1a3348] rounded-full shadow-2xl flex justify-around items-center px-4 py-2 z-50">
                <NavItem icon={<LayoutDashboard size={24} />} label="Board" active />
                <NavItem icon={<Trophy size={24} />} label="Rank" />
                <div className="w-14 h-14 bg-[#8C302C] rounded-full -mt-10 shadow-lg flex items-center justify-center border-4 border-[#F1EEE6] active:scale-95 transition-transform">
                    <Ticket size={24} className="text-[#F1EEE6]" />
                </div>
                <NavItem icon={<BarChart3 size={24} />} label="Data" />
                <NavItem icon={<Menu size={24} />} label="Menu" />
            </div>

        </div >
    );
}
