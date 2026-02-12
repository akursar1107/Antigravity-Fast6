/**
 * Server-side token provider for authentication.
 * This module handles JWT token management on the server side,
 * which bypasses localStorage (unavailable in server components).
 *
 * Priority: 1) Auth cookie (logged-in user) 2) Env fallback (dev mode)
 */

import { getTokenFromSession } from "./auth";

// Cache to store tokens per username during a request (for env fallback)
const tokenCache = new Map<string, { token: string; timestamp: number }>();
const CACHE_TTL = 5 * 60 * 1000; // 5 minutes

function getBaseUrl(): string {
  return process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";
}

/**
 * Get auth token for server-side API calls.
 * Uses session cookie first (if user logged in), then env fallback.
 */
export async function getServerToken(username?: string): Promise<string | null> {
  // 1. Check session cookie (user logged in via /login)
  const sessionToken = await getTokenFromSession();
  if (sessionToken) return sessionToken;

  // 2. Fallback: fetch token for username (dev mode via NEXT_PUBLIC_TEST_USERNAME)
  const fallbackUsername = username ?? process.env.NEXT_PUBLIC_TEST_USERNAME ?? "Phil";

  const cached = tokenCache.get(fallbackUsername);
  if (cached && Date.now() - cached.timestamp < CACHE_TTL) {
    return cached.token;
  }

  try {
    const url = `${getBaseUrl()}/api/v1/auth/login`;
    const response = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username: fallbackUsername }),
    });

    if (!response.ok) return null;

    const data = (await response.json()) as { access_token: string };
    const token = data.access_token;
    tokenCache.set(fallbackUsername, { token, timestamp: Date.now() });
    return token;
  } catch {
    return null;
  }
}
