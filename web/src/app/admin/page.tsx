import ErrorBanner from "@/components/ui/ErrorBanner";
import StatCard from "@/components/ui/StatCard";
import Badge from "@/components/ui/Badge";
import AdminSyncButtons from "@/components/admin/AdminSyncButtons";
import { getAdminStatsServer } from "@/lib/api";
import { getServerToken } from "@/lib/server-token";

export default async function AdminDashboard() {
  const username = process.env.NEXT_PUBLIC_TEST_USERNAME ?? "Anders";
  const token = await getServerToken(username);

  if (!token) {
    return <ErrorBanner message="Failed to authenticate with backend" />;
  }

  const statsRes = await getAdminStatsServer(token);

  if (!statsRes.ok) {
    return (
      <ErrorBanner
        title="Admin access required"
        message={`Could not load admin stats (HTTP ${statsRes.error.status ?? "unknown"}). Make sure your account has admin privileges.`}
      />
    );
  }

  const s = statsRes.data.system_stats;

  return (
    <>
      <header className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <p className="text-xs font-bold uppercase tracking-[0.3em] text-[#78716c] font-mono">
            admin center
          </p>
          <h1 className="mt-2 text-2xl font-black tracking-widest text-[#234058] uppercase font-mono">
            Dashboard
          </h1>
          <p className="mt-2 text-sm text-[#78716c] font-mono">
            System overview and management tools.
          </p>
        </div>
        <Badge label="Admin" tone="warning" />
      </header>

      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <StatCard
          label="Total users"
          value={s.total_users}
          helper="Registered players"
        />
        <StatCard
          label="Total picks"
          value={s.total_picks}
          helper={`${s.graded_picks} graded · ${s.ungraded_picks} pending`}
        />
        <StatCard
          label="Grading progress"
          value={`${s.grading_progress}%`}
          helper={`${s.graded_picks}/${s.total_picks} picks graded`}
        />
        <StatCard
          label="Total weeks"
          value={s.total_seasons}
          helper="Across all seasons"
        />
      </section>

      {s.ungraded_picks > 0 && (
        <div className="rounded-lg border-2 border-[#A2877D] bg-[#A2877D]/10 p-5">
          <p className="text-xs font-bold uppercase tracking-[0.2em] text-[#8C302C] font-mono">
            Action needed
          </p>
          <p className="mt-2 text-sm text-[#234058] font-mono">
            {s.ungraded_picks} pick{s.ungraded_picks !== 1 ? "s" : ""} awaiting
            grading. Head to the{" "}
            <a
              href="/admin/grading"
              className="underline font-bold text-[#8C302C] hover:text-[#234058]"
            >
              Grading
            </a>{" "}
            tab to resolve.
          </p>
        </div>
      )}

      <section>
        <AdminSyncButtons />
      </section>
    </>
  );
}
