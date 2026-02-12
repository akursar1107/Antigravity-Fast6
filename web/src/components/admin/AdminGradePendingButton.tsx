"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { gradePendingPicksAction } from "@/app/admin/actions";

export default function AdminGradePendingButton({
  season,
  pendingCount,
}: {
  season: number;
  pendingCount: number;
}) {
  const [status, setStatus] = useState<"idle" | "loading" | "success" | "error">("idle");
  const [message, setMessage] = useState("");
  const router = useRouter();

  async function handleGradePending() {
    setStatus("loading");
    setMessage("");
    const res = await gradePendingPicksAction(season);
    if (res.ok && res.data) {
      setStatus("success");
      if (res.data.error) {
        setMessage(res.data.error);
      } else {
        setMessage(
          `Graded ${res.data.graded_picks} pending pick${res.data.graded_picks === 1 ? "" : "s"}`
        );
        router.refresh();
      }
    } else {
      setStatus("error");
      setMessage(res.error ?? "Grade pending failed");
    }
  }

  return (
    <div className="mt-4">
      <button
        type="button"
        onClick={handleGradePending}
        disabled={status === "loading" || pendingCount === 0}
        className="rounded border-2 border-[#8C302C] bg-[#8C302C] px-4 py-2 text-sm font-bold uppercase tracking-wider text-[#F1EEE6] transition hover:bg-[#6d2420] disabled:opacity-50 disabled:cursor-not-allowed font-mono"
      >
        {status === "loading" ? "Grading…" : "Grade pending picks"}
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
