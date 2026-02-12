"use client";

import { useState } from "react";
import Link from "next/link";
import type { User } from "@/lib/api";

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
      const res = await fetch(`${baseUrl}/api/v1/users`, {
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
      const res = await fetch(`${baseUrl}/api/v1/users/${userId}`, {
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
      <div className="rounded-lg border-2 border-[#d1d5db] bg-[#fff] p-6 shadow-sm">
        <h2 className="mb-4 text-sm font-black uppercase tracking-[0.15em] text-[#234058] font-mono">
          Add User
        </h2>
        <div className="flex flex-wrap items-end gap-3">
          <div className="flex flex-col gap-1">
            <label className="text-[10px] font-bold uppercase tracking-wider text-[#78716c] font-mono">Name *</label>
            <input
              type="text"
              value={newName}
              onChange={(e) => setNewName(e.target.value)}
              placeholder="John Doe"
              className="rounded-lg border-2 border-[#d1d5db] bg-[#F1EEE6] px-3 py-2 text-sm text-[#234058] font-mono placeholder-[#78716c] focus:border-[#234058] focus:outline-none"
            />
          </div>
          <div className="flex flex-col gap-1">
            <label className="text-[10px] font-bold uppercase tracking-wider text-[#78716c] font-mono">Email</label>
            <input
              type="email"
              value={newEmail}
              onChange={(e) => setNewEmail(e.target.value)}
              placeholder="john@example.com"
              className="rounded-lg border-2 border-[#d1d5db] bg-[#F1EEE6] px-3 py-2 text-sm text-[#234058] font-mono placeholder-[#78716c] focus:border-[#234058] focus:outline-none"
            />
          </div>
          <label className="flex items-center gap-2 py-2 text-sm text-[#234058] font-mono font-bold">
            <input
              type="checkbox"
              checked={newIsAdmin}
              onChange={(e) => setNewIsAdmin(e.target.checked)}
              className="rounded border-2 border-[#d1d5db] text-[#8C302C] focus:ring-[#8C302C]"
            />
            Admin
          </label>
          <button
            type="button"
            onClick={createUser}
            className="rounded-lg bg-[#234058] px-4 py-2 text-sm font-bold text-[#F1EEE6] font-mono uppercase tracking-wider transition hover:bg-[#8C302C]"
          >
            Add user
          </button>
        </div>
      </div>

      {/* Status messages */}
      {status && (
        <div className="rounded-lg border-2 border-[#15803d] bg-[#15803d]/10 px-4 py-3 text-sm font-mono text-[#15803d] font-bold">
          {status}
        </div>
      )}
      {error && (
        <div className="rounded-lg border-2 border-[#8C302C] bg-[#8C302C]/10 px-4 py-3 text-sm font-mono text-[#8C302C] font-bold">
          {error}
        </div>
      )}

      {/* Users table */}
      <div className="overflow-x-auto rounded-lg border-2 border-[#d1d5db] bg-[#fff] shadow-sm">
        <table className="w-full text-left text-sm font-mono" aria-label="Users">
          <thead className="bg-[#f8fafc] border-b-2 border-[#d1d5db]">
            <tr>
              <th className="px-4 py-3 font-bold uppercase tracking-[0.15em] text-[#64748b] text-[10px]">ID</th>
              <th className="px-4 py-3 font-bold uppercase tracking-[0.15em] text-[#64748b] text-[10px]">Name</th>
              <th className="px-4 py-3 font-bold uppercase tracking-[0.15em] text-[#64748b] text-[10px]">Email</th>
              <th className="px-4 py-3 font-bold uppercase tracking-[0.15em] text-[#64748b] text-[10px]">Role</th>
              <th className="px-4 py-3 text-right font-bold uppercase tracking-[0.15em] text-[#64748b] text-[10px]">Actions</th>
            </tr>
          </thead>
          <tbody>
            {users.map((user) => (
              <tr
                key={user.id}
                className="border-b border-dashed border-[#e5e7eb] hover:bg-[#fff7ed] transition-colors"
              >
                <td className="px-4 py-3 text-[#78716c]">{user.id}</td>
                <td className="px-4 py-3">
                  <Link
                    href={`/admin/users/${user.id}`}
                    className="font-bold text-[#234058] underline-offset-2 hover:underline"
                  >
                    {user.name}
                  </Link>
                </td>
                <td className="px-4 py-3 text-[#44403c]">{user.email ?? "—"}</td>
                <td className="px-4 py-3">
                  {user.is_admin ? (
                    <span className="inline-flex items-center rounded-sm border-2 border-[#A2877D] bg-[#A2877D]/10 px-2 py-0.5 text-[10px] font-bold text-[#A2877D] uppercase tracking-wider">
                      Admin
                    </span>
                  ) : (
                    <span className="text-[10px] font-bold text-[#78716c] uppercase tracking-wider">Member</span>
                  )}
                </td>
                <td className="px-4 py-3 text-right">
                  <button
                    type="button"
                    onClick={() => deleteUser(user.id, user.name)}
                    className="rounded-lg border-2 border-[#8C302C]/40 px-3 py-1 text-[10px] font-bold text-[#8C302C] uppercase tracking-wider transition hover:bg-[#8C302C]/10"
                  >
                    Delete
                  </button>
                </td>
              </tr>
            ))}
            {users.length === 0 && (
              <tr>
                <td colSpan={5} className="px-4 py-8 text-center text-[#78716c] font-mono">
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
