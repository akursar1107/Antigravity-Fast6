import { NextResponse } from "next/server";
import { cookies } from "next/headers";

const AUTH_COOKIE_NAME = "fast6_auth_token";

export async function POST() {
  const cookieStore = await cookies();
  cookieStore.delete(AUTH_COOKIE_NAME);
  return NextResponse.json({ ok: true });
}
