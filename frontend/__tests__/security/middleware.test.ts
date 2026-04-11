import { NextRequest } from "next/server";
import { afterEach, describe, expect, it, vi } from "vitest";

import { middleware } from "@/middleware";

const EDGE_BASE = "https://edge.test";

function makeJwt(payload: Record<string, unknown>) {
  const p = Buffer.from(JSON.stringify(payload)).toString("base64url");
  return `header.${p}.signature`;
}

afterEach(() => {
  vi.restoreAllMocks();
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
    vi.spyOn(global, "fetch").mockResolvedValue(
      new Response(JSON.stringify({ authenticated: true }), {
        status: 200,
        headers: { "content-type": "application/json" },
      }),
    );

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

  it("redirects to /login when session is inactive", async () => {
    vi.spyOn(global, "fetch").mockResolvedValue(
      new Response(JSON.stringify({ authenticated: false }), {
        status: 200,
        headers: { "content-type": "application/json" },
      }),
    );

    const token = makeJwt({ exp: Math.floor(Date.now() / 1000) + 3600 });
    const req = new NextRequest(`${EDGE_BASE}/console/students`, {
      headers: { cookie: `admin_token=${token}` },
    });

    const res = await middleware(req);

    expect(res.status).toBe(307);
    expect(res.headers.get("location") ?? "").toContain("/login");
  });
});
