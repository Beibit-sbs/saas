import { NextRequest, NextResponse } from "next/server";
import { getServerApiBaseUrl } from "@/shared/server/runtime-env";

type Ctx = { params: { code: string } };

function unauthorized() {
  return NextResponse.json({ detail: "Authentication required" }, { status: 401 });
}

async function proxy(request: NextRequest, context: Ctx, method: "PATCH" | "DELETE") {
  const apiBase = getServerApiBaseUrl();
  const token = request.cookies.get("admin_token")?.value;
  if (!token) return unauthorized();

  const code = encodeURIComponent(String(context.params.code || "").trim());
  const headers = new Headers();
  headers.set("authorization", `Bearer ${token}`);
  if (method === "PATCH") {
    headers.set("content-type", "application/json");
  }

  const upstream = await fetch(new URL(`/api/admin/i18n/languages/${code}`, apiBase), {
    method,
    headers,
    body: method === "PATCH" ? await request.text() : undefined,
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

export async function PATCH(request: NextRequest, context: Ctx) {
  try {
    return await proxy(request, context, "PATCH");
  } catch {
    return NextResponse.json({ detail: "Upstream unavailable" }, { status: 503 });
  }
}

export async function DELETE(request: NextRequest, context: Ctx) {
  try {
    return await proxy(request, context, "DELETE");
  } catch {
    return NextResponse.json({ detail: "Upstream unavailable" }, { status: 503 });
  }
}
