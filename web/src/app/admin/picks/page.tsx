import ErrorBanner from "@/components/ui/ErrorBanner";
import Badge from "@/components/ui/Badge";
import { getPicksServer, getUsersServer } from "@/lib/api";
import { getServerToken } from "@/lib/server-token";

export default async function AdminPicksPage() {
  const username = process.env.NEXT_PUBLIC_TEST_USERNAME ?? "Anders";
  const token = await getServerToken(username);

  if (!token) {
    return <ErrorBanner message="Failed to authenticate with backend" />;
  }

  const [picksRes, usersRes] = await Promise.all([
    getPicksServer(token),
    getUsersServer(token),
  ]);

  if (!picksRes.ok) {
    return (
      <ErrorBanner
        title="Admin access required"
        message="Could not load picks."
      />
    );
  }

  const picks = picksRes.data;
  const users = usersRes.ok ? usersRes.data : [];
  const userMap = new Map(users.map((u) => [u.id, u.name]));

  return (
    <>
      <header className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <p className="text-xs uppercase tracking-[0.3em] text-slate-500">
            admin · picks
          </p>
          <h1 className="mt-2 text-3xl font-semibold text-slate-50">
            All Picks
          </h1>
          <p className="mt-2 text-sm text-slate-400">
            View and manage all user picks across all weeks.
          </p>
        </div>
        <Badge label={`${picks.length} picks`} tone="info" />
      </header>

      {picks.length === 0 ? (
        <div className="flex flex-col items-center justify-center gap-3 rounded-2xl border border-slate-800 bg-slate-900/60 py-16 text-center">
          <div className="text-4xl">🏈</div>
          <p className="text-lg font-semibold text-slate-300">No picks yet</p>
          <p className="text-sm text-slate-500">
            Picks will appear here once users submit them.
          </p>
        </div>
      ) : (
        <div className="overflow-x-auto rounded-2xl border border-slate-800 bg-slate-900/60">
          <table className="w-full text-left text-sm" aria-label="All picks">
            <thead className="border-b border-slate-800 bg-slate-900/80">
              <tr>
                <th className="px-4 py-3 font-semibold uppercase tracking-[0.15em] text-slate-400">
                  ID
                </th>
                <th className="px-4 py-3 font-semibold uppercase tracking-[0.15em] text-slate-400">
                  User
                </th>
                <th className="px-4 py-3 font-semibold uppercase tracking-[0.15em] text-slate-400">
                  Week
                </th>
                <th className="px-4 py-3 font-semibold uppercase tracking-[0.15em] text-slate-400">
                  Team
                </th>
                <th className="px-4 py-3 font-semibold uppercase tracking-[0.15em] text-slate-400">
                  Player
                </th>
                <th className="px-4 py-3 text-right font-semibold uppercase tracking-[0.15em] text-slate-400">
                  Odds
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800">
              {picks.map((pick) => (
                <tr
                  key={pick.id}
                  className="transition hover:bg-slate-800/40"
                >
                  <td className="px-4 py-3 text-slate-500">{pick.id}</td>
                  <td className="px-4 py-3 font-medium text-slate-100">
                    {userMap.get(pick.user_id) ?? `User #${pick.user_id}`}
                  </td>
                  <td className="px-4 py-3 text-slate-300">
                    Week {pick.week_id}
                  </td>
                  <td className="px-4 py-3 text-slate-300">
                    {pick.team}
                  </td>
                  <td className="px-4 py-3 text-slate-100">
                    {pick.player_name}
                  </td>
                  <td className="px-4 py-3 text-right text-slate-300">
                    {pick.odds != null ? `+${pick.odds}` : "—"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </>
  );
}
