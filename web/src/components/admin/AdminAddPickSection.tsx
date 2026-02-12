"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Plus } from "lucide-react";
import type { Pick } from "@/lib/api";
import AdminAddPickWorkflow from "./AdminAddPickWorkflow";

type AdminAddPickSectionProps = {
  token: string;
};

export default function AdminAddPickSection({ token }: AdminAddPickSectionProps) {
  const [showWorkflow, setShowWorkflow] = useState(false);
  const router = useRouter();

  const handleSuccess = (_pick: Pick) => {
    router.refresh();
  };

  return (
    <>
      <button
        type="button"
        onClick={() => setShowWorkflow(true)}
        className="inline-flex items-center gap-2 rounded border-2 border-[#234058] bg-[#234058] px-4 py-2 text-sm font-mono font-bold text-[#F1EEE6] hover:bg-[#1a3348] transition-colors"
      >
        <Plus size={16} />
        Add Pick
      </button>
      {showWorkflow && (
        <AdminAddPickWorkflow
          token={token}
          onClose={() => setShowWorkflow(false)}
          onSuccess={handleSuccess}
        />
      )}
    </>
  );
}
