import ErrorBanner from "@/components/ui/ErrorBanner";
import Badge from "@/components/ui/Badge";
import AdminPicksTable from "@/components/admin/AdminPicksTable";
import AdminAddPickSection from "@/components/admin/AdminAddPickSection";
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
    const status = picksRes.error?.status;
    const msg = picksRes.error?.message ?? "Could not load picks.";
    const hint =
      status === 403
        ? "Your session may have an old role. Sign out and sign back in to refresh your admin access."
        : status === 401
          ? "Session expired. Please sign in again."
          : "Ensure the backend is running and reachable.";
    return (
      <ErrorBanner
        title={status === 403 ? "Admin access required" : "Could not load picks"}
        message={`${msg} ${hint}`}
      />
    );
  }

  const picks = picksRes.data;
  const users = usersRes.ok ? usersRes.data : [];

  return (
    <>
      <header className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <p className="text-xs font-bold uppercase tracking-[0.3em] text-[#78716c] font-mono">
            admin · picks
          </p>
          <h1 className="mt-2 text-2xl font-black tracking-widest text-[#234058] uppercase font-mono">
            All Picks
          </h1>
          <p className="mt-2 text-sm text-[#78716c] font-mono">
            View and manage all user picks across all weeks.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <AdminAddPickSection token={token} />
          <Badge label={`${picks.length} picks`} tone="info" />
        </div>
      </header>

      {picks.length === 0 ? (
        <div className="flex flex-col items-center justify-center gap-3 rounded-lg border-2 border-[#d1d5db] bg-[#fff] py-16 text-center shadow-sm">
          <div className="text-4xl">🏈</div>
          <p className="text-lg font-bold text-[#234058] font-mono">No picks yet</p>
          <p className="text-sm text-[#78716c] font-mono">
            Picks will appear here once users submit them.
          </p>
        </div>
      ) : (
        <AdminPicksTable picks={picks} users={users} />
      )}
    </>
  );
}
