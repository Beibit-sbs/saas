import { NextRequest, NextResponse } from "next/server";
import { getServerApiBaseUrl } from "@/shared/server/runtime-env";

function unauthorized() {
  return NextResponse.json({ detail: "Authentication required" }, { status: 401 });
}

export async function GET(request: NextRequest) {
  const apiBase = getServerApiBaseUrl();
  const token = request.cookies.get("app_access_token")?.value ?? request.cookies.get("admin_token")?.value;
  if (!token) return unauthorized();

  try {
    const upstream = await fetch(new URL("/api/auth/me/preferences", apiBase), {
      method: "GET",
      headers: {
        authorization: `Bearer ${token}`,
      },
      cache: "no-store",
    });

    const contentType = upstream.headers.get("content-type") ?? "";
    if (contentType.includes("application/json")) {
      const payload = await upstream.json();
      return NextResponse.json(payload, { status: upstream.status });
    }
    const text = await upstream.text();
    return new NextResponse(text, { status: upstream.status });
  } catch {
    return NextResponse.json({ detail: "Upstream unavailable" }, { status: 503 });
  }
}
