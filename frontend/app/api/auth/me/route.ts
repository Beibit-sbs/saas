import { NextRequest, NextResponse } from "next/server";
import { toSafeSessionFromProfile } from "@/shared/server/auth-session";

const API_BASE =
  process.env.API_BASE_URL ?? process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

function unauthenticated(status: number = 401, requestId?: string | null) {
  return NextResponse.json(
    { authenticated: false, user: null },
    {
      status,
      headers: {
        "cache-control": "no-store",
        ...(requestId ? { "x-request-id": requestId } : {}),
      },
    },
  );
}

export async function GET(request: NextRequest) {
  const token = request.cookies.get("admin_token")?.value;
  if (!token) {
    return unauthenticated(401, request.headers.get("x-request-id"));
  }

  const requestId = request.headers.get("x-request-id");

  try {
    const upstream = await fetch(`${API_BASE}/api/auth/me/profile`, {
      method: "GET",
      headers: {
        authorization: `Bearer ${token}`,
        ...(requestId ? { "x-request-id": requestId } : {}),
      },
      cache: "no-store",
    });

    const upstreamRequestId = upstream.headers.get("x-request-id") ?? requestId;
    if (upstream.status === 401 || upstream.status === 403) {
      return unauthenticated(401, upstreamRequestId);
    }

    if (!upstream.ok) {
      return unauthenticated(503, upstreamRequestId);
    }

    const profile = (await upstream.json()) as unknown;
    const session = toSafeSessionFromProfile(profile);
    if (!session) {
      return unauthenticated(401, upstreamRequestId);
    }

    return NextResponse.json(session, {
      status: 200,
      headers: {
        "cache-control": "no-store",
        ...(upstreamRequestId ? { "x-request-id": upstreamRequestId } : {}),
      },
    });
  } catch {
    return unauthenticated(503, requestId);
  }
}
