import { NextRequest } from "next/server";
import { describe, expect, it, vi, afterEach } from "vitest";

import { POST as loginPost } from "@/app/api/auth/login/route";
import { POST as logoutPost } from "@/app/api/auth/logout/route";
import { GET as meGet } from "@/app/api/auth/me/route";
import { middleware } from "@/middleware";

process.env.API_BASE_URL = process.env.API_BASE_URL ?? "http://backend:8000";

const API_BASE = process.env.API_BASE_URL;
const EDGE_BASE = "https://edge.test";

function makeJwt(payload: Record<string, unknown>) {
  const p = Buffer.from(JSON.stringify(payload)).toString("base64url");
  return `header.${p}.signature`;
}

afterEach(() => {
  vi.restoreAllMocks();
});

describe("auth routes hardening", () => {
  it("login stores token only in httpOnly cookie and returns safe session", async () => {
    const token = makeJwt({
      sub: "owner@example.com",
      display_name: "Owner",
      roles: ["admin"],
      scp: ["students.read"],
      tenant_id: 1,
      exp: Math.floor(Date.now() / 1000) + 3600,
    });

    vi.spyOn(global, "fetch").mockResolvedValue(
      new Response(JSON.stringify({ access_token: token, token_type: "bearer" }), {
        status: 200,
        headers: { "content-type": "application/json" },
      }),
    );

    const response = await loginPost(
      new Request(`${EDGE_BASE}/api/auth/login`, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ username: "owner@example.com", password: "secret", tenant_id: 1 }),
      }),
    );

    const body = await response.json();
    expect(response.status).toBe(200);
    expect(body.ok).toBe(true);
    expect(body.authenticated).toBe(true);
    expect(body.user.sub).toBe("owner@example.com");
    expect(body.token).toBeUndefined();
    expect(body.access_token).toBeUndefined();

    const fetchCalls = vi.mocked(global.fetch).mock.calls;
    expect(fetchCalls).toHaveLength(1);
    const [, init] = fetchCalls[0] as [string, RequestInit];
    expect(init.body).toBe(JSON.stringify({ username: "owner@example.com", password: "secret", tenant_id: 1, login: "owner@example.com" }));
    const headers = new Headers(init.headers as HeadersInit);
    expect(headers.get("x-tenant-id")).toBe("1");

    const setCookie = response.headers.get("set-cookie") ?? "";
    expect(setCookie).toContain("app_access_token=");
    expect(setCookie).toContain("HttpOnly");
    expect(setCookie).toContain("SameSite=lax");
  });

  it("logout clears auth cookie", async () => {
    const response = await logoutPost();
    expect(response.status).toBe(200);

    const setCookie = response.headers.get("set-cookie") ?? "";
    expect(setCookie).toContain("admin_token=");
    expect(setCookie).toContain("Max-Age=0");
    expect(setCookie).toContain("HttpOnly");
  });

  it("login forwards explicit tenant_id to backend", async () => {
    const token = makeJwt({
      sub: "tenant.user@example.com",
      display_name: "Tenant User",
      roles: ["admin"],
      scp: ["students.read"],
      tenant_id: 2,
      exp: Math.floor(Date.now() / 1000) + 3600,
    });

    const fetchMock = vi.spyOn(global, "fetch").mockResolvedValue(
      new Response(JSON.stringify({ access_token: token, token_type: "bearer" }), {
        status: 200,
        headers: { "content-type": "application/json" },
      }),
    );

    const response = await loginPost(
      new Request(`${EDGE_BASE}/api/auth/login`, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ username: "tenant.user@example.com", password: "secret", tenant_id: 2 }),
      }),
    );

    expect(response.status).toBe(200);
    const [url, init] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect(String(url)).toBe(`${API_BASE}/api/auth/login`);
    const headers = new Headers(init.headers as HeadersInit);
    expect(headers.get("x-tenant-id")).toBe("2");
  });

  it("login rejects non-platform payload without tenant", async () => {
    const fetchMock = vi.spyOn(global, "fetch");

    const response = await loginPost(
      new Request(`${EDGE_BASE}/api/auth/login`, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ username: "tenant.user@example.com", password: "secret" }),
      }),
    );

    expect(response.status).toBe(400);
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it("local/platform_admin login uses platform tenant implicitly", async () => {
    const token = makeJwt({
      sub: "platform_admin",
      display_name: "Platform Admin",
      roles: ["admin"],
      scp: ["students.read"],
      tenant_id: 1,
      exp: Math.floor(Date.now() / 1000) + 3600,
    });

    const fetchMock = vi.spyOn(global, "fetch").mockResolvedValue(
      new Response(JSON.stringify({ access_token: token, token_type: "bearer" }), {
        status: 200,
        headers: { "content-type": "application/json" },
      }),
    );

    const response = await loginPost(
      new Request(`${EDGE_BASE}/api/auth/login`, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ username: "local/platform_admin", password: "secret" }),
      }),
    );

    expect(response.status).toBe(200);
    const [, init] = fetchMock.mock.calls[0] as [string, RequestInit];
    const headers = new Headers(init.headers as HeadersInit);
    expect(headers.get("x-tenant-id")).toBe("1");
  });

  it("me validates session via backend me endpoint and returns safe payload", async () => {
    const fetchMock = vi.spyOn(global, "fetch").mockResolvedValue(
      new Response(
        JSON.stringify({
          authenticated: true,
          user: {
            sub: "owner@example.com",
            displayName: "Owner",
            roles: ["admin"],
            permissions: ["students.read"],
            tenantId: 7,
          },
        }),
        {
          status: 200,
          headers: {
            "content-type": "application/json",
            "x-request-id": "up-me-1",
          },
        },
      ),
    );

    const request = new NextRequest(`${EDGE_BASE}/api/auth/me`, {
      headers: {
        cookie: "admin_token=session-token",
        "x-request-id": "req-me-1",
      },
    });

    const response = await meGet(request);
    expect(response.status).toBe(200);
    expect(response.headers.get("x-request-id")).toBe("up-me-1");

    const body = await response.json();
    expect(body.authenticated).toBe(true);
    expect(body.user.sub).toBe("owner@example.com");
    expect(body.user.permissions).toContain("students.read");
    expect(body.token).toBeUndefined();
    expect(body.access_token).toBeUndefined();

    const fetchCalls = fetchMock.mock.calls;
    expect(fetchCalls).toHaveLength(1);
    const [url, init] = fetchCalls[0] as [string, RequestInit];
    expect(String(url)).toBe(`${API_BASE}/api/auth/me`);
    const headers = new Headers(init.headers as HeadersInit);
    expect(headers.get("authorization")).toBe("Bearer session-token");
    expect(headers.get("x-request-id")).toBe("req-me-1");
  });

  it("me returns unauthenticated for invalid session", async () => {
    vi.spyOn(global, "fetch").mockResolvedValue(
      new Response(JSON.stringify({ detail: "invalid token" }), {
        status: 401,
        headers: { "content-type": "application/json" },
      }),
    );

    const request = new NextRequest(`${EDGE_BASE}/api/auth/me`, {
      headers: { cookie: "admin_token=invalid-token" },
    });

    const response = await meGet(request);
    expect(response.status).toBe(401);

    const body = await response.json();
    expect(body.authenticated).toBe(false);
    expect(body.user).toBeNull();
  });

  it("me returns unauthenticated for expired session", async () => {
    vi.spyOn(global, "fetch").mockResolvedValue(
      new Response(JSON.stringify({ detail: "token expired" }), {
        status: 401,
        headers: { "content-type": "application/json" },
      }),
    );

    const request = new NextRequest(`${EDGE_BASE}/api/auth/me`, {
      headers: { cookie: "admin_token=expired-token" },
    });

    const response = await meGet(request);
    expect(response.status).toBe(401);

    const body = await response.json();
    expect(body.authenticated).toBe(false);
    expect(body.user).toBeNull();
  });

  it("me fails safely when backend profile endpoint is unavailable", async () => {
    vi.spyOn(global, "fetch").mockRejectedValue(new Error("upstream unavailable"));

    const request = new NextRequest(`${EDGE_BASE}/api/auth/me`, {
      headers: { cookie: "admin_token=session-token" },
    });

    const response = await meGet(request);
    expect(response.status).toBe(503);

    const body = await response.json();
    expect(body.authenticated).toBe(false);
    expect(body.user).toBeNull();
  });

  it("me does not synthesize permissions from roles when backend omits them", async () => {
    vi.spyOn(global, "fetch").mockResolvedValue(
      new Response(
        JSON.stringify({
          authenticated: true,
          user: {
            sub: "owner@example.com",
            displayName: "Owner",
            roles: ["admin"],
            tenantId: 7,
          },
        }),
        {
          status: 200,
          headers: { "content-type": "application/json" },
        },
      ),
    );

    const request = new NextRequest(`${EDGE_BASE}/api/auth/me`, {
      headers: { cookie: "admin_token=session-token" },
    });

    const response = await meGet(request);
    expect(response.status).toBe(200);

    const body = await response.json();
    expect(body.authenticated).toBe(true);
    expect(body.user.permissions).toEqual([]);
  });

  it("me returns 401 when no session cookie", async () => {
    const request = new NextRequest(`${EDGE_BASE}/api/auth/me`);
    const response = await meGet(request);

    expect(response.status).toBe(401);
    const body = await response.json();
    expect(body.authenticated).toBe(false);
    expect(body.user).toBeNull();
  });

  it("middleware and me stay consistent for expired session", async () => {
    const expiredToken = makeJwt({ exp: Math.floor(Date.now() / 1000) - 1 });
    const middlewareRequest = new NextRequest(`${EDGE_BASE}/console/students`, {
      headers: { cookie: `admin_token=${expiredToken}` },
    });
    const middlewareResponse = await middleware(middlewareRequest);
    expect(middlewareResponse.status).toBe(307);
    expect(middlewareResponse.headers.get("location") ?? "").toContain("/login");

    vi.spyOn(global, "fetch").mockResolvedValue(
      new Response(JSON.stringify({ detail: "token expired" }), {
        status: 401,
        headers: { "content-type": "application/json" },
      }),
    );

    const meRequest = new NextRequest(`${EDGE_BASE}/api/auth/me`, {
      headers: { cookie: `admin_token=${expiredToken}` },
    });
    const meResponse = await meGet(meRequest);
    expect(meResponse.status).toBe(401);

    const meBody = await meResponse.json();
    expect(meBody.authenticated).toBe(false);
    expect(meBody.user).toBeNull();
  });

  it("middleware redirects authenticated user from /login to /console", async () => {
    const validToken = makeJwt({ exp: Math.floor(Date.now() / 1000) + 3600 });
    vi.spyOn(global, "fetch").mockResolvedValue(
      new Response(JSON.stringify({ authenticated: true, user: { sub: "owner@example.com" } }), {
        status: 200,
        headers: { "content-type": "application/json" },
      }),
    );

    const request = new NextRequest(`${EDGE_BASE}/login`, {
      headers: { cookie: `admin_token=${validToken}` },
    });

    const response = await middleware(request);
    expect(response.status).toBe(307);
    expect(response.headers.get("location") ?? "").toContain("/console");
  });

  it("middleware keeps /login when no session cookie", async () => {
    const request = new NextRequest(`${EDGE_BASE}/login`);
    const response = await middleware(request);
    expect(response.status).toBe(200);
  });
});
