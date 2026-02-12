"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import type { ReactNode } from "react";
import { LayoutDashboard, Users, FileCheck, List, Ticket, LogOut } from "lucide-react";

const adminNav = [
  { href: "/admin", label: "Dashboard", icon: LayoutDashboard },
  { href: "/admin/users", label: "Users", icon: Users },
  { href: "/admin/picks", label: "Picks", icon: List },
  { href: "/admin/grading", label: "Grading", icon: FileCheck },
];

export default function AdminLayoutClient({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();

  function isActive(href: string): boolean {
    if (href === "/admin") return pathname === "/admin";
    return pathname.startsWith(href);
  }

  async function handleLogout() {
    await fetch("/api/auth/logout", { method: "POST" });
    router.push("/login?redirect=/admin");
    router.refresh();
  }

  return (
    <div className="min-h-screen bg-[#F1EEE6] text-[#234058] selection:bg-[#8C302C]/30 overflow-x-hidden relative">
      {/* Pigskin background */}
      <div
        className="fixed inset-0 opacity-[0.12] pointer-events-none z-0 mix-blend-multiply bg-repeat"
        style={{
          backgroundImage: `url("data:image/svg+xml,%3Csvg viewBox='0 0 400 400' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='pigskin'%3E%3CfeTurbulence type='turbulence' baseFrequency='0.04' numOctaves='1' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23pigskin)' opacity='1'/%3E%3C/svg%3E")`,
        }}
      />

      <div className="flex min-h-screen relative z-10">
        {/* Sidebar */}
        <aside className="hidden lg:flex w-64 flex-col border-r-2 border-[#1a3348] bg-[#234058] px-6 py-8 shadow-2xl relative overflow-hidden">
          <div className="absolute inset-0 opacity-[0.1] pointer-events-none mix-blend-overlay bg-repeat"
            style={{ backgroundImage: `url("data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='sidebarSkin'%3E%3CfeTurbulence type='turbulence' baseFrequency='0.05' numOctaves='1' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23sidebarSkin)' opacity='1'/%3E%3C/svg%3E")` }} />
          <div className="mb-8 relative z-10">
            <Link href="/admin" className="flex items-center gap-3 group">
              <div className="w-10 h-10 bg-[#8C302C] rounded-sm flex items-center justify-center shadow-lg border-2 border-[#1a3348]">
                <Ticket size={20} className="text-[#F1EEE6]" />
              </div>
              <div>
                <div className="text-xl font-black text-[#F1EEE6] font-mono tracking-tight">
                  FAST<span className="text-[#8C302C]">6</span>
                </div>
                <div className="text-[10px] font-bold uppercase tracking-[0.2em] text-[#A2877D]">
                  admin center
                </div>
              </div>
            </Link>
          </div>
          <nav className="flex flex-col gap-1 flex-1 relative z-10">
            {adminNav.map((item) => {
              const active = isActive(item.href);
              const Icon = item.icon;
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`flex items-center gap-3 px-4 py-3 rounded-r-full transition-all duration-200 border-l-4 ${
                    active
                      ? "bg-[#1a3348] border-[#A2877D] text-[#F1EEE6] shadow-md"
                      : "border-transparent text-[#8faec7] hover:bg-[#1a3348]/50 hover:text-[#F1EEE6]"
                  }`}
                >
                  <Icon size={18} />
                  <span className="text-sm font-bold tracking-widest uppercase font-mono">
                    {item.label}
                  </span>
                </Link>
              );
            })}
          </nav>
          <div className="mt-6 border-t border-[#1a3348] pt-4 space-y-2 relative z-10">
            <Link
              href="/"
              className="block text-xs font-bold text-[#8faec7] uppercase tracking-wider hover:text-[#F1EEE6] transition font-mono"
            >
              ← Back to dashboard
            </Link>
            <button
              onClick={handleLogout}
              className="flex items-center gap-2 text-xs font-bold text-[#8faec7] uppercase tracking-wider hover:text-[#F1EEE6] transition font-mono"
            >
              <LogOut size={14} />
              Sign out
            </button>
          </div>
        </aside>

        {/* Main */}
        <main className="flex-1 px-6 py-10 lg:px-10">
          <div className="mx-auto flex w-full max-w-6xl flex-col gap-8">
            {/* Mobile nav */}
            <div className="lg:hidden flex flex-col gap-4 rounded-lg border-2 border-[#d1d5db] bg-[#F1EEE6] px-5 py-4">
              <div className="flex justify-between items-center">
                <div>
                  <div className="text-lg font-black text-[#234058] font-mono">
                    FAST<span className="text-[#8C302C]">6</span> Admin
                  </div>
                  <div className="text-[0.6rem] uppercase tracking-[0.3em] text-[#A2877D] font-mono">
                    admin center
                  </div>
                </div>
                <Link href="/" className="text-xs font-bold text-[#78716c] uppercase tracking-wider font-mono">
                  ← Public
                </Link>
              </div>
              <nav className="flex flex-wrap gap-2 text-xs uppercase tracking-[0.2em] font-mono">
                {adminNav.map((item) => {
                  const active = isActive(item.href);
                  return (
                    <Link
                      key={item.href}
                      href={item.href}
                      className={`rounded-full border px-3 py-1.5 transition font-bold ${
                        active
                          ? "border-[#A2877D] bg-[#234058]/10 text-[#234058]"
                          : "border-[#d1d5db] text-[#78716c] hover:border-[#A2877D]"
                      }`}
                    >
                      {item.label}
                    </Link>
                  );
                })}
              </nav>
            </div>
            {children}
          </div>
        </main>
      </div>
    </div>
  );
}
