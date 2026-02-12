"use client";

import React from "react";
import TicketCard from "@/components/ui/TicketCard";

// Re-export for backward compatibility
export { TicketCard };

// --- Sub-Components ---

export const TeamLogo = ({ team, size = "md" }: { team: string, size?: "sm" | "md" | "lg" }) => {
    const sizes = { sm: "w-8 h-8", md: "w-14 h-14", lg: "w-20 h-20" };
    return (
        <div className={`${sizes[size]} relative flex items-center justify-center p-2 shrink-0 group-hover:scale-105 transition-transform duration-300`}>
            <div className="absolute inset-0 bg-[#e5e2d9] rounded-full opacity-50 mix-blend-multiply" />
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img
                src={`https://a.espncdn.com/i/teamlogos/nfl/500/${team.toLowerCase()}.png`}
                alt={team}
                className="w-full h-full object-contain mix-blend-multiply relative z-10"
            />
        </div>
    );
};

// --- NAV ITEM ---
export const NavItem = ({ icon, label, active, mobile }: any) => {
    if (mobile) {
        return (
            <button className={`flex flex-col items-center gap-1 p-2 rounded-lg transition-all ${active ? 'text-[#A2877D]' : 'text-[#8faec7]'}`}>
                {icon}
                <span className="text-[10px] font-bold uppercase tracking-wide font-mono">{label}</span>
            </button>
        );
    }
    return (
        <button className={`flex items-center gap-3 px-4 py-3 rounded-r-full w-full transition-all duration-200 border-l-4 mr-2 relative overflow-hidden group ${active ? 'bg-[#1a3348] border-[#A2877D] text-[#F1EEE6] shadow-md' : 'border-transparent text-[#8faec7] hover:bg-[#1a3348]/50 hover:text-[#F1EEE6]'}`}>

            {/* Texture: ACTIVE LEATHER */}
            {active && (
                <div className="absolute inset-0 opacity-[0.2] pointer-events-none mix-blend-overlay bg-repeat"
                    style={{ backgroundImage: `url("data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='activeSkin'%3E%3CfeTurbulence type='turbulence' baseFrequency='0.05' numOctaves='1' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23activeSkin)' opacity='1'/%3E%3C/svg%3E")` }}
                />
            )}

            {React.cloneElement(icon, { size: 18, className: "relative z-10" })}
            <span className="text-sm font-bold tracking-widest uppercase font-mono relative z-10">{label}</span>
        </button>
    );
};

export const AvatarGroup = ({ count, label }: { count: number, label: string }) => (
    <div className="flex items-center gap-2">
        <div className="flex -space-x-3">
            {[...Array(Math.min(3, count))].map((_, i) => (
                <div key={i} className="w-8 h-8 rounded-full bg-[#f3f4f6] border-2 border-[#F1EEE6] flex items-center justify-center text-[10px] text-[#234058] font-bold shadow-sm relative z-10">
                    {String.fromCharCode(65 + i)}
                </div>
            ))}
            {count > 3 && <div className="w-8 h-8 rounded-full bg-[#e5e7eb] border-2 border-[#F1EEE6] flex items-center justify-center text-[10px] text-[#6b7280] font-bold relative z-0">+{count - 3}</div>}
        </div>
        <span className="text-[10px] font-bold text-[#6b7280] uppercase tracking-wide pl-1 font-mono">{label}</span>
    </div>
);
