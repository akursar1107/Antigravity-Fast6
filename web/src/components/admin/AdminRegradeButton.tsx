"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { regradeSeasonAction } from "@/app/admin/actions";

export default function AdminRegradeButton({ season }: { season: number }) {
  const [status, setStatus] = useState<"idle" | "loading" | "success" | "error">("idle");
  const [message, setMessage] = useState("");
  const router = useRouter();

  async function handleRegrade() {
    setStatus("loading");
    setMessage("");
    const res = await regradeSeasonAction(season);
    if (res.ok && res.data) {
      setStatus("success");
      if (res.data.error) {
        setMessage(res.data.error);
      } else {
        setMessage(
          `Re-graded ${res.data.graded_picks} picks (cleared ${res.data.results_cleared} previous results)`
        );
        router.refresh();
      }
    } else {
      setStatus("error");
      setMessage(res.error ?? "Regrade failed");
    }
  }

  return (
    <div className="mt-4">
      <button
        type="button"
        onClick={handleRegrade}
        disabled={status === "loading"}
        className="rounded border-2 border-[#234058] bg-[#234058] px-4 py-2 text-sm font-bold uppercase tracking-wider text-[#F1EEE6] transition hover:bg-[#1a3348] disabled:opacity-50 disabled:cursor-not-allowed font-mono"
      >
        {status === "loading" ? "Re-grading…" : "Re-grade all picks"}
      </button>
      {message && (
        <p
          className={`mt-2 text-sm font-mono ${
            status === "error" ? "text-[#8C302C]" : "text-[#15803d]"
          }`}
        >
          {message}
        </p>
      )}
    </div>
  );
}
