import { NextRequest, NextResponse } from "next/server";

const API_BASE = process.env.API_BASE_URL ?? process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

function unauthorized() {
  return NextResponse.json({ detail: "Authentication required" }, { status: 401 });
}

export async function PUT(request: NextRequest) {
  const token = request.cookies.get("admin_token")?.value;
  if (!token) return unauthorized();

  try {
    const upstream = await fetch(`${API_BASE}/api/auth/me/password`, {
      method: "PUT",
      headers: {
        authorization: `Bearer ${token}`,
        "content-type": "application/json",
      },
      body: await request.text(),
      cache: "no-store",
    });

    if (upstream.status === 404) {
      return NextResponse.json(
        { detail: "Password update endpoint is not available in this environment." },
        { status: 501 },
      );
    }

    const contentType = upstream.headers.get("content-type") ?? "";
    if (contentType.includes("application/json")) {
      const payload = await upstream.json();
      return NextResponse.json(payload, { status: upstream.status });
    }

    const text = await upstream.text();
    return new NextResponse(text, { status: upstream.status });
  } catch {
    return NextResponse.json({ detail: "Upstream unavailable" }, { status: 503 });
  }
}
