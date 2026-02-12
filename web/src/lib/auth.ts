/**
 * Server-side auth utilities.
 * Reads token from cookie for authenticated requests.
 */
import { cookies } from "next/headers";

export const AUTH_COOKIE_NAME = "fast6_auth_token";
const COOKIE_MAX_AGE = 60 * 60 * 24 * 30; // 30 days

/** Get token from auth cookie (server only). Returns null if not logged in. */
export async function getTokenFromSession(): Promise<string | null> {
  const cookieStore = await cookies();
  const token = cookieStore.get(AUTH_COOKIE_NAME)?.value;
  return token ?? null;
}

/** Set auth cookie (call from Server Action). */
export async function setAuthCookie(token: string): Promise<void> {
  const cookieStore = await cookies();
  cookieStore.set(AUTH_COOKIE_NAME, token, {
    httpOnly: true,
    secure: process.env.NODE_ENV === "production",
    sameSite: "lax",
    maxAge: COOKIE_MAX_AGE,
    path: "/",
  });
}

/** Clear auth cookie (logout). */
export async function clearAuthCookie(): Promise<void> {
  const cookieStore = await cookies();
  cookieStore.delete(AUTH_COOKIE_NAME);
}
