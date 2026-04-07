import { NextRequest, NextResponse } from "next/server";
import { getServerApiBaseUrl } from "@/shared/server/runtime-env";

function unauthorized() {
  return NextResponse.json({ detail: "Authentication required" }, { status: 401 });
}

async function proxy(request: NextRequest, method: "GET" | "POST") {
  const apiBase = getServerApiBaseUrl();
  const token = request.cookies.get("admin_token")?.value;
  if (!token) return unauthorized();

  const headers = new Headers();
  headers.set("authorization", `Bearer ${token}`);
  headers.set("content-type", "application/json");

  const upstream = await fetch(new URL("/api/admin/i18n/languages", apiBase), {
    method,
    headers,
    body: method === "POST" ? await request.text() : undefined,
    cache: "no-store",
  });

  const contentType = upstream.headers.get("content-type") ?? "";
  if (contentType.includes("application/json")) {
    const payload = await upstream.json();
    return NextResponse.json(payload, { status: upstream.status });
  }
  const text = await upstream.text();
  return new NextResponse(text, { status: upstream.status });
}

export async function GET(request: NextRequest) {
  try {
    return await proxy(request, "GET");
  } catch {
    return NextResponse.json({ detail: "Upstream unavailable" }, { status: 503 });
  }
}

export async function POST(request: NextRequest) {
  try {
    return await proxy(request, "POST");
  } catch {
    return NextResponse.json({ detail: "Upstream unavailable" }, { status: 503 });
  }
}
