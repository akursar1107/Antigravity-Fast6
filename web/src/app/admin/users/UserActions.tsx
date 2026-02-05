"use client";

import { useState } from "react";
import type { User, ApiResponse } from "@/lib/api";

interface UserActionsProps {
  token: string;
  initialUsers: User[];
}

export default function UserActions({ token, initialUsers }: UserActionsProps) {
  const [users, setUsers] = useState<User[]>(initialUsers);
  const [newName, setNewName] = useState("");
  const [newEmail, setNewEmail] = useState("");
  const [newIsAdmin, setNewIsAdmin] = useState(false);
  const [status, setStatus] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const baseUrl =
    process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

  async function createUser() {
    if (!newName.trim()) return;
    setError(null);
    setStatus(null);

    try {
      const res = await fetch(`${baseUrl}/api/users`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          name: newName.trim(),
          email: newEmail.trim() || null,
          is_admin: newIsAdmin,
        }),
      });

      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        setError(body.detail ?? `Failed (HTTP ${res.status})`);
        return;
      }

      const user = (await res.json()) as User;
      setUsers((prev) => [...prev, user]);
      setNewName("");
      setNewEmail("");
      setNewIsAdmin(false);
      setStatus(`Created user "${user.name}"`);
    } catch {
      setError("Network error");
    }
  }

  async function deleteUser(userId: number, userName: string) {
    if (!confirm(`Delete user "${userName}"? This will also delete their picks.`))
      return;
    setError(null);
    setStatus(null);

    try {
      const res = await fetch(`${baseUrl}/api/users/${userId}`, {
        method: "DELETE",
        headers: { Authorization: `Bearer ${token}` },
      });

      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        setError(body.detail ?? `Failed (HTTP ${res.status})`);
        return;
      }

      setUsers((prev) => prev.filter((u) => u.id !== userId));
      setStatus(`Deleted user "${userName}"`);
    } catch {
      setError("Network error");
    }
  }

  return (
    <>
      {/* Create user form */}
      <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6">
        <h2 className="mb-4 text-sm font-semibold uppercase tracking-[0.15em] text-slate-400">
          Add User
        </h2>
        <div className="flex flex-wrap items-end gap-3">
          <div className="flex flex-col gap-1">
            <label className="text-xs text-slate-500">Name *</label>
            <input
              type="text"
              value={newName}
              onChange={(e) => setNewName(e.target.value)}
              placeholder="John Doe"
              className="rounded-lg border border-slate-700 bg-slate-800 px-3 py-2 text-sm text-slate-100 placeholder-slate-600 focus:border-indigo-500 focus:outline-none"
            />
          </div>
          <div className="flex flex-col gap-1">
            <label className="text-xs text-slate-500">Email</label>
            <input
              type="email"
              value={newEmail}
              onChange={(e) => setNewEmail(e.target.value)}
              placeholder="john@example.com"
              className="rounded-lg border border-slate-700 bg-slate-800 px-3 py-2 text-sm text-slate-100 placeholder-slate-600 focus:border-indigo-500 focus:outline-none"
            />
          </div>
          <label className="flex items-center gap-2 py-2 text-sm text-slate-300">
            <input
              type="checkbox"
              checked={newIsAdmin}
              onChange={(e) => setNewIsAdmin(e.target.checked)}
              className="rounded border-slate-600"
            />
            Admin
          </label>
          <button
            type="button"
            onClick={createUser}
            className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white transition hover:bg-indigo-500"
          >
            Add user
          </button>
        </div>
      </div>

      {/* Status messages */}
      {status && (
        <div className="rounded-lg border border-emerald-500/30 bg-emerald-900/20 px-4 py-3 text-sm text-emerald-300">
          {status}
        </div>
      )}
      {error && (
        <div className="rounded-lg border border-red-500/30 bg-red-900/20 px-4 py-3 text-sm text-red-300">
          {error}
        </div>
      )}

      {/* Users table */}
      <div className="overflow-x-auto rounded-2xl border border-slate-800 bg-slate-900/60">
        <table className="w-full text-left text-sm" aria-label="Users">
          <thead className="border-b border-slate-800 bg-slate-900/80">
            <tr>
              <th className="px-4 py-3 font-semibold uppercase tracking-[0.15em] text-slate-400">
                ID
              </th>
              <th className="px-4 py-3 font-semibold uppercase tracking-[0.15em] text-slate-400">
                Name
              </th>
              <th className="px-4 py-3 font-semibold uppercase tracking-[0.15em] text-slate-400">
                Email
              </th>
              <th className="px-4 py-3 font-semibold uppercase tracking-[0.15em] text-slate-400">
                Role
              </th>
              <th className="px-4 py-3 text-right font-semibold uppercase tracking-[0.15em] text-slate-400">
                Actions
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800">
            {users.map((user) => (
              <tr
                key={user.id}
                className="transition hover:bg-slate-800/40"
              >
                <td className="px-4 py-3 text-slate-500">{user.id}</td>
                <td className="px-4 py-3 font-medium text-slate-100">
                  {user.name}
                </td>
                <td className="px-4 py-3 text-slate-400">
                  {user.email ?? "—"}
                </td>
                <td className="px-4 py-3">
                  {user.is_admin ? (
                    <span className="inline-flex items-center rounded-full border border-amber-500/30 bg-amber-500/10 px-2 py-0.5 text-xs text-amber-400">
                      Admin
                    </span>
                  ) : (
                    <span className="text-xs text-slate-500">Member</span>
                  )}
                </td>
                <td className="px-4 py-3 text-right">
                  <button
                    type="button"
                    onClick={() => deleteUser(user.id, user.name)}
                    className="rounded-lg border border-red-500/30 px-3 py-1 text-xs text-red-400 transition hover:bg-red-500/10"
                  >
                    Delete
                  </button>
                </td>
              </tr>
            ))}
            {users.length === 0 && (
              <tr>
                <td
                  colSpan={5}
                  className="px-4 py-8 text-center text-slate-500"
                >
                  No users yet
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </>
  );
}
