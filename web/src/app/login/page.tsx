"use client";

import { useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import { Ticket } from "lucide-react";

function getBaseUrl(): string {
  return process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";
}

export default function LoginPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const redirectTo = searchParams.get("redirect") ?? "/admin";

  const [username, setUsername] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      const res = await fetch(`${getBaseUrl()}/api/v1/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username: username.trim() }),
      });

      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        setError(data.detail ?? "Invalid username");
        setLoading(false);
        return;
      }

      const data = (await res.json()) as { access_token: string };
      const token = data.access_token;

      // Set cookie via API route (server sets httpOnly cookie)
      const setRes = await fetch("/api/auth/set-token", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ token }),
      });

      if (!setRes.ok) {
        setError("Failed to save session");
        setLoading(false);
        return;
      }

      router.push(redirectTo);
      router.refresh();
    } catch {
      setError("Could not reach server");
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen bg-[#F1EEE6] text-[#234058] flex items-center justify-center p-4 relative overflow-hidden">
      {/* Pigskin background */}
      <div
        className="fixed inset-0 opacity-[0.12] pointer-events-none z-0 mix-blend-multiply bg-repeat"
        style={{
          backgroundImage: `url("data:image/svg+xml,%3Csvg viewBox='0 0 400 400' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='pigskin'%3E%3CfeTurbulence type='turbulence' baseFrequency='0.04' numOctaves='1' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23pigskin)' opacity='1'/%3E%3C/svg%3E")`,
        }}
      />

      <div className="w-full max-w-sm relative z-10">
        <div className="rounded-xl border-2 border-[#d1d5db] bg-[#fff] shadow-xl p-8">
          <div className="flex items-center gap-3 mb-8">
            <div className="w-12 h-12 bg-[#8C302C] rounded-sm flex items-center justify-center border-2 border-[#234058]">
              <Ticket size={24} className="text-[#F1EEE6]" />
            </div>
            <div>
              <h1 className="text-2xl font-black tracking-tight text-[#234058] font-mono">
                FAST<span className="text-[#8C302C]">6</span>
              </h1>
              <p className="text-xs font-bold uppercase tracking-[0.2em] text-[#8C302C] font-mono">
                Sign in
              </p>
            </div>
          </div>

          <form onSubmit={handleSubmit} className="space-y-6">
            <div>
              <label
                htmlFor="username"
                className="block text-xs font-bold uppercase tracking-wider text-[#78716c] font-mono mb-2"
              >
                Username
              </label>
              <input
                id="username"
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="Enter your name"
                autoComplete="username"
                autoFocus
                className="w-full px-4 py-3 rounded-lg border-2 border-[#d1d5db] bg-[#F1EEE6] text-[#234058] font-mono placeholder:text-[#78716c] focus:border-[#8C302C] focus:outline-none focus:ring-2 focus:ring-[#8C302C]/20"
                disabled={loading}
              />
            </div>

            {error && (
              <p className="text-sm text-[#8C302C] font-mono">{error}</p>
            )}

            <button
              type="submit"
              disabled={loading || !username.trim()}
              className="w-full py-3 rounded-lg bg-[#8C302C] text-[#F1EEE6] font-bold uppercase tracking-wider font-mono hover:bg-[#702420] disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {loading ? "Signing in…" : "Sign in"}
            </button>
          </form>

          <p className="mt-6 text-xs text-[#78716c] font-mono text-center">
            Friend group — no password. Enter your name as registered.
          </p>
        </div>

        <p className="mt-6 text-center">
          <Link
            href="/"
            className="text-sm font-mono text-[#78716c] hover:text-[#234058]"
          >
            ← Back to dashboard
          </Link>
        </p>
      </div>
    </div>
  );
}
