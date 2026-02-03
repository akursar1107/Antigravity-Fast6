import Link from "next/link";
import type { ReactNode } from "react";

interface DashboardLayoutProps {
  children: ReactNode;
}

const navItems = [
  { href: "/", label: "Overview" },
  { href: "/leaderboard", label: "Leaderboard" },
  { href: "/analytics", label: "Analytics" },
  { href: "/weeks/1", label: "Week" },
  { href: "/about", label: "About" },
];

export default function DashboardLayout({ children }: DashboardLayoutProps) {
  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      <div className="flex min-h-screen">
        <aside className="hidden w-64 flex-col border-r border-slate-800 bg-slate-950/80 px-6 py-8 lg:flex">
          <div className="mb-8">
            <div className="text-xl font-semibold text-slate-50">Fast6</div>
            <div className="text-xs uppercase tracking-[0.2em] text-slate-500">
              public dashboard
            </div>
          </div>
          <nav className="flex flex-col gap-2 text-sm">
            {navItems.map((item) => (
              <Link
                key={item.href}
                href={item.href}
                className="rounded-lg px-3 py-2 text-slate-300 transition hover:bg-slate-900 hover:text-slate-100"
              >
                {item.label}
              </Link>
            ))}
          </nav>
          <div className="mt-auto text-xs text-slate-500">
            Data updates weekly
          </div>
        </aside>
        <main className="flex-1 px-6 py-10 lg:px-10">
          <div className="mx-auto flex w-full max-w-6xl flex-col gap-8">
            <div className="flex flex-col gap-4 rounded-2xl border border-slate-800 bg-slate-900/60 px-5 py-4 lg:hidden">
              <div className="flex items-center justify-between">
                <div>
                  <div className="text-lg font-semibold text-slate-50">Fast6</div>
                  <div className="text-[0.6rem] uppercase tracking-[0.3em] text-slate-500">
                    public dashboard
                  </div>
                </div>
                <span className="text-xs text-slate-400">Season 2025</span>
              </div>
              <nav className="flex flex-wrap gap-2 text-xs uppercase tracking-[0.2em] text-slate-400">
                {navItems.map((item) => (
                  <Link
                    key={item.href}
                    href={item.href}
                    className="rounded-full border border-slate-800 px-3 py-1 text-slate-300 transition hover:border-indigo-400/60 hover:text-slate-100"
                  >
                    {item.label}
                  </Link>
                ))}
              </nav>
            </div>
            {children}
          </div>
        </main>
      </div>
    </div>
  );
}
