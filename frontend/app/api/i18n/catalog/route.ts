import { NextResponse } from "next/server";
import { getServerApiBaseUrl } from "@/shared/server/runtime-env";

export async function GET() {
  const apiBase = getServerApiBaseUrl();
  try {
    const upstream = await fetch(new URL("/api/i18n/catalog", apiBase), {
      method: "GET",
      cache: "no-store",
      headers: { "Content-Type": "application/json" },
    });

    const text = await upstream.text();
    const payload = text ? JSON.parse(text) : {};
    return NextResponse.json(payload, { status: upstream.status });
  } catch {
    return NextResponse.json({ languages: [] }, { status: 200 });
  }
}
