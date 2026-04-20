import { NextRequest, NextResponse } from "next/server";
import { getServerApiBaseUrl } from "@/shared/server/runtime-env";

function readAuthToken(request: NextRequest): string | undefined {
  return request.cookies.get("app_access_token")?.value ?? request.cookies.get("admin_token")?.value;
}

const UPSTREAM_TIMEOUT_MS = 8000;
const BFF_DEBUG = process.env.BFF_DEBUG === "1";

const HOP_BY_HOP_HEADERS = new Set([
  "connection",
  "keep-alive",
  "proxy-authenticate",
  "proxy-authorization",
  "te",
  "trailer",
  "transfer-encoding",
  "upgrade",
  "host",
  "cookie",
  "content-length",
]);

function toUpstreamPath(pathParts: string[]): string {
  const normalized = pathParts.join("/");
  if (
    normalized === "health"
    || normalized.startsWith("health/")
    || normalized === "metrics"
    || normalized.startsWith("metrics/")
  ) {
    return `/${normalized}`;
  }
  // platform-core admin routes are under /api/v1/admin on the backend
  if (normalized.startsWith("admin/platform/")) {
    return `/api/v1/${normalized}`;
  }
  // platform management routes are mounted at /platform on the backend.
  if (normalized === "platform" || normalized.startsWith("platform/")) {
    return `/${normalized}`;
  }
  return `/api/${normalized}`;
}

function normalizeError(status: number, detail: string, requestId: string | null) {
  const code = status === 401
    ? "UNAUTHORIZED"
    : status === 400
      ? "BAD_REQUEST"
      : "UPSTREAM_ERROR";

  return {
    error: {
      status,
      code,
      detail,
      request_id: requestId,
    },
  };
}

function hasUnsafePathPart(pathPart: string): boolean {
  const lowered = pathPart.toLowerCase();
  if (lowered === "." || lowered === "..") return true;
  if (lowered.includes("://")) return true;
  if (lowered.startsWith("//")) return true;
  if (lowered.includes("\\")) return true;
  if (lowered.includes("%2f") || lowered.includes("%5c") || lowered.includes("%2e%2e")) return true;
  return false;
}

function bffDebugLog(payload: Record<string, unknown>) {
  if (!BFF_DEBUG) return;
  // Dev-only diagnostics — sanitised: strip body/headers to prevent leaking internals.
  const { body, headers, ...safe } = payload;
  try {
    console.error("[bff-debug]", JSON.stringify(safe));
  } catch {
    console.error("[bff-debug]", safe);
  }
}

export async function proxyBffRequest(request: NextRequest, pathParts: string[]) {
  const apiBase = getServerApiBaseUrl();
  const token = readAuthToken(request);
  const csrfHeader = request.headers.get("x-csrf-token");
  const requestPath = `/${pathParts.join("/")}`;

  if (pathParts.length === 0 || pathParts.some(hasUnsafePathPart)) {
    bffDebugLog({
      phase: "path-reject",
      method: request.method,
      requestPath,
      reason: "unsafe_path",
    });
    return NextResponse.json(
      normalizeError(400, "Invalid upstream path", request.headers.get("x-request-id")),
      { status: 400 },
    );
  }

  bffDebugLog({
    phase: "request",
    method: request.method,
    requestPath,
    hasAdminTokenCookie: Boolean(token),
    hasCsrfHeader: Boolean(csrfHeader),
  });

  if (!token) {
    bffDebugLog({
      phase: "auth-reject",
      method: request.method,
      requestPath,
      reason: "missing_admin_token_cookie",
    });
    return NextResponse.json(
      normalizeError(401, "Authentication required", request.headers.get("x-request-id")),
      { status: 401 },
    );
  }

  const upstreamUrl = new URL(toUpstreamPath(pathParts), apiBase);
  upstreamUrl.search = request.nextUrl.search;

  const headers = new Headers();
  headers.set("authorization", `Bearer ${token}`);

  const requestId = request.headers.get("x-request-id");
  if (requestId) {
    headers.set("x-request-id", requestId);
  }

  for (const [key, value] of request.headers.entries()) {
    if (HOP_BY_HOP_HEADERS.has(key.toLowerCase())) continue;
    if (key.toLowerCase() === "authorization") continue;
    if (key.toLowerCase() === "x-request-id") continue;
    headers.set(key, value);
  }

  const hasBody = request.method !== "GET" && request.method !== "HEAD";
  const body = hasBody ? await request.text() : undefined;

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), UPSTREAM_TIMEOUT_MS);

  let upstream: Response;
  try {
    upstream = await fetch(upstreamUrl, {
      method: request.method,
      headers,
      body,
      cache: "no-store",
      signal: controller.signal,
    });
  } catch (error) {
    clearTimeout(timeoutId);
    const message = error instanceof Error && error.name === "AbortError"
      ? `Upstream timeout after ${UPSTREAM_TIMEOUT_MS}ms`
      : "Upstream unavailable";
    bffDebugLog({
      phase: "upstream-fetch-error",
      method: request.method,
      requestPath,
      upstreamUrl: upstreamUrl.toString(),
      message,
    });
    return NextResponse.json(
      normalizeError(503, message, requestId),
      { status: 503 },
    );
  }
  clearTimeout(timeoutId);

  const contentType = upstream.headers.get("content-type") ?? "";
  const upstreamRequestId = upstream.headers.get("x-request-id") ?? requestId;

  if (!upstream.ok) {
    let detail = `HTTP ${upstream.status}`;
    try {
      if (contentType.includes("application/json")) {
        const json = (await upstream.json()) as { detail?: string; error?: { detail?: string } };
        detail = json.detail ?? json.error?.detail ?? detail;
      } else {
        const text = await upstream.text();
        if (text) detail = text;
      }
    } catch {
      // Keep normalized fallback detail.
    }

    bffDebugLog({
      phase: "upstream-error",
      method: request.method,
      requestPath,
      upstreamUrl: upstreamUrl.toString(),
      upstreamStatus: upstream.status,
      detail,
    });

    return NextResponse.json(normalizeError(upstream.status, detail, upstreamRequestId), {
      status: upstream.status,
      headers: upstreamRequestId ? { "x-request-id": upstreamRequestId } : undefined,
    });
  }

  bffDebugLog({
    phase: "upstream-ok",
    method: request.method,
    requestPath,
    upstreamUrl: upstreamUrl.toString(),
    upstreamStatus: upstream.status,
  });

  if (upstream.status === 204) {
    return new NextResponse(null, {
      status: 204,
      headers: upstreamRequestId ? { "x-request-id": upstreamRequestId } : undefined,
    });
  }

  if (contentType.includes("application/json")) {
    const payload = await upstream.json();
    return NextResponse.json(payload, {
      status: upstream.status,
      headers: upstreamRequestId ? { "x-request-id": upstreamRequestId } : undefined,
    });
  }

  const text = await upstream.text();
  return new NextResponse(text, {
    status: upstream.status,
    headers: {
      "content-type": contentType || "text/plain; charset=utf-8",
      ...(upstreamRequestId ? { "x-request-id": upstreamRequestId } : {}),
    },
  });
}
