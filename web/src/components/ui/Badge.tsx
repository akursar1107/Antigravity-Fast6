interface BadgeProps {
  label: string;
  tone?: "default" | "success" | "warning" | "danger" | "info";
}

const toneStyles: Record<NonNullable<BadgeProps["tone"]>, string> = {
  default: "bg-indigo-500/15 text-indigo-200 border-indigo-500/40",
  success: "bg-emerald-500/10 text-emerald-400 border-emerald-500/20",
  warning: "bg-amber-500/10 text-amber-400 border-amber-500/20",
  danger: "bg-red-500/10 text-red-400 border-red-500/20",
  info: "bg-blue-500/10 text-blue-400 border-blue-500/20",
};

export default function Badge({ label, tone = "default" }: BadgeProps) {
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
