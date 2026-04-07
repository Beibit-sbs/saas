import { NextResponse } from "next/server";
import { getServerApiBaseUrl } from "@/shared/server/runtime-env";

export async function GET() {
  const apiBase = getServerApiBaseUrl();
  try {
    const upstream = await fetch(new URL("/api/public/tenants/login-directory", apiBase), {
      method: "GET",
      cache: "no-store",
      headers: { "Content-Type": "application/json" },
    });

    const contentType = upstream.headers.get("content-type") ?? "";
    if (contentType.includes("application/json")) {
      const payload = await upstream.json();
      return NextResponse.json(payload, { status: upstream.status });
    }

    const text = await upstream.text();
    return new NextResponse(text, { status: upstream.status });
  } catch {
    return NextResponse.json({ tenants: [] }, { status: 200 });
  }
}
