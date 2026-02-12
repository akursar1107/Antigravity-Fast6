import DashboardLayoutWrapper from "@/components/layout/DashboardLayoutWrapper";

export default function AboutPage() {
  return (
    <DashboardLayoutWrapper>
      <div className="flex flex-col gap-8">
        <div>
          <h1 className="text-3xl font-black tracking-widest text-[#234058] uppercase font-mono">
            About Fast6
          </h1>
          <p className="mt-4 text-lg text-[#44403c] font-mono">
            The ultimate NFL first touchdown scorer prediction platform for friend groups
          </p>
        </div>

        <div className="grid gap-6 md:grid-cols-2">
          <div className="rounded-lg border-2 border-[#d1d5db] bg-[#fff] p-6 shadow-sm">
            <h2 className="text-sm font-black tracking-widest uppercase text-[#234058] font-mono">
              What is Fast6?
            </h2>
            <p className="mt-3 text-sm text-[#44403c] font-mono">
              Fast6 is a prediction platform where friends compete to correctly pick which player will score the first touchdown in each NFL game. Compete across seasons, track your performance, and climb the leaderboard with real-time analytics and insights.
            </p>
          </div>

          <div className="rounded-lg border-2 border-[#d1d5db] bg-[#fff] p-6 shadow-sm">
            <h2 className="text-sm font-black tracking-widest uppercase text-[#234058] font-mono">
              Key Features
            </h2>
            <ul className="mt-3 space-y-2 text-sm text-[#44403c] font-mono">
              <li>✓ Real-time leaderboard tracking</li>
              <li>✓ Advanced analytics & ROI tracking</li>
              <li>✓ Player performance insights</li>
              <li>✓ Season-long competitions</li>
              <li>✓ Defensive matchup analysis</li>
            </ul>
          </div>

          <div className="rounded-lg border-2 border-[#d1d5db] bg-[#fff] p-6 shadow-sm">
            <h2 className="text-sm font-black tracking-widest uppercase text-[#234058] font-mono">
              How It Works
            </h2>
            <ol className="mt-3 space-y-2 text-sm text-[#44403c] font-mono">
              <li>1. Make your first TD predictions each week</li>
              <li>2. Games are played and results are automatically graded</li>
              <li>3. Earn points and track your ROI</li>
              <li>4. Compete against friends throughout the season</li>
            </ol>
          </div>

          <div className="rounded-lg border-2 border-[#d1d5db] bg-[#fff] p-6 shadow-sm">
            <h2 className="text-sm font-black tracking-widest uppercase text-[#234058] font-mono">
              Scoring System
            </h2>
            <div className="mt-3 space-y-2 text-sm text-[#44403c] font-mono">
              <p>
                <span className="font-bold text-[#234058]">First TD:</span> 3 points
              </p>
              <p>
                <span className="font-bold text-[#234058]">Any-Time TD:</span> 1 point
              </p>
              <p className="mt-2 text-xs text-[#78716c]">
                Track your return on investment (ROI) and win percentage across the season.
              </p>
            </div>
          </div>
        </div>

        <div className="rounded-lg border-2 border-[#d1d5db] bg-[#F1EEE6] p-6 text-center">
          <p className="text-sm text-[#44403c] font-mono">
            Built with Next.js, FastAPI, and real NFL data. Deployed and ready to compete.
          </p>
          <p className="mt-2 text-xs text-[#78716c] font-mono">
            Season 2025 • Version 1.0
          </p>
        </div>
      </div>
    </DashboardLayoutWrapper>
  );
}
