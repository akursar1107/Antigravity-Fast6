import DashboardLayout from "@/components/layout/DashboardLayout";
import Badge from "@/components/ui/Badge";
import ChartCard from "@/components/ui/ChartCard";
import StatCard from "@/components/ui/StatCard";

export default function Home() {
  return (
    <DashboardLayout>
      <header className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <p className="text-xs uppercase tracking-[0.3em] text-slate-500">
            fast6 analytics
          </p>
          <h1 className="mt-2 text-3xl font-semibold text-slate-50">
            Weekly overview
          </h1>
          <p className="mt-2 text-sm text-slate-400">
            Track picks, ROI, and player trends in one place.
          </p>
        </div>
        <Badge label="Season 2025" tone="info" />
      </header>

      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <StatCard label="Total picks" value="128" helper="All active weeks" />
        <StatCard label="Accuracy" value="42%" helper="Across graded picks" />
        <StatCard label="ROI" value="+18.4" helper="Units on season" />
        <StatCard label="Best week" value="Week 8" helper="12 correct picks" />
      </section>

      <section className="grid gap-6 lg:grid-cols-[2fr,1fr]">
        <ChartCard
          title="ROI trend"
          subtitle="Season performance by week"
        >
          <div className="h-56 rounded-xl border border-dashed border-slate-700/70 bg-slate-950/40" />
        </ChartCard>
        <ChartCard title="Hot players" subtitle="Most selected scorers">
          <ul className="space-y-3 text-sm text-slate-300">
            <li className="flex items-center justify-between">
              <span>Tyreek Hill</span>
              <span className="text-slate-400">6 picks</span>
            </li>
            <li className="flex items-center justify-between">
              <span>Christian McCaffrey</span>
              <span className="text-slate-400">5 picks</span>
            </li>
            <li className="flex items-center justify-between">
              <span>A.J. Brown</span>
              <span className="text-slate-400">4 picks</span>
            </li>
          </ul>
        </ChartCard>
      </section>
    </DashboardLayout>
  );
}
