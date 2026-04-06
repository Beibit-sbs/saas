import { NextRequest, NextResponse } from "next/server";
import { getServerApiBaseUrl } from "@/shared/server/runtime-env";

function readAuthToken(request: NextRequest): string | undefined {
  return request.cookies.get("app_access_token")?.value ?? request.cookies.get("admin_token")?.value;
}

const PUBLIC_PATHS = ["/login", "/api/auth/login"];

const ROLE_ROUTE_RULES: Array<{ prefix: string; allowedRoles: string[] }> = [
  { prefix: "/student", allowedRoles: ["student", "admin", "superadmin"] },
  { prefix: "/faculty", allowedRoles: ["faculty", "teacher", "instructor", "admin", "superadmin"] },
  {
    prefix: "/registrar",
    allowedRoles: ["registrar", "academic_admin", "institution_admin", "admin", "superadmin"],
  },
];

type SessionSnapshot = {
  active: boolean;
  roles: string[];
};

function isTokenExpired(token: string): boolean {
  try {
    const [, payload] = token.split(".");
    if (!payload) return true;
    const normalized = payload.replace(/-/g, "+").replace(/_/g, "/");
    const padded = normalized + "=".repeat((4 - (normalized.length % 4)) % 4);
    const decoded = JSON.parse(atob(padded));
    if (!decoded.exp) return false;
    return Date.now() / 1000 > decoded.exp;
  } catch {
    return true;
  }
}

function normalizeRoles(value: unknown): string[] {
  if (!Array.isArray(value)) {
    return [];
  }
  return value
    .map((item) => String(item).trim().toLowerCase())
    .filter(Boolean);
}

async function readSessionSnapshot(token: string, requestId: string | null): Promise<SessionSnapshot> {
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
      const payload = (await response.json().catch(() => ({}))) as {
        authenticated?: boolean;
        user?: { roles?: unknown };
      };
      if (payload.authenticated === true) {
        return {
          active: true,
          roles: normalizeRoles(payload.user?.roles),
        };
      }
      return { active: false, roles: [] };
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
      if (!profileResponse.ok) {
        return { active: false, roles: [] };
      }
      const profilePayload = (await profileResponse.json().catch(() => ({}))) as {
        roles?: unknown;
      };
      return {
        active: true,
        roles: normalizeRoles(profilePayload.roles),
      };
    }

    return { active: false, roles: [] };
  } catch {
    return { active: false, roles: [] };
  }
}

function resolveRequiredRoles(pathname: string): string[] | null {
  for (const rule of ROLE_ROUTE_RULES) {
    if (pathname === rule.prefix || pathname.startsWith(`${rule.prefix}/`)) {
      return rule.allowedRoles;
    }
  }
  return null;
}

export async function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  if (pathname === "/admin" || pathname.startsWith("/admin/")) {
    return NextResponse.redirect(new URL("/console/platform", request.url));
  }

  if (pathname.startsWith("/login")) {
    const token = readAuthToken(request);
    if (token && !isTokenExpired(token)) {
      const snapshot = await readSessionSnapshot(token, request.headers.get("x-request-id"));
      if (snapshot.active) {
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

  const protectedPath = pathname.startsWith("/console") || resolveRequiredRoles(pathname) !== null;
  if (!protectedPath) {
    return NextResponse.next();
  }

  const token = readAuthToken(request);

  if (!token || isTokenExpired(token)) {
    const loginUrl = new URL("/login", request.url);
    const search = request.nextUrl.search;
    loginUrl.searchParams.set("next", search ? `${pathname}${search}` : pathname);
    return NextResponse.redirect(loginUrl);
  }

  // For the admin console, a valid non-expired token is sufficient.
  // Avoid backend round-trips here to prevent redirect loops when edge fetch has transient issues.
  if (pathname === "/console" || pathname.startsWith("/console/")) {
    return NextResponse.next();
  }

  const snapshot = await readSessionSnapshot(token, request.headers.get("x-request-id"));
  if (!snapshot.active) {
    const loginUrl = new URL("/login", request.url);
    const search = request.nextUrl.search;
    loginUrl.searchParams.set("next", search ? `${pathname}${search}` : pathname);
    return NextResponse.redirect(loginUrl);
  }

  const requiredRoles = resolveRequiredRoles(pathname);
  if (requiredRoles) {
    const hasAccess = snapshot.roles.some((role) => requiredRoles.includes(role));
    if (!hasAccess) {
      return NextResponse.redirect(new URL("/console", request.url));
    }
  }

  return NextResponse.next();
}

export const config = {
  matcher: [
    "/login",
    "/console/:path*",
    "/admin",
    "/admin/:path*",
    "/student",
    "/student/:path*",
    "/faculty",
    "/faculty/:path*",
    "/registrar",
    "/registrar/:path*",
  ],
};
