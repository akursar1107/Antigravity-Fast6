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
    <div className="flex flex-col gap-3 rounded-2xl border border-indigo-500/40 bg-indigo-500/10 p-5 text-indigo-50">
      <div>
        <p className="text-sm font-semibold uppercase tracking-[0.2em] text-indigo-200">
          {title}
        </p>
        <p className="mt-2 text-sm text-indigo-100/90">{message}</p>
      </div>
      {actionLabel && onAction ? (
        <button
          type="button"
          onClick={onAction}
          className="w-fit rounded-full border border-indigo-400/60 px-4 py-2 text-xs font-semibold uppercase tracking-[0.2em] text-indigo-50 transition hover:bg-indigo-500/20"
        >
          {actionLabel}
        </button>
      ) : null}
    </div>
  );
}
