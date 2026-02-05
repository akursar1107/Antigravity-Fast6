import type { ReactNode } from "react";

interface StatCardProps {
  label: string;
  value: string | number;
  helper?: string;
  icon?: ReactNode;
}

export default function StatCard({ label, value, helper, icon }: StatCardProps) {
  return (
    <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-5 shadow-lg">
      <div className="flex items-center justify-between">
        <p className="text-xs uppercase tracking-[0.2em] text-slate-400">
          {label}
        </p>
        {icon ? <span className="text-slate-500">{icon}</span> : null}
      </div>
      <div className="mt-4 text-3xl font-semibold text-slate-50">
        {value}
      </div>
      {helper ? <p className="mt-2 text-sm text-slate-400">{helper}</p> : null}
    </div>
  );
}
