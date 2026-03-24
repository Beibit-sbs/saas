import { NextResponse } from "next/server";
import { isJwtExpired, toSafeSession } from "@/shared/server/auth-session";

const API_BASE = process.env.API_BASE_URL ?? "http://localhost:8000";

export async function POST(request: Request) {
  const body = await request.json();

  const upstream = await fetch(`${API_BASE}/api/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });

  const data = await upstream.json();

  if (!upstream.ok) {
    return NextResponse.json(data, { status: upstream.status });
  }

  const token = String(data.access_token ?? "").trim();
  const session = token ? toSafeSession(token) : null;

  if (!token || !session || isJwtExpired(token)) {
    return NextResponse.json({ error: { detail: "Invalid auth session" } }, { status: 401 });
  }

  const response = NextResponse.json({ ok: true, ...session });
  response.headers.set("cache-control", "no-store");

  response.cookies.set("admin_token", token, {
    httpOnly: true,
    secure: process.env.NODE_ENV === "production",
    sameSite: "lax",
    path: "/",
    maxAge: 60 * 60 * 8, // 8 hours
  });
  return response;
}
