"use client";

import { useState } from "react";
import { updateUserBaseBet } from "@/lib/api";
import { useRouter } from "next/navigation";

interface BaseBetFormProps {
  userId: number;
  currentBaseBet: number | null;
}

export default function BaseBetForm({
  userId,
  currentBaseBet,
}: BaseBetFormProps) {
  const [value, setValue] = useState(
    currentBaseBet != null ? String(currentBaseBet) : "1"
  );
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<{ type: "success" | "error"; text: string } | null>(null);
  const router = useRouter();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const num = parseFloat(value);
    if (isNaN(num) || num < 0.1 || num > 10000) {
      setMessage({ type: "error", text: "Enter a value between 0.1 and 10000" });
      return;
    }
    setSaving(true);
    setMessage(null);
    const res = await updateUserBaseBet(userId, num);
    setSaving(false);
    if (res.ok) {
      setMessage({ type: "success", text: "Base bet updated. Run Recalculate stats in Admin to update ROI." });
      router.refresh();
    } else {
      setMessage({ type: "error", text: res.error.message });
    }
  };

  return (
    <form onSubmit={handleSubmit} className="flex flex-wrap items-end gap-2">
      <div>
        <label
          htmlFor="base-bet"
          className="block text-[10px] font-bold uppercase tracking-wider text-[#7D6E63] font-mono mb-1"
        >
          Base bet ($)
        </label>
        <input
          id="base-bet"
          type="number"
          min={0.1}
          max={10000}
          step="any"
          value={value}
          onChange={(e) => setValue(e.target.value)}
          className="w-24 rounded border border-[#8B7355]/60 bg-white px-2 py-1.5 text-sm font-mono text-[#234058] focus:border-[#234058] focus:outline-none focus:ring-1 focus:ring-[#234058]"
          disabled={saving}
        />
      </div>
      <button
        type="submit"
        disabled={saving}
        className="rounded border-2 border-[#234058] bg-[#234058] px-3 py-1.5 text-xs font-bold uppercase tracking-wider text-white transition hover:bg-[#1a2d3d] disabled:opacity-50"
      >
        {saving ? "Saving…" : "Save"}
      </button>
      {message && (
        <p
          className={`w-full text-xs font-mono ${
            message.type === "success" ? "text-[#15803d]" : "text-[#8C302C]"
          }`}
        >
          {message.text}
        </p>
      )}
    </form>
  );
}
