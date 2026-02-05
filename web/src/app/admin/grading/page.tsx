import ErrorBanner from "@/components/ui/ErrorBanner";
import Badge from "@/components/ui/Badge";
import { getServerToken } from "@/lib/server-token";
import type { GradingStatus } from "@/lib/api";
import { request } from "@/lib/api";

export default async function AdminGradingPage() {
  const username = process.env.NEXT_PUBLIC_TEST_USERNAME ?? "Anders";
  const season = parseInt(process.env.NEXT_PUBLIC_CURRENT_SEASON ?? "2025", 10);
  const token = await getServerToken(username);

  if (!token) {
    return <ErrorBanner message="Failed to authenticate with backend" />;
  }

  const gradingRes = await request<GradingStatus>(
    `/api/analytics/grading-status?season=${season}`,
    token
  );

  if (!gradingRes.ok) {
    return (
      <ErrorBanner
        title="Admin access required"
        message="Could not load grading status."
      />
    );
  }

  const g = gradingRes.data;

  return (
    <>
      <header className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <p className="text-xs uppercase tracking-[0.3em] text-slate-500">
            admin · grading
          </p>
          <h1 className="mt-2 text-3xl font-semibold text-slate-50">
            Grading
          </h1>
          <p className="mt-2 text-sm text-slate-400">
            Grade picks and track grading progress.
          </p>
        </div>
        <Badge
          label={g.ungraded_picks > 0 ? `${g.ungraded_picks} pending` : "All graded"}
          tone={g.ungraded_picks > 0 ? "warning" : "success"}
        />
      </header>

      {/* Progress overview */}
      <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6">
        <h2 className="mb-4 text-sm font-semibold uppercase tracking-[0.15em] text-slate-400">
          Season {g.season} Progress
        </h2>
        <div className="mb-4 flex items-center gap-4">
          <div className="h-3 flex-1 overflow-hidden rounded-full bg-slate-800">
            <div
              className="h-full rounded-full bg-gradient-to-r from-indigo-500 to-purple-500 transition-all"
              style={{ width: `${g.grading_progress}%` }}
            />
          </div>
          <span className="text-sm font-semibold text-slate-200">
            {g.grading_progress}%
          </span>
        </div>
        <div className="grid grid-cols-3 gap-4 text-center">
          <div>
            <p className="text-2xl font-semibold text-slate-100">
              {g.total_picks}
            </p>
            <p className="text-xs text-slate-500">Total picks</p>
          </div>
          <div>
            <p className="text-2xl font-semibold text-emerald-400">
              {g.graded_picks}
            </p>
            <p className="text-xs text-slate-500">Graded</p>
          </div>
          <div>
            <p className="text-2xl font-semibold text-amber-400">
              {g.ungraded_picks}
            </p>
            <p className="text-xs text-slate-500">Pending</p>
          </div>
        </div>
      </div>

      {g.ungraded_picks === 0 ? (
        <div className="flex flex-col items-center justify-center gap-3 rounded-2xl border border-slate-800 bg-slate-900/60 py-16 text-center">
          <div className="text-4xl">✅</div>
          <p className="text-lg font-semibold text-slate-300">All caught up!</p>
          <p className="text-sm text-slate-500">
            All picks for season {g.season} have been graded.
          </p>
        </div>
      ) : (
        <div className="rounded-2xl border border-amber-500/30 bg-amber-900/10 p-5">
          <p className="text-sm font-semibold uppercase tracking-[0.2em] text-amber-400">
            Batch grading
          </p>
          <p className="mt-2 text-sm text-amber-200/80">
            Batch grading via the API: POST to{" "}
            <code className="rounded bg-slate-800 px-1.5 py-0.5 text-xs text-amber-300">
              /api/admin/batch-grade
            </code>{" "}
            with an array of grade objects. See the{" "}
            <a
              href={`${process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000"}/docs`}
              target="_blank"
              rel="noopener noreferrer"
              className="underline hover:text-amber-100"
            >
              API docs
            </a>{" "}
            for details.
          </p>
        </div>
      )}
    </>
  );
}
