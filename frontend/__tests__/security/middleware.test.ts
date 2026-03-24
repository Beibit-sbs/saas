import { NextRequest } from "next/server";
import { describe, expect, it } from "vitest";

import { middleware } from "@/middleware";

function makeJwt(payload: Record<string, unknown>) {
  const p = Buffer.from(JSON.stringify(payload)).toString("base64url");
  return `header.${p}.signature`;
}

describe("console route protection middleware", () => {
  it("redirects unauthenticated /console requests to /login", () => {
    const req = new NextRequest("http://localhost/console/students");
    const res = middleware(req);

    expect(res.status).toBe(307);
    const location = res.headers.get("location") ?? "";
    expect(location).toContain("/login");
    expect(location).toContain("next=%2Fconsole%2Fstudents");
  });

  it("allows authenticated /console requests with non-expired token", () => {
    const token = makeJwt({ exp: Math.floor(Date.now() / 1000) + 3600 });
    const req = new NextRequest("http://localhost/console/students", {
      headers: { cookie: `admin_token=${token}` },
    });

    const res = middleware(req);

    expect(res.status).toBe(200);
    expect(res.headers.get("location")).toBeNull();
  });

  it("redirects expired token to /login", () => {
    const token = makeJwt({ exp: Math.floor(Date.now() / 1000) - 1 });
    const req = new NextRequest("http://localhost/console/grades", {
      headers: { cookie: `admin_token=${token}` },
    });

    const res = middleware(req);

    expect(res.status).toBe(307);
    expect(res.headers.get("location") ?? "").toContain("/login");
  });
});
