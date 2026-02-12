import ErrorBanner from "@/components/ui/ErrorBanner";
import Badge from "@/components/ui/Badge";
import AdminRegradeButton from "@/components/admin/AdminRegradeButton";
import AdminGradePendingButton from "@/components/admin/AdminGradePendingButton";
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
          <p className="text-xs font-bold uppercase tracking-[0.3em] text-[#78716c] font-mono">
            admin · grading
          </p>
          <h1 className="mt-2 text-2xl font-black tracking-widest text-[#234058] uppercase font-mono">
            Grading
          </h1>
          <p className="mt-2 text-sm text-[#78716c] font-mono">
            Grade picks and track grading progress.
          </p>
        </div>
        <Badge
          label={g.ungraded_picks > 0 ? `${g.ungraded_picks} pending` : "All graded"}
          tone={g.ungraded_picks > 0 ? "warning" : "success"}
        />
      </header>

      {/* Progress overview */}
      <div className="rounded-lg border-2 border-[#d1d5db] bg-[#fff] p-6 shadow-sm">
        <h2 className="mb-4 text-sm font-black uppercase tracking-[0.15em] text-[#234058] font-mono">
          Season {g.season} Progress
        </h2>
        <div className="mb-4 flex items-center gap-4">
          <div className="h-3 flex-1 overflow-hidden rounded-full bg-[#d1d5db]">
            <div
              className="h-full rounded-full bg-[#8C302C] transition-all"
              style={{ width: `${g.grading_progress}%` }}
            />
          </div>
          <span className="text-sm font-bold text-[#234058] font-mono">
            {g.grading_progress}%
          </span>
        </div>
        <div className="grid grid-cols-3 gap-4 text-center">
          <div>
            <p className="text-2xl font-black text-[#234058] font-mono">
              {g.total_picks}
            </p>
            <p className="text-[10px] font-bold uppercase tracking-wider text-[#78716c] font-mono">Total picks</p>
          </div>
          <div>
            <p className="text-2xl font-black text-[#15803d] font-mono">
              {g.graded_picks}
            </p>
            <p className="text-[10px] font-bold uppercase tracking-wider text-[#78716c] font-mono">Graded</p>
          </div>
          <div>
            <p className="text-2xl font-black text-[#A2877D] font-mono">
              {g.ungraded_picks}
            </p>
            <p className="text-[10px] font-bold uppercase tracking-wider text-[#78716c] font-mono">Pending</p>
          </div>
        </div>
      </div>

      {g.ungraded_picks === 0 ? (
        <div className="flex flex-col items-center justify-center gap-3 rounded-lg border-2 border-[#d1d5db] bg-[#fff] py-16 text-center shadow-sm">
          <div className="text-4xl">✅</div>
          <p className="text-lg font-bold text-[#234058] font-mono">All caught up!</p>
          <p className="text-sm text-[#78716c] font-mono">
            All picks for season {g.season} have been graded.
          </p>
          <p className="mt-2 text-xs text-[#78716c] font-mono">
            Use Re-grade all picks if TD data or grading logic has changed.
          </p>
          <AdminRegradeButton season={g.season} />
        </div>
      ) : (
        <div className="space-y-5">
          <div className="rounded-lg border-2 border-[#8C302C] bg-[#8C302C]/5 p-5">
            <p className="text-xs font-bold uppercase tracking-[0.2em] text-[#8C302C] font-mono">
              Grade pending picks
            </p>
            <p className="mt-2 text-sm text-[#234058] font-mono">
              Auto-grade only the {g.ungraded_picks} ungraded pick{g.ungraded_picks === 1 ? "" : "s"} for this season. Existing grades are not changed.
            </p>
            <AdminGradePendingButton season={g.season} pendingCount={g.ungraded_picks} />
          </div>
          <div className="rounded-lg border-2 border-[#d1d5db] bg-[#fff] p-5 shadow-sm">
            <p className="text-xs font-bold uppercase tracking-[0.2em] text-[#234058] font-mono">
              Re-grade all picks
            </p>
            <p className="mt-2 text-sm text-[#78716c] font-mono">
              Re-run auto-grading on all picks for this season. Use when TD data or grading logic has changed.
            </p>
            <AdminRegradeButton season={g.season} />
          </div>
          <div className="rounded-lg border-2 border-[#A2877D] bg-[#A2877D]/10 p-5">
            <p className="text-xs font-bold uppercase tracking-[0.2em] text-[#8C302C] font-mono">
              Batch grading
            </p>
            <p className="mt-2 text-sm text-[#234058] font-mono">
              Batch grading via the API: POST to{" "}
            <code className="rounded bg-[#234058]/10 px-1.5 py-0.5 text-xs font-mono text-[#234058] border border-[#d1d5db]">
              /api/admin/batch-grade
            </code>{" "}
            with an array of grade objects. See the{" "}
            <a
              href={`${process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000"}/docs`}
              target="_blank"
              rel="noopener noreferrer"
              className="underline font-bold text-[#8C302C] hover:text-[#234058]"
            >
              API docs
            </a>{" "}
            for details.
          </p>
          </div>
        </div>
      )}
    </>
  );
}
