import { NextRequest, NextResponse } from "next/server";
import { toSafeSessionFromProfile } from "@/shared/server/auth-session";
import { getServerApiBaseUrl } from "@/shared/server/runtime-env";

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
  const apiBase = getServerApiBaseUrl();
  const token = request.cookies.get("admin_token")?.value;
  if (!token) {
    return unauthenticated(401, request.headers.get("x-request-id"));
  }

  const requestId = request.headers.get("x-request-id");

  try {
    const sessionUpstream = await fetch(new URL("/api/auth/me", apiBase), {
      method: "GET",
      headers: {
        authorization: `Bearer ${token}`,
        ...(requestId ? { "x-request-id": requestId } : {}),
      },
      cache: "no-store",
    });

    const upstreamRequestId = sessionUpstream.headers.get("x-request-id") ?? requestId;
    if (sessionUpstream.status === 401 || sessionUpstream.status === 403) {
      return unauthenticated(401, upstreamRequestId);
    }

    if (sessionUpstream.ok) {
      const payload = (await sessionUpstream.json().catch(() => null)) as
        | {
          authenticated?: boolean;
          user?: {
            sub?: string;
            displayName?: string;
            roles?: unknown;
            permissions?: unknown;
            tenantId?: number;
            language?: string;
          };
        }
        | null;
      if (payload?.authenticated === true && payload.user?.sub) {
        const normalized = {
          authenticated: true,
          user: {
            sub: payload.user.sub,
            displayName: payload.user.displayName ?? payload.user.sub,
            roles: Array.isArray(payload.user.roles) ? payload.user.roles : [],
            permissions: Array.isArray(payload.user.permissions) ? payload.user.permissions : [],
            ...(typeof payload.user.tenantId === "number" ? { tenantId: payload.user.tenantId } : {}),
            ...(typeof payload.user.language === "string" ? { language: payload.user.language } : {}),
          },
        };
        return NextResponse.json(normalized, {
          status: 200,
          headers: {
            "cache-control": "no-store",
            ...(upstreamRequestId ? { "x-request-id": upstreamRequestId } : {}),
          },
        });
      }
      return unauthenticated(401, upstreamRequestId);
    }

    // Backward compatibility for environments that only expose /me/profile.
    if (sessionUpstream.status !== 404) {
      return unauthenticated(503, upstreamRequestId);
    }

    const profileUpstream = await fetch(new URL("/api/auth/me/profile", apiBase), {
      method: "GET",
      headers: {
        authorization: `Bearer ${token}`,
        ...(requestId ? { "x-request-id": requestId } : {}),
      },
      cache: "no-store",
    });

    const profileRequestId = profileUpstream.headers.get("x-request-id") ?? requestId;
    if (profileUpstream.status === 401 || profileUpstream.status === 403 || profileUpstream.status === 404) {
      return unauthenticated(401, profileRequestId);
    }

    if (!profileUpstream.ok) {
      return unauthenticated(503, profileRequestId);
    }

    const profile = (await profileUpstream.json()) as unknown;
    const session = toSafeSessionFromProfile(profile);
    if (!session) {
      return unauthenticated(401, profileRequestId);
    }

    return NextResponse.json(session, {
      status: 200,
      headers: {
        "cache-control": "no-store",
        ...(profileRequestId ? { "x-request-id": profileRequestId } : {}),
      },
    });
  } catch {
    return unauthenticated(503, requestId);
  }
}
