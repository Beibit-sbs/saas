import { NextResponse } from "next/server";
import { getServerApiBaseUrl } from "@/shared/server/runtime-env";

export async function GET() {
  const apiBase = getServerApiBaseUrl();
  try {
    const upstream = await fetch(new URL("/api/auth/modes", apiBase), {
      method: "GET",
      cache: "no-store",
      headers: { "Content-Type": "application/json" },
    });

    const payload = await upstream.json().catch(() => ({}));
    return NextResponse.json(payload, { status: upstream.status });
  } catch {
    return NextResponse.json({ detail: "Upstream unavailable" }, { status: 503 });
  }
}
