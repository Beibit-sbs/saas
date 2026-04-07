import { NextResponse } from "next/server";

export async function POST() {
  const response = NextResponse.json({ ok: true });
  response.headers.set("cache-control", "no-store");
  const cookieOptions = {
    httpOnly: true,
    secure: process.env.NODE_ENV === "production",
    sameSite: "lax",
    maxAge: 0,
    path: "/",
  } as const;
  response.cookies.set("admin_token", "", cookieOptions);
  response.cookies.set("app_access_token", "", cookieOptions);
  return response;
}
