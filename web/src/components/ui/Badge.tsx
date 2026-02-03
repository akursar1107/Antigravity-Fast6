interface BadgeProps {
  label: string;
  tone?: "success" | "warning" | "danger" | "info";
}

const toneStyles: Record<NonNullable<BadgeProps["tone"]>, string> = {
  success: "bg-indigo-500/15 text-indigo-200 border-indigo-500/40",
  warning: "bg-slate-500/15 text-slate-200 border-slate-500/40",
  danger: "bg-indigo-500/20 text-indigo-100 border-indigo-400/50",
  info: "bg-indigo-500/15 text-indigo-200 border-indigo-500/40",
};

export default function Badge({ label, tone = "info" }: BadgeProps) {
  return (
    <span
      className={`inline-flex items-center rounded-full border px-3 py-1 text-xs uppercase tracking-[0.2em] ${
        toneStyles[tone]
      }`}
    >
      {label}
    </span>
  );
}
