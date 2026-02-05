import DashboardLayout from "@/components/layout/DashboardLayout";

export default function AboutPage() {
  return (
    <DashboardLayout>
      <div className="flex flex-col gap-8">
        <div>
          <h1 className="text-4xl font-bold text-slate-50">About Fast6</h1>
          <p className="mt-4 text-lg text-slate-300">
            The ultimate NFL first touchdown scorer prediction platform for friend groups
          </p>
        </div>

        <div className="grid gap-8 md:grid-cols-2">
          {/* About Section */}
          <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6">
            <h2 className="text-xl font-semibold text-slate-50">What is Fast6?</h2>
            <p className="mt-3 text-sm text-slate-400">
              Fast6 is a prediction platform where friends compete to correctly pick which player will score the first touchdown in each NFL game. Compete across seasons, track your performance, and climb the leaderboard with real-time analytics and insights.
            </p>
          </div>

          {/* Features Section */}
          <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6">
            <h2 className="text-xl font-semibold text-slate-50">Key Features</h2>
            <ul className="mt-3 space-y-2 text-sm text-slate-400">
              <li>✓ Real-time leaderboard tracking</li>
              <li>✓ Advanced analytics & ROI tracking</li>
              <li>✓ Player performance insights</li>
              <li>✓ Season-long competitions</li>
              <li>✓ Defensive matchup analysis</li>
            </ul>
          </div>

          {/* How It Works */}
          <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6">
            <h2 className="text-xl font-semibold text-slate-50">How It Works</h2>
            <ol className="mt-3 space-y-2 text-sm text-slate-400">
              <li>1. Make your first TD predictions each week</li>
              <li>2. Games are played and results are automatically graded</li>
              <li>3. Earn points and track your ROI</li>
              <li>4. Compete against friends throughout the season</li>
            </ol>
          </div>

          {/* Scoring Section */}
          <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6">
            <h2 className="text-xl font-semibold text-slate-50">Scoring System</h2>
            <div className="mt-3 space-y-2 text-sm text-slate-400">
              <p>
                <span className="font-semibold text-slate-200">First TD:</span> 3 points
              </p>
              <p>
                <span className="font-semibold text-slate-200">Any-Time TD:</span> 1 point
              </p>
              <p className="mt-2 text-xs">
                Track your return on investment (ROI) and win percentage across the season.
              </p>
            </div>
          </div>
        </div>

        {/* Footer Section */}
        <div className="rounded-2xl border border-slate-800 bg-slate-900/40 p-6 text-center">
          <p className="text-sm text-slate-400">
            Built with Next.js, FastAPI, and real NFL data. Deployed and ready to compete.
          </p>
          <p className="mt-2 text-xs text-slate-500">
            Season 2025 • Version 1.0
          </p>
        </div>
      </div>
    </DashboardLayout>
  );
}
