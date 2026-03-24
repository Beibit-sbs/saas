import { NextRequest, NextResponse } from "next/server";

const API_BASE =
  process.env.API_BASE_URL ?? process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

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
  if (normalized === "health" || normalized === "metrics") {
    return `/${normalized}`;
  }
  return `/api/${normalized}`;
}

function normalizeError(status: number, detail: string, requestId: string | null) {
  return {
    error: {
      status,
      code: status === 401 ? "UNAUTHORIZED" : "UPSTREAM_ERROR",
      detail,
      request_id: requestId,
    },
  };
}

export async function proxyBffRequest(request: NextRequest, pathParts: string[]) {
  const token = request.cookies.get("admin_token")?.value;

  if (!token) {
    return NextResponse.json(
      normalizeError(401, "Authentication required", request.headers.get("x-request-id")),
      { status: 401 },
    );
  }

  const upstreamUrl = new URL(toUpstreamPath(pathParts), API_BASE);
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

  const upstream = await fetch(upstreamUrl, {
    method: request.method,
    headers,
    body,
    cache: "no-store",
  });

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

    return NextResponse.json(normalizeError(upstream.status, detail, upstreamRequestId), {
      status: upstream.status,
      headers: upstreamRequestId ? { "x-request-id": upstreamRequestId } : undefined,
    });
  }

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
