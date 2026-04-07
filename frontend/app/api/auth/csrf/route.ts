import { NextResponse } from "next/server";
import { getServerApiBaseUrl } from "@/shared/server/runtime-env";

export async function GET() {
  const apiBase = getServerApiBaseUrl();
  try {
    const upstream = await fetch(new URL("/api/auth/csrf", apiBase), {
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
