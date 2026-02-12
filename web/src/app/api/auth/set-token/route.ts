import { NextRequest, NextResponse } from "next/server";
import { cookies } from "next/headers";

const AUTH_COOKIE_NAME = "fast6_auth_token";
const COOKIE_MAX_AGE = 60 * 60 * 24 * 30; // 30 days

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const token = body.token as string;

    if (!token || typeof token !== "string") {
      return NextResponse.json(
        { error: "Token required" },
        { status: 400 }
      );
    }

    const cookieStore = await cookies();
    cookieStore.set(AUTH_COOKIE_NAME, token, {
      httpOnly: true,
      secure: process.env.NODE_ENV === "production",
      sameSite: "lax",
      maxAge: COOKIE_MAX_AGE,
      path: "/",
    });

    return NextResponse.json({ ok: true });
  } catch {
    return NextResponse.json({ error: "Invalid request" }, { status: 400 });
  }
}
