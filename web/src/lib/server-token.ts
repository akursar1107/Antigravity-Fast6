/**
 * Server-side token provider for authentication.
 * This module handles JWT token management on the server side,
 * which bypasses localStorage (unavailable in server components).
 */

// Cache to store tokens per username during a request
const tokenCache = new Map<string, { token: string; timestamp: number }>();
const CACHE_TTL = 5 * 60 * 1000; // 5 minutes

function getBaseUrl(): string {
  // On server, use backend URL directly
  return process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";
}

export async function getServerToken(username: string): Promise<string | null> {
  // Check cache first
  const cached = tokenCache.get(username);
  if (cached && Date.now() - cached.timestamp < CACHE_TTL) {
    return cached.token;
  }

  try {
    const url = `${getBaseUrl()}/api/auth/login`;
    const response = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username }),
    });

    if (!response.ok) {
      return null;
    }

    const data = (await response.json()) as { access_token: string };
    const token = data.access_token;
    
    // Cache the token
    tokenCache.set(username, { token, timestamp: Date.now() });
    
    return token;
  } catch {
    return null;
  }
}
