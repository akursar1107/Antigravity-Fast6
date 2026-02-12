import ErrorBanner from "@/components/ui/ErrorBanner";
import Badge from "@/components/ui/Badge";
import { getUsersServer } from "@/lib/api";
import { getServerToken } from "@/lib/server-token";
import UserActions from "./UserActions";

export default async function AdminUsersPage() {
  const username = process.env.NEXT_PUBLIC_TEST_USERNAME ?? "Anders";
  const token = await getServerToken(username);

  if (!token) {
    return <ErrorBanner message="Failed to authenticate with backend" />;
  }

  const usersRes = await getUsersServer(token);

  if (!usersRes.ok) {
    return (
      <ErrorBanner
        title="Admin access required"
        message="Could not load users."
      />
    );
  }

  const users = usersRes.data;

  return (
    <>
      <header className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <p className="text-xs font-bold uppercase tracking-[0.3em] text-[#78716c] font-mono">
            admin · users
          </p>
          <h1 className="mt-2 text-2xl font-black tracking-widest text-[#234058] uppercase font-mono">
            Manage Users
          </h1>
        </div>
        <Badge label={`${users.length} users`} tone="info" />
      </header>

      <UserActions token={token} initialUsers={users} />
    </>
  );
}
