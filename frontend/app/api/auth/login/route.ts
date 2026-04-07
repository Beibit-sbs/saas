import { NextResponse } from "next/server";
import { isJwtExpired, toSafeSession } from "@/shared/server/auth-session";
import { getServerApiBaseUrl, shouldUseSecureCookie } from "@/shared/server/runtime-env";

const DEFAULT_LOGIN_TENANT_ID = process.env.AUTH_DEFAULT_TENANT_ID ?? "1";
const PRIMARY_AUTH_COOKIE = "app_access_token";
const LEGACY_AUTH_COOKIE = "admin_token";

function resolveTenantId(body: unknown, request: Request): string {
  if (body && typeof body === "object") {
    const tenantIdCandidate = (body as { tenant_id?: unknown; tenantId?: unknown }).tenant_id
      ?? (body as { tenant_id?: unknown; tenantId?: unknown }).tenantId;
    if (tenantIdCandidate !== undefined && tenantIdCandidate !== null) {
      const normalized = String(tenantIdCandidate).trim();
      if (normalized) return normalized;
    }
  }

  const headerTenantId = request.headers.get("x-tenant-id");
  if (headerTenantId && headerTenantId.trim()) {
    return headerTenantId.trim();
  }

  return String(DEFAULT_LOGIN_TENANT_ID).trim() || "1";
}

function normalizeLogin(raw: unknown): string {
  const value = String(raw ?? "").trim();
  if (!value) return "";
  const lowered = value.toLowerCase();
  if (lowered.startsWith("local/")) {
    const stripped = value.slice(6).trim();
    return stripped || value;
  }
  return value;
}

function isPlatformAdminLogin(login: string): boolean {
  return login.trim().toLowerCase() === "platform_admin";
}

export async function POST(request: Request) {
  const apiBase = getServerApiBaseUrl();
  const body = await request.json();
  const login = normalizeLogin(body?.login ?? body?.username);
  const tenantId = isPlatformAdminLogin(login) ? "1" : resolveTenantId(body, request);

  const upstream = await fetch(new URL("/api/auth/login", apiBase), {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-Tenant-ID": tenantId,
    },
    body: JSON.stringify({
      ...body,
      login,
    }),
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

  const cookieOptions = {
    httpOnly: true,
    secure: shouldUseSecureCookie(request),
    sameSite: "lax",
    path: "/",
    maxAge: 60 * 60 * 8, // 8 hours
  } as const;

  response.cookies.set(PRIMARY_AUTH_COOKIE, token, cookieOptions);
  response.cookies.set(LEGACY_AUTH_COOKIE, token, cookieOptions);
  return response;
}
