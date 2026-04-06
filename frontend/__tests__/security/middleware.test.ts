import { NextRequest } from "next/server";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { middleware } from "@/middleware";

const EDGE_BASE = "https://edge.test";

function makeJwt(payload: Record<string, unknown>) {
  const p = Buffer.from(JSON.stringify(payload)).toString("base64url");
  return `header.${p}.signature`;
}

function mockActiveSession(roles: string[] = ["admin"]) {
  vi.stubGlobal(
    "fetch",
    vi.fn(async () =>
      new Response(JSON.stringify({ authenticated: true, user: { roles } }), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      }),
    ),
  );
}

beforeEach(() => {
  vi.unstubAllGlobals();
  process.env.API_BASE_URL = "https://api.example.test";
});

afterEach(() => {
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
  delete process.env.API_BASE_URL;
});

describe("console route protection middleware", () => {
  it("redirects unauthenticated /console requests to /login", async () => {
    const req = new NextRequest(`${EDGE_BASE}/console/students`);
    const res = await middleware(req);

    expect(res.status).toBe(307);
    const location = res.headers.get("location") ?? "";
    expect(location).toContain("/login");
    expect(location).toContain("next=%2Fconsole%2Fstudents");
  });

  it("allows authenticated /console requests with non-expired token", async () => {
    mockActiveSession(["admin"]);
    const token = makeJwt({ exp: Math.floor(Date.now() / 1000) + 3600 });
    const req = new NextRequest(`${EDGE_BASE}/console/students`, {
      headers: { cookie: `admin_token=${token}` },
    });

    const res = await middleware(req);

    expect(res.status).toBe(200);
    expect(res.headers.get("location")).toBeNull();
  });

  it("redirects expired token to /login", async () => {
    const token = makeJwt({ exp: Math.floor(Date.now() / 1000) - 1 });
    const req = new NextRequest(`${EDGE_BASE}/console/grades`, {
      headers: { cookie: `admin_token=${token}` },
    });

    const res = await middleware(req);

    expect(res.status).toBe(307);
    expect(res.headers.get("location") ?? "").toContain("/login");
  });

  it("redirects to /console when role does not match /student zone", async () => {
    mockActiveSession(["faculty"]);
    const token = makeJwt({ exp: Math.floor(Date.now() / 1000) + 3600 });
    const req = new NextRequest(`${EDGE_BASE}/student`, {
      headers: { cookie: `admin_token=${token}` },
    });

    const res = await middleware(req);

    expect(res.status).toBe(307);
    expect(res.headers.get("location")).toBe(`${EDGE_BASE}/console`);
  });

  it("allows student role to /student zone", async () => {
    mockActiveSession(["student"]);
    const token = makeJwt({ exp: Math.floor(Date.now() / 1000) + 3600 });
    const req = new NextRequest(`${EDGE_BASE}/student`, {
      headers: { cookie: `admin_token=${token}` },
    });

    const res = await middleware(req);

    expect(res.status).toBe(200);
  });

  it("allows superadmin to /registrar zone", async () => {
    mockActiveSession(["superadmin"]);
    const token = makeJwt({ exp: Math.floor(Date.now() / 1000) + 3600 });
    const req = new NextRequest(`${EDGE_BASE}/registrar`, {
      headers: { cookie: `admin_token=${token}` },
    });

    const res = await middleware(req);

    expect(res.status).toBe(200);
  });

  it("redirects to /login when token is valid but session is inactive", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () =>
        new Response(JSON.stringify({ authenticated: false }), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        }),
      ),
    );

    const token = makeJwt({ exp: Math.floor(Date.now() / 1000) + 3600 });
    const req = new NextRequest(`${EDGE_BASE}/faculty`, {
      headers: { cookie: `admin_token=${token}` },
    });

    const res = await middleware(req);

    expect(res.status).toBe(307);
    expect(res.headers.get("location") ?? "").toContain("/login");
  });
});
