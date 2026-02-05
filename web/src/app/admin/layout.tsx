"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import type { ReactNode } from "react";

const adminNav = [
  { href: "/admin", label: "Dashboard" },
  { href: "/admin/users", label: "Users" },
  { href: "/admin/picks", label: "Picks" },
  { href: "/admin/grading", label: "Grading" },
];

export default function AdminLayout({ children }: { children: ReactNode }) {
  const pathname = usePathname();

  function isActive(href: string): boolean {
    if (href === "/admin") return pathname === "/admin";
    return pathname.startsWith(href);
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      <div className="flex min-h-screen">
        {/* Sidebar */}
        <aside className="hidden w-64 flex-col border-r border-slate-800 bg-slate-950/80 px-6 py-8 lg:flex">
          <div className="mb-8">
            <div className="text-xl font-semibold text-slate-50">Fast6</div>
            <div className="text-xs uppercase tracking-[0.2em] text-amber-400">
              admin center
            </div>
          </div>
          <nav className="flex flex-col gap-1 text-sm">
            {adminNav.map((item) => {
              const active = isActive(item.href);
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`rounded-lg px-3 py-2 transition ${
                    active
                      ? "border-l-2 border-amber-400 bg-slate-900 font-medium text-slate-50"
                      : "text-slate-400 hover:bg-slate-900 hover:text-slate-200"
                  }`}
                >
                  {item.label}
                </Link>
              );
            })}
          </nav>
          <div className="mt-6 border-t border-slate-800 pt-4">
            <Link
              href="/"
              className="text-xs text-slate-500 transition hover:text-slate-300"
            >
              ← Back to public dashboard
            </Link>
          </div>
          <div className="mt-auto text-xs text-slate-500">Admin access only</div>
        </aside>

        {/* Mobile nav */}
        <main className="flex-1 px-6 py-10 lg:px-10">
          <div className="mx-auto flex w-full max-w-6xl flex-col gap-8">
            <div className="flex flex-col gap-4 rounded-2xl border border-slate-800 bg-slate-900/60 px-5 py-4 lg:hidden">
              <div className="flex items-center justify-between">
                <div>
                  <div className="text-lg font-semibold text-slate-50">Fast6</div>
                  <div className="text-[0.6rem] uppercase tracking-[0.3em] text-amber-400">
                    admin center
                  </div>
                </div>
                <Link href="/" className="text-xs text-slate-400 hover:text-slate-200">
                  ← Public
                </Link>
              </div>
              <nav className="flex flex-wrap gap-2 text-xs uppercase tracking-[0.2em] text-slate-400">
                {adminNav.map((item) => {
                  const active = isActive(item.href);
                  return (
                    <Link
                      key={item.href}
                      href={item.href}
                      className={`rounded-full border px-3 py-1 transition ${
                        active
                          ? "border-amber-400/60 bg-amber-500/10 text-slate-100"
                          : "border-slate-800 text-slate-300 hover:border-amber-400/60 hover:text-slate-100"
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
