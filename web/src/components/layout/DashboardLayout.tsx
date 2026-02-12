"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import type { ReactNode } from "react";
import {
  LayoutDashboard,
  Trophy,
  BarChart3,
  History,
  Settings,
  Ticket,
  Menu,
  Calendar,
} from "lucide-react";
import RoiTrendsChartMulti from "@/components/analytics/RoiTrendsChartMulti";
import type { RoiTrendByUser, LeaderboardEntry } from "@/lib/api";

interface DashboardLayoutProps {
  children: ReactNode;
  roiTrendsByUser?: RoiTrendByUser[];
  leaderboard?: LeaderboardEntry[];
}

const currentWeek = process.env.NEXT_PUBLIC_CURRENT_WEEK ?? "1";

const navItems = [
  { href: "/", label: "Board", icon: LayoutDashboard },
  { href: "/leaderboard", label: "Rankings", icon: Trophy },
  { href: "/schedule/" + currentWeek, label: "Schedule", icon: Calendar },
  { href: "/weeks/" + currentWeek, label: "Stubs", icon: History },
  { href: "/analytics", label: "Analysis", icon: BarChart3 },
  { href: "/about", label: "Config", icon: Settings },
];

export default function DashboardLayout({
  children,
  roiTrendsByUser = [],
  leaderboard = [],
}: DashboardLayoutProps) {
  const pathname = usePathname();

  function isActive(href: string): boolean {
    if (href === "/") return pathname === "/";
    return pathname.startsWith(href);
  }

  return (
    <div className="min-h-screen bg-[#F1EEE6] text-[#234058] font-sans selection:bg-[#8C302C]/30 overflow-x-hidden relative">
      {/* GLOBAL BACKGROUND: PIGSKIN TEXTURE */}
      <div
        className="fixed inset-0 opacity-[0.12] pointer-events-none z-0 mix-blend-multiply bg-repeat"
        style={{
          backgroundImage: `url("data:image/svg+xml,%3Csvg viewBox='0 0 400 400' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='pigskin'%3E%3CfeTurbulence type='turbulence' baseFrequency='0.04' numOctaves='1' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23pigskin)' opacity='1'/%3E%3C/svg%3E")`,
        }}
      />

      <div className="max-w-[1600px] mx-auto flex relative z-10">
        {/* 1. LEFT SIDEBAR (Salty Dog #234058) */}
        <aside className="hidden lg:flex w-72 flex-col h-screen sticky top-0 border-r-2 border-[#1a3348] bg-[#234058] p-6 z-20 shadow-2xl relative overflow-hidden">
          {/* Sidebar Leather Texture */}
          <div
            className="absolute inset-0 opacity-[0.1] pointer-events-none z-0 mix-blend-overlay bg-repeat"
            style={{
              backgroundImage: `url("data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='sidebarSkin'%3E%3CfeTurbulence type='turbulence' baseFrequency='0.05' numOctaves='1' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23sidebarSkin)' opacity='1'/%3E%3C/svg%3E")`,
            }}
          />

          {/* Logo */}
          <Link
            href="/"
            className="flex items-center gap-3 mb-12 px-2 group cursor-pointer border-b border-[#1a3348] pb-6 relative z-10"
          >
            <div className="w-12 h-12 bg-[#8C302C] rounded-sm flex items-center justify-center shadow-lg transform -rotate-3 border-2 border-[#1a3348]">
              <Ticket size={24} className="text-[#F1EEE6]" />
            </div>
            <div className="flex flex-col">
              <span className="text-3xl font-black tracking-tighter text-[#F1EEE6] leading-none font-mono">
                FAST<span className="text-[#8C302C]">6</span>
              </span>
              <span className="text-[9px] font-bold text-[#8faec7] uppercase tracking-[0.2em] ml-0.5">
                Ticket Office
              </span>
            </div>
          </Link>

          <nav className="space-y-1 flex-1 relative z-10">
            {navItems.map((item) => {
              const active = isActive(item.href);
              const Icon = item.icon;
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`flex items-center gap-3 px-4 py-3 rounded-r-full w-full transition-all duration-200 border-l-4 mr-2 relative overflow-hidden group ${
                    active
                      ? "bg-[#1a3348] border-[#A2877D] text-[#F1EEE6] shadow-md"
                      : "border-transparent text-[#8faec7] hover:bg-[#1a3348]/50 hover:text-[#F1EEE6]"
                  }`}
                >
                  {active && (
                    <div
                      className="absolute inset-0 opacity-[0.2] pointer-events-none mix-blend-overlay bg-repeat"
                      style={{
                        backgroundImage: `url("data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='activeSkin'%3E%3CfeTurbulence type='turbulence' baseFrequency='0.05' numOctaves='1' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23activeSkin)' opacity='1'/%3E%3C/svg%3E")`,
                      }}
                    />
                  )}
                  <Icon size={18} className="relative z-10" />
                  <span className="text-sm font-bold tracking-widest uppercase font-mono relative z-10">
                    {item.label}
                  </span>
                </Link>
              );
            })}
          </nav>

          <div className="mt-auto pt-6 border-t border-[#1a3348] relative z-10">
            <Link
              href="/admin"
              className="block p-3 bg-[#1a3348] rounded-lg border border-[#234058] hover:border-[#8C302C] transition-colors cursor-pointer group"
            >
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-[#F1EEE6] text-[#234058] flex items-center justify-center font-bold font-mono text-sm shadow-lg">
                  AK
                </div>
                <div className="flex-1 min-w-0">
                  <div className="text-xs font-bold uppercase tracking-wider text-[#8faec7]">
                    Admin
                  </div>
                  <div className="text-sm font-black text-[#F1EEE6] group-hover:text-[#8C302C] transition-colors">
                    Settings
                  </div>
                </div>
              </div>
            </Link>
          </div>
        </aside>

        {/* 2. CENTER FEED */}
        <main className="flex-1 min-w-0 border-r-2 border-[#d1d5db] relative z-10">
          {/* Desktop Header */}
          <div className="hidden lg:flex items-center justify-between px-8 py-6 sticky top-0 bg-[#F1EEE6]/95 backdrop-blur-sm z-40 border-b-2 border-[#d1d5db]">
            <div className="flex flex-col">
              <h1 className="text-xl font-black tracking-widest text-[#234058] uppercase font-mono flex items-center gap-2">
                /// Public Dashboard ///
              </h1>
            </div>
            <div className="flex items-center gap-3 bg-[#234058] text-[#F1EEE6] px-5 py-2 rounded-sm shadow-md border border-[#1a3348]">
              <span className="text-[10px] font-bold uppercase tracking-wider text-[#8faec7]">
                Season {process.env.NEXT_PUBLIC_CURRENT_SEASON ?? "2025"}
              </span>
            </div>
          </div>

          {/* Mobile Header */}
          <div className="lg:hidden flex flex-col gap-4 rounded-2xl border-2 border-[#d1d5db] bg-[#F1EEE6] px-5 py-4 mx-4 mt-4">
            <div className="flex justify-between items-center">
              <div>
                <div className="text-lg font-black text-[#234058] font-mono">
                  FAST<span className="text-[#8C302C]">6</span>
                </div>
                <div className="text-[0.6rem] uppercase tracking-[0.3em] text-[#78716c] font-mono">
                  Ticket Office
                </div>
              </div>
              <span className="text-xs font-bold text-[#78716c] uppercase tracking-wider font-mono">
                Season {process.env.NEXT_PUBLIC_CURRENT_SEASON ?? "2025"}
              </span>
            </div>
            <nav className="flex flex-wrap gap-2 text-xs uppercase tracking-[0.2em] font-mono">
              {navItems.map((item) => {
                const active = isActive(item.href);
                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    className={`rounded-full border min-h-[44px] min-w-[44px] inline-flex items-center justify-center px-4 py-2 transition font-bold ${
                      active
                        ? "border-[#A2877D] bg-[#234058]/10 text-[#234058]"
                        : "border-[#d1d5db] text-[#78716c] hover:border-[#A2877D] hover:text-[#234058]"
                    }`}
                  >
                    {item.label}
                  </Link>
                );
              })}
            </nav>
          </div>

          <div className="p-4 pb-28 md:p-8 md:pb-8">{children}</div>
        </main>

        {/* 3. RIGHT PANEL - Yield Analysis */}
        <aside className="hidden xl:block w-80 sticky top-0 h-screen p-6 border-l-2 border-[#d1d5db] bg-[#F1EEE6] z-20 overflow-y-auto">
          <div className="mb-8">
            <div className="flex justify-between items-center mb-4 px-1">
              <span className="text-xs font-black tracking-widest text-[#78716c] uppercase font-mono">
                Yield Analysis
              </span>
            </div>
            <div className="bg-[#fff] border-2 border-[#d1d5db] p-4 relative shadow-sm">
              <div className="absolute top-0 left-0 w-full h-4 flex justify-between px-2 -mt-2">
                {[...Array(6)].map((_, i) => (
                  <div key={i} className="w-3 h-3 bg-[#F1EEE6] rounded-full" />
                ))}
              </div>
              <div className="mt-2">
                <div className="flex justify-between items-end mb-2">
                  <span className="text-xs font-bold text-[#a8a29e] uppercase">
                    Leader
                  </span>
                  <span className="text-xl font-black text-[#15803d] font-mono">
                    {leaderboard.length > 0
                      ? `$${leaderboard[0].roi_dollars >= 0 ? "+" : ""}${leaderboard[0].roi_dollars.toFixed(0)}`
                      : "$0"}
                  </span>
                </div>
                <RoiTrendsChartMulti data={roiTrendsByUser} />
              </div>
            </div>
          </div>
          <div className="mb-8">
            <div className="flex justify-between items-center mb-4 px-1">
              <span className="text-xs font-black tracking-widest text-[#78716c] uppercase font-mono">
                Leaderboard
              </span>
            </div>
            <div className="bg-[#fff] border-2 border-[#d1d5db] p-1 shadow-sm">
              <table className="w-full text-left font-mono text-sm">
                <thead className="bg-[#f8fafc] border-b-2 border-[#d1d5db] text-[10px] uppercase text-[#64748b] font-bold">
                  <tr>
                    <th className="p-2">#</th>
                    <th className="p-2">Agent</th>
                    <th className="p-2 text-right">Rec</th>
                  </tr>
                </thead>
                <tbody>
                  {leaderboard.length > 0 ? (
                    leaderboard.slice(0, 5).map((entry, i) => (
                      <tr
                        key={entry.user_id}
                        className="border-b border-dashed border-[#e5e7eb] hover:bg-[#fff7ed]"
                      >
                        <td className="p-2 font-bold text-[#A2877D]">
                          {String(entry.rank).padStart(2, "0")}
                        </td>
                        <td className="p-2 font-bold text-[#234058]">
                          <Link
                            href={`/users/${entry.user_id}`}
                            className="hover:text-[#8C302C] transition"
                          >
                            {entry.user_name}
                          </Link>
                        </td>
                        <td className="p-2 text-right text-[#44403c]">
                          {entry.correct_picks}-{entry.total_picks - entry.correct_picks}
                        </td>
                      </tr>
                    ))
                  ) : (
                    <tr>
                      <td colSpan={3} className="p-4 text-center text-[#78716c] text-sm">
                        No data yet
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </aside>
      </div>

      {/* Mobile Nav */}
      <div className="md:hidden fixed bottom-6 left-1/2 -translate-x-1/2 w-[90%] max-w-[400px] bg-[#234058] border-2 border-[#1a3348] rounded-full shadow-2xl flex justify-around items-center px-2 py-3 z-50 pb-[max(0.75rem,env(safe-area-inset-bottom))]">
        <Link
          href="/"
          className={`flex flex-col items-center gap-1 min-h-[44px] min-w-[44px] justify-center p-2 rounded-lg transition-all ${
            pathname === "/" ? "text-[#A2877D]" : "text-[#8faec7]"
          }`}
        >
          <LayoutDashboard size={24} />
          <span className="text-[10px] font-bold uppercase tracking-wide font-mono">
            Board
          </span>
        </Link>
        <Link
          href={"/schedule/" + currentWeek}
          className={`flex flex-col items-center gap-1 min-h-[44px] min-w-[44px] justify-center p-2 rounded-lg transition-all ${
            pathname.startsWith("/schedule") ? "text-[#A2877D]" : "text-[#8faec7]"
          }`}
        >
          <Calendar size={24} />
          <span className="text-[10px] font-bold uppercase tracking-wide font-mono">
            Sched
          </span>
        </Link>
        <Link
          href="/leaderboard"
          className={`flex flex-col items-center gap-1 min-h-[44px] min-w-[44px] justify-center p-2 rounded-lg transition-all ${
            pathname.startsWith("/leaderboard") ? "text-[#A2877D]" : "text-[#8faec7]"
          }`}
        >
          <Trophy size={24} />
          <span className="text-[10px] font-bold uppercase tracking-wide font-mono">
            Rank
          </span>
        </Link>
        <Link
          href="/fast6"
          className="w-14 h-14 bg-[#8C302C] rounded-full -mt-10 shadow-lg flex items-center justify-center border-4 border-[#F1EEE6] active:scale-95 transition-transform"
        >
          <Ticket size={24} className="text-[#F1EEE6]" />
        </Link>
        <Link
          href="/analytics"
          className={`flex flex-col items-center gap-1 min-h-[44px] min-w-[44px] justify-center p-2 rounded-lg transition-all ${
            pathname.startsWith("/analytics") ? "text-[#A2877D]" : "text-[#8faec7]"
          }`}
        >
          <BarChart3 size={24} />
          <span className="text-[10px] font-bold uppercase tracking-wide font-mono">
            Data
          </span>
        </Link>
        <Link
          href="/about"
          className={`flex flex-col items-center gap-1 min-h-[44px] min-w-[44px] justify-center p-2 rounded-lg transition-all ${
            pathname.startsWith("/about") ? "text-[#A2877D]" : "text-[#8faec7]"
          }`}
        >
          <Menu size={24} />
          <span className="text-[10px] font-bold uppercase tracking-wide font-mono">
            Menu
          </span>
        </Link>
      </div>
    </div>
  );
}
