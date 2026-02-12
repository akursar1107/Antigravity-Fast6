interface BadgeProps {
  label: string;
  tone?: "default" | "success" | "warning" | "danger" | "info";
}

const toneStyles: Record<NonNullable<BadgeProps["tone"]>, string> = {
  default: "bg-[#234058]/10 text-[#234058] border-[#234058]/30",
  success: "bg-[#15803d]/10 text-[#15803d] border-[#15803d]/30",
  warning: "bg-[#A2877D]/20 text-[#A2877D] border-[#A2877D]/40",
  danger: "bg-[#8C302C]/10 text-[#8C302C] border-[#8C302C]/30",
  info: "bg-[#8faec7]/20 text-[#234058] border-[#8faec7]/40",
};

export default function Badge({ label, tone = "default" }: BadgeProps) {
  return (
    <span
      className={`inline-flex items-center rounded-sm border px-3 py-1 text-[10px] font-bold uppercase tracking-[0.2em] font-mono ${toneStyles[tone]}`}
    >
      {label}
    </span>
  );
}
