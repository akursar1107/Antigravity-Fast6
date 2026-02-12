"use client";

interface ErrorBannerProps {
  title?: string;
  message: string;
  actionLabel?: string;
  onAction?: () => void;
}

export default function ErrorBanner({
  title = "Unable to load data",
  message,
  actionLabel,
  onAction,
}: ErrorBannerProps) {
  return (
    <div className="flex flex-col gap-3 rounded-lg border-2 border-[#8C302C]/40 bg-[#8C302C]/10 p-5">
      <div>
        <p className="text-xs font-bold uppercase tracking-[0.2em] text-[#8C302C] font-mono">
          {title}
        </p>
        <p className="mt-2 text-sm text-[#234058] font-mono">{message}</p>
      </div>
      {actionLabel && onAction ? (
        <button
          type="button"
          onClick={onAction}
          className="w-fit rounded-sm border-2 border-[#8C302C]/60 px-4 py-2 text-xs font-bold uppercase tracking-[0.2em] text-[#8C302C] font-mono transition hover:bg-[#8C302C]/20"
        >
          {actionLabel}
        </button>
      ) : null}
    </div>
  );
}
