import { NextRequest, NextResponse } from "next/server";
import { getServerApiBaseUrl } from "@/shared/server/runtime-env";

function unauthorized() {
  return NextResponse.json({ detail: "Authentication required" }, { status: 401 });
}

function misconfigured() {
  return NextResponse.json({ detail: "INTERNAL_API_TOKEN is not configured" }, { status: 503 });
}

export async function POST(request: NextRequest) {
  const token = request.cookies.get("app_access_token")?.value ?? request.cookies.get("admin_token")?.value;
  if (!token) return unauthorized();

  const internalApiToken = process.env.INTERNAL_API_TOKEN?.trim();
  if (!internalApiToken) return misconfigured();

  const apiBase = getServerApiBaseUrl();

  let limit = 100;
  try {
    const body = (await request.json()) as { limit?: number };
    if (typeof body.limit === "number" && Number.isFinite(body.limit)) {
      limit = Math.max(1, Math.min(500, Math.trunc(body.limit)));
    }
  } catch {
    // No JSON body means default limit.
  }

  try {
    const upstream = await fetch(new URL(`/api/v1/internal/webhooks/retry-failed?limit=${limit}`, apiBase), {
      method: "POST",
      headers: {
        authorization: `Bearer ${internalApiToken}`,
        "content-type": "application/json",
      },
      cache: "no-store",
    });

    const data = await upstream.json().catch(() => ({}));
    return NextResponse.json(data, { status: upstream.status });
  } catch {
    return NextResponse.json({ detail: "upstream unavailable" }, { status: 503 });
  }
}