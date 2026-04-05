import { NextRequest, NextResponse } from "next/server";
import { getServerApiBaseUrl } from "@/shared/server/runtime-env";

const PUBLIC_PATHS = ["/login", "/api/auth/login"];

function isTokenExpired(token: string): boolean {
  try {
    const [, payload] = token.split(".");
    const decoded = JSON.parse(Buffer.from(payload, "base64url").toString());
    if (!decoded.exp) return false;
    return Date.now() / 1000 > decoded.exp;
  } catch {
    return true;
  }
}

async function hasActiveSession(token: string, requestId: string | null): Promise<boolean> {
  const apiBase = getServerApiBaseUrl();
  try {
    const response = await fetch(new URL("/api/auth/me", apiBase), {
      method: "GET",
      headers: {
        authorization: `Bearer ${token}`,
        ...(requestId ? { "x-request-id": requestId } : {}),
      },
      cache: "no-store",
    });

    if (response.ok) {
      const payload = (await response.json().catch(() => ({}))) as { authenticated?: boolean };
      return payload.authenticated === true;
    }

    // Backward compatibility for environments that only expose /me/profile.
    if (response.status === 404) {
      const profileResponse = await fetch(new URL("/api/auth/me/profile", apiBase), {
        method: "GET",
        headers: {
          authorization: `Bearer ${token}`,
          ...(requestId ? { "x-request-id": requestId } : {}),
        },
        cache: "no-store",
      });
      return profileResponse.ok;
    }

    return false;
  } catch {
    return false;
  }
}

export async function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  if (pathname === "/admin" || pathname.startsWith("/admin/")) {
    return NextResponse.redirect(new URL("/console/platform", request.url));
  }

  if (pathname.startsWith("/login")) {
    const token = request.cookies.get("admin_token")?.value;
    if (token && !isTokenExpired(token)) {
      const isActive = await hasActiveSession(token, request.headers.get("x-request-id"));
      if (isActive) {
        const next = request.nextUrl.searchParams.get("next") ?? "/console";
        const target = next.startsWith("/login") ? "/console" : next;
        return NextResponse.redirect(new URL(target, request.url));
      }
    }
    return NextResponse.next();
  }

  if (PUBLIC_PATHS.some((p) => pathname.startsWith(p))) {
    return NextResponse.next();
  }

  if (!pathname.startsWith("/console")) {
    return NextResponse.next();
  }

  const token = request.cookies.get("admin_token")?.value;

  if (!token || isTokenExpired(token)) {
    const loginUrl = new URL("/login", request.url);
    const search = request.nextUrl.search;
    loginUrl.searchParams.set("next", search ? `${pathname}${search}` : pathname);
    return NextResponse.redirect(loginUrl);
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/login", "/console/:path*", "/admin", "/admin/:path*"],
};
