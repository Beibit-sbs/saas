import { NextResponse } from "next/server";
import { isJwtExpired, toSafeSession } from "@/shared/server/auth-session";

const API_BASE = process.env.API_BASE_URL ?? "http://localhost:8000";
const DEFAULT_LOGIN_TENANT_ID = process.env.AUTH_DEFAULT_TENANT_ID ?? "1";

function shouldUseSecureCookie(request: Request): boolean {
  const explicit = process.env.AUTH_COOKIE_SECURE;
  if (explicit === "true") return true;
  if (explicit === "false") return false;

  try {
    const url = new URL(request.url);
    // Local HTTP runtime must keep non-secure cookie; otherwise browser omits it and /api/auth/me fails.
    if (url.hostname === "localhost" || url.hostname === "127.0.0.1") return false;
    if (url.protocol === "https:") return true;
  } catch {
    // Fall through to proxy/env heuristics.
  }

  const forwardedProto = request.headers.get("x-forwarded-proto");
  if (forwardedProto && forwardedProto.toLowerCase().includes("https")) {
    return true;
  }

  return process.env.NODE_ENV === "production";
}

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

export async function POST(request: Request) {
  const body = await request.json();
  const login = normalizeLogin(body?.login ?? body?.username);
  const tenantId = resolveTenantId(body, request);

  const upstream = await fetch(`${API_BASE}/api/auth/login`, {
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

  response.cookies.set("admin_token", token, {
    httpOnly: true,
    secure: shouldUseSecureCookie(request),
    sameSite: "lax",
    path: "/",
    maxAge: 60 * 60 * 8, // 8 hours
  });
  return response;
}
