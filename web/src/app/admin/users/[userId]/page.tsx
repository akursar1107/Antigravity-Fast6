import { notFound } from "next/navigation";
import ErrorBanner from "@/components/ui/ErrorBanner";
import Badge from "@/components/ui/Badge";
import AdminUserPicksEditor from "@/components/admin/AdminUserPicksEditor";
import {
  getUserServer,
  getAdminUserPicksWithResultsServer,
} from "@/lib/api";
import { getServerToken } from "@/lib/server-token";

export default async function AdminUserPicksPage({
  params,
}: {
  params: Promise<{ userId: string }>;
}) {
  const { userId } = await params;
  const id = parseInt(userId, 10);
  if (isNaN(id)) notFound();

  const username = process.env.NEXT_PUBLIC_TEST_USERNAME ?? "Anders";
  const token = await getServerToken(username);

  if (!token) {
    return <ErrorBanner message="Failed to authenticate with backend" />;
  }

  const [userRes, picksRes] = await Promise.all([
    getUserServer(id, token),
    getAdminUserPicksWithResultsServer(id, token),
  ]);

  if (!userRes.ok) {
    if (userRes.error?.status === 404) notFound();
    return (
      <ErrorBanner
        title="Cannot load user"
        message={userRes.error?.message ?? "Unknown error"}
      />
    );
  }

  if (!picksRes.ok) {
    return (
      <ErrorBanner
        title="Cannot load picks"
        message={picksRes.error?.message ?? "Unknown error"}
      />
    );
  }

  const user = userRes.data;
  const picks = picksRes.data;

  return (
    <>
      <header className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <p className="text-xs font-bold uppercase tracking-[0.3em] text-[#78716c] font-mono">
            admin · user picks
          </p>
          <h1 className="mt-2 text-2xl font-black tracking-widest text-[#234058] uppercase font-mono">
            {user.name}
          </h1>
          <p className="mt-2 text-sm text-[#78716c] font-mono">
            View and update picks for this user.
          </p>
        </div>
        <Badge label={`${picks.length} picks`} tone="info" />
      </header>

      <AdminUserPicksEditor
        picks={picks}
        userName={user.name}
        token={token}
      />
    </>
  );
}
