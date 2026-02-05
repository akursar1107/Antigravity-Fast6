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
    <div className="flex flex-col gap-3 rounded-2xl border border-red-500/30 bg-red-900/20 p-5 text-red-50">
      <div>
        <p className="text-sm font-semibold uppercase tracking-[0.2em] text-red-400">
          {title}
        </p>
        <p className="mt-2 text-sm text-red-300/90">{message}</p>
      </div>
      {actionLabel && onAction ? (
        <button
          type="button"
          onClick={onAction}
          className="w-fit rounded-full border border-red-400/60 px-4 py-2 text-xs font-semibold uppercase tracking-[0.2em] text-red-50 transition hover:bg-red-500/20"
        >
          {actionLabel}
        </button>
      ) : null}
    </div>
  );
}
