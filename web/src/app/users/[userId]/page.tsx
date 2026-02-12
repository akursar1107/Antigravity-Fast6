import Link from "next/link";
import { notFound } from "next/navigation";
import DashboardLayoutWrapper from "@/components/layout/DashboardLayoutWrapper";
import ErrorBanner from "@/components/ui/ErrorBanner";
import TicketStub from "@/components/ui/TicketStub";
import BaseBetForm from "@/components/users/BaseBetForm";
import ReceiptPicksList from "@/components/users/ReceiptPicksList";
import {
  getUserStatsServer,
  getUserGradedPicksServer,
  getUserServer,
  getCurrentUserServer,
} from "@/lib/api";
import { getServerToken } from "@/lib/server-token";

const CURRENT_SEASON = parseInt(process.env.NEXT_PUBLIC_CURRENT_SEASON ?? "2025", 10);

export default async function UserProfilePage({
  params,
}: {
  params: Promise<{ userId: string }>;
}) {
  const { userId } = await params;
  const id = parseInt(userId, 10);
  if (isNaN(id)) notFound();

  const token = await getServerToken(
    process.env.NEXT_PUBLIC_TEST_USERNAME ?? "Anders"
  );
  if (!token) {
    return (
      <DashboardLayoutWrapper>
        <ErrorBanner message="Failed to authenticate with backend" />
      </DashboardLayoutWrapper>
    );
  }

  const [statsResponse, picksResponse, userResponse, currentUserResponse] =
    await Promise.all([
      getUserStatsServer(id, token),
      getUserGradedPicksServer(id, token),
      getUserServer(id, token),
      getCurrentUserServer(token),
    ]);

  const isOwnProfile =
    currentUserResponse.ok && currentUserResponse.data.id === id;
  const user = userResponse.ok ? userResponse.data : null;

  if (!statsResponse.ok) {
    if (statsResponse.error.status === 404) notFound();
    return (
      <DashboardLayoutWrapper>
        <ErrorBanner
          title="Cannot load profile"
          message={statsResponse.error.message}
        />
      </DashboardLayoutWrapper>
    );
  }

  const s = statsResponse.data;
  const allPicks = picksResponse.ok ? picksResponse.data : [];
  const picks = allPicks.filter(
    (p) => p.season === CURRENT_SEASON
  );
  const displayPicks = picks.length > 0 ? picks : allPicks;

  return (
    <DashboardLayoutWrapper>
      <div className="flex flex-col gap-6">
        <Link
          href="/leaderboard"
          className="text-sm font-bold uppercase tracking-wider text-[#78716c] hover:text-[#234058] font-mono transition inline-flex items-center gap-2"
        >
          ← Leaderboard
        </Link>

        {/* Main ticket stub: agent header */}
        <TicketStub tearLine={75}>
          <div className="p-6 sm:p-8">
            <div className="flex flex-col sm:flex-row sm:items-end sm:justify-between gap-4">
              <div>
                <p className="text-[10px] font-bold uppercase tracking-[0.4em] text-[#7D6E63] font-mono">
                  Fast6 ticket office · agent stub
                </p>
                <h1 className="mt-2 text-2xl sm:text-3xl font-black tracking-[0.15em] text-[#234058] uppercase font-mono drop-shadow-sm">
                  {s.user_name}
                </h1>
                <div className="mt-2 flex flex-wrap items-center gap-2">
                  <span className="inline-block rounded border border-[#8B7355]/60 bg-[#F5F0E8] px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider text-[#7D6E63] font-mono">
                    Season {CURRENT_SEASON}
                  </span>
                  <span className="text-[#8C302C] font-mono text-xs font-bold">
                    #{String(id).padStart(3, "0")}
                  </span>
                </div>
              </div>
              <div className="text-right border-t sm:border-t-0 sm:border-l-2 border-dashed border-[#8B7355]/50 pt-4 sm:pt-0 sm:pl-6 sm:ml-4">
                <p className="text-[10px] font-bold uppercase tracking-[0.25em] text-[#7D6E63] font-mono">
                  Total pts
                </p>
                <p className="mt-1 text-2xl font-black text-[#234058] font-mono tabular-nums">
                  {s.total_points}
                </p>
              </div>
            </div>
          </div>
        </TicketStub>

        {/* Stat stubs row */}
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <TicketStub compact>
            <div className="p-4">
              <p className="text-[10px] font-bold uppercase tracking-[0.2em] text-[#7D6E63] font-mono">
                ROI
              </p>
              <p
                className={`mt-1 text-xl font-black font-mono tabular-nums ${
                  s.roi_dollars >= 0 ? "text-[#15803d]" : "text-[#8C302C]"
                }`}
              >
                ${s.roi_dollars >= 0 ? "+" : ""}
                {s.roi_dollars.toFixed(1)}
              </p>
            </div>
          </TicketStub>
          <TicketStub compact>
            <div className="p-4">
              <p className="text-[10px] font-bold uppercase tracking-[0.2em] text-[#7D6E63] font-mono">
                Record
              </p>
              <p className="mt-1 text-xl font-black text-[#44403c] font-mono tabular-nums">
                {s.correct_picks}-{s.total_picks - s.correct_picks}
              </p>
            </div>
          </TicketStub>
          <TicketStub compact>
            <div className="p-4">
              <p className="text-[10px] font-bold uppercase tracking-[0.2em] text-[#7D6E63] font-mono">
                Win %
              </p>
              <p className="mt-1 text-xl font-black text-[#44403c] font-mono tabular-nums">
                {s.win_percentage.toFixed(0)}%
              </p>
            </div>
          </TicketStub>
          <TicketStub compact>
            <div className="p-4">
              <p className="text-[10px] font-bold uppercase tracking-[0.2em] text-[#7D6E63] font-mono">
                Avg / pick
              </p>
              <p className="mt-1 text-xl font-black text-[#234058] font-mono tabular-nums">
                {s.avg_points_per_pick.toFixed(2)}
              </p>
            </div>
          </TicketStub>
        </div>

        {/* Details ticket stub */}
        <TicketStub tearLine={65}>
          <div className="p-6">
            <h2 className="text-[10px] font-bold uppercase tracking-[0.3em] text-[#7D6E63] font-mono">
              Stub details
            </h2>
            <div className="mt-4 grid gap-6 sm:grid-cols-2 lg:grid-cols-4 font-mono text-sm">
              <div className="flex justify-between sm:flex-col sm:justify-start gap-1 border-b border-dashed border-[#8B7355]/40 pb-3 sm:pb-0 sm:border-0">
                <span className="text-[#7D6E63] text-xs uppercase tracking-wider">
                  Weeks played
                </span>
                <span className="font-bold text-[#234058] tabular-nums">
                  {s.weeks_participated}
                </span>
              </div>
              <div className="flex justify-between sm:flex-col sm:justify-start gap-1 border-b border-dashed border-[#8B7355]/40 pb-3 sm:pb-0 sm:border-0">
                <span className="text-[#7D6E63] text-xs uppercase tracking-wider">
                  Total picks
                </span>
                <span className="font-bold text-[#234058] tabular-nums">
                  {s.total_picks}
                </span>
              </div>
              <div className="flex justify-between sm:flex-col sm:justify-start gap-1 border-b border-dashed border-[#8B7355]/40 pb-3 sm:pb-0 sm:border-0">
                <span className="text-[#7D6E63] text-xs uppercase tracking-wider">
                  First TD hits
                </span>
                <span className="font-bold text-[#234058] tabular-nums">
                  {s.correct_picks}
                </span>
              </div>
              <div className="flex justify-between sm:flex-col sm:justify-start gap-1">
                <span className="text-[#7D6E63] text-xs uppercase tracking-wider">
                  Anytime TD hits
                </span>
                <span className="font-bold text-[#234058] tabular-nums">
                  {s.any_time_td_hits ?? 0}
                </span>
              </div>
            </div>
            {isOwnProfile && (
              <div className="mt-6 pt-4 border-t border-dashed border-[#8B7355]/40">
                <p className="text-[10px] font-bold uppercase tracking-wider text-[#7D6E63] font-mono mb-2">
                  Your base bet
                </p>
                <p className="text-xs text-[#78716c] font-mono mb-2">
                  Amount ($) you bet per pick for ROI calculation. Affects
                  win/loss dollar amounts.
                </p>
                <BaseBetForm
                  userId={id}
                  currentBaseBet={user?.base_bet ?? null}
                />
              </div>
            )}
          </div>
        </TicketStub>

        {/* Wins & losses receipt */}
        <div>
          <h2 className="mb-3 text-[10px] font-bold uppercase tracking-[0.3em] text-[#7D6E63] font-mono">
            Picks · Wins & losses
          </h2>
          {!picksResponse.ok && (
            <ErrorBanner
              title="Could not load picks"
              message={picksResponse.error?.message ?? "Unknown error"}
            />
          )}
          <ReceiptPicksList
            picks={displayPicks}
            userName={s.user_name}
            season={displayPicks.length > 0 ? displayPicks[0]?.season ?? CURRENT_SEASON : CURRENT_SEASON}
          />
        </div>
      </div>
    </DashboardLayoutWrapper>
  );
}
