import { NextRequest } from "next/server";
import { afterEach, describe, expect, it, vi } from "vitest";

import { GET as bffGet, POST as bffPost } from "@/app/api/bff/[...path]/route";

process.env.API_BASE_URL = process.env.API_BASE_URL ?? "http://backend:8000";

const API_BASE = process.env.API_BASE_URL;
const EDGE_BASE = "https://edge.test";

afterEach(() => {
  vi.restoreAllMocks();
});

describe("bff proxy route", () => {
  it("returns 401 for missing session cookie", async () => {
    const req = new NextRequest(`${EDGE_BASE}/api/bff/admin/students`);
    const res = await bffGet(req, { params: { path: ["admin", "students"] } });

    expect(res.status).toBe(401);
    const body = await res.json();
    expect(body.error.code).toBe("UNAUTHORIZED");
  });

  it("forwards authorized request to backend with request id", async () => {
    const fetchMock = vi.spyOn(global, "fetch").mockResolvedValue(
      new Response(JSON.stringify({ items: [] }), {
        status: 200,
        headers: { "content-type": "application/json", "x-request-id": "up-req-1" },
      }),
    );

    const req = new NextRequest(`${EDGE_BASE}/api/bff/admin/students?page=1`, {
      headers: {
        cookie: "admin_token=session-token",
        "x-request-id": "req-123",
      },
    });

    const res = await bffGet(req, { params: { path: ["admin", "students"] } });

    expect(res.status).toBe(200);
    const body = await res.json();
    expect(body.items).toEqual([]);

    expect(fetchMock).toHaveBeenCalledOnce();
    const [url, init] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect(String(url)).toBe(`${API_BASE}/api/admin/students?page=1`);

    const headers = new Headers(init.headers as HeadersInit);
    expect(headers.get("authorization")).toBe("Bearer session-token");
    expect(headers.get("x-request-id")).toBe("req-123");
  });

  it("normalizes upstream errors", async () => {
    vi.spyOn(global, "fetch").mockResolvedValue(
      new Response(JSON.stringify({ detail: "backend failed" }), {
        status: 500,
        headers: { "content-type": "application/json", "x-request-id": "up-err-1" },
      }),
    );

    const req = new NextRequest(`${EDGE_BASE}/api/bff/admin/enrollments`, {
      headers: { cookie: "admin_token=session-token" },
    });

    const res = await bffGet(req, { params: { path: ["admin", "enrollments"] } });

    expect(res.status).toBe(500);
    const body = await res.json();
    expect(body.error.code).toBe("UPSTREAM_ERROR");
    expect(body.error.detail).toBe("backend failed");
    expect(body.error.request_id).toBe("up-err-1");
  });

  it("forwards request body for mutating methods", async () => {
    const fetchMock = vi.spyOn(global, "fetch").mockResolvedValue(
      new Response(JSON.stringify({ ok: true }), {
        status: 200,
        headers: { "content-type": "application/json" },
      }),
    );

    const req = new NextRequest(`${EDGE_BASE}/api/bff/v1/admin/tenants`, {
      method: "POST",
      headers: {
        cookie: "admin_token=session-token",
        "content-type": "application/json",
      },
      body: JSON.stringify({ slug: "t1" }),
    });

    const res = await bffPost(req, { params: { path: ["v1", "admin", "tenants"] } });

    expect(res.status).toBe(200);
    const [, init] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect(init.body).toBe(JSON.stringify({ slug: "t1" }));
  });
});
