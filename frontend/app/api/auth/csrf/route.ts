import { NextResponse } from "next/server";

const API_BASE = process.env.API_BASE_URL ?? process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export async function GET() {
  try {
    const upstream = await fetch(`${API_BASE}/api/auth/csrf`, {
      method: "GET",
      cache: "no-store",
      headers: { "Content-Type": "application/json" },
    });

    const payload = await upstream.json().catch(() => ({}));
    const response = NextResponse.json(payload, { status: upstream.status });

    const setCookie = upstream.headers.get("set-cookie");
    if (setCookie) {
      response.headers.append("set-cookie", setCookie);
    }

    return response;
  } catch {
    return NextResponse.json({ detail: "Upstream unavailable" }, { status: 503 });
  }
}
