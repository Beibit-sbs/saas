import { NextRequest } from "next/server";
import { describe, expect, it, vi, afterEach } from "vitest";

import { POST as loginPost } from "@/app/api/auth/login/route";
import { POST as logoutPost } from "@/app/api/auth/logout/route";
import { GET as meGet } from "@/app/api/auth/me/route";
import { middleware } from "@/middleware";

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
      permissions: ["students.read"],
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
      new Request("http://localhost/api/auth/login", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ username: "owner@example.com", password: "secret" }),
      }),
    );

    const body = await response.json();
    expect(response.status).toBe(200);
    expect(body.ok).toBe(true);
    expect(body.authenticated).toBe(true);
    expect(body.user.sub).toBe("owner@example.com");
    expect(body.token).toBeUndefined();
    expect(body.access_token).toBeUndefined();

    const setCookie = response.headers.get("set-cookie") ?? "";
    expect(setCookie).toContain("admin_token=");
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

  it("me validates session via backend profile and returns safe payload", async () => {
    const fetchMock = vi.spyOn(global, "fetch").mockResolvedValue(
      new Response(
        JSON.stringify({
          user_id: "owner@example.com",
          display_name: "Owner",
          roles: ["admin"],
          tenant_id: 7,
          auth_source: "local",
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

    const request = new NextRequest("http://localhost/api/auth/me", {
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
    expect(String(url)).toBe("http://localhost:8000/api/auth/me/profile");
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

    const request = new NextRequest("http://localhost/api/auth/me", {
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

    const request = new NextRequest("http://localhost/api/auth/me", {
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

    const request = new NextRequest("http://localhost/api/auth/me", {
      headers: { cookie: "admin_token=session-token" },
    });

    const response = await meGet(request);
    expect(response.status).toBe(503);

    const body = await response.json();
    expect(body.authenticated).toBe(false);
    expect(body.user).toBeNull();
  });

  it("me returns 401 when no session cookie", async () => {
    const request = new NextRequest("http://localhost/api/auth/me");
    const response = await meGet(request);

    expect(response.status).toBe(401);
    const body = await response.json();
    expect(body.authenticated).toBe(false);
    expect(body.user).toBeNull();
  });

  it("middleware and me stay consistent for expired session", async () => {
    const expiredToken = makeJwt({ exp: Math.floor(Date.now() / 1000) - 1 });
    const middlewareRequest = new NextRequest("http://localhost/console/students", {
      headers: { cookie: `admin_token=${expiredToken}` },
    });
    const middlewareResponse = middleware(middlewareRequest);
    expect(middlewareResponse.status).toBe(307);
    expect(middlewareResponse.headers.get("location") ?? "").toContain("/login");

    vi.spyOn(global, "fetch").mockResolvedValue(
      new Response(JSON.stringify({ detail: "token expired" }), {
        status: 401,
        headers: { "content-type": "application/json" },
      }),
    );

    const meRequest = new NextRequest("http://localhost/api/auth/me", {
      headers: { cookie: `admin_token=${expiredToken}` },
    });
    const meResponse = await meGet(meRequest);
    expect(meResponse.status).toBe(401);

    const meBody = await meResponse.json();
    expect(meBody.authenticated).toBe(false);
    expect(meBody.user).toBeNull();
  });
});
