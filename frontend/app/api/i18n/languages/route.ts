import { NextResponse } from "next/server";

const API_BASE = process.env.API_BASE_URL ?? process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export async function GET() {
  try {
    const upstream = await fetch(new URL("/api/i18n/languages", API_BASE), {
      method: "GET",
      cache: "no-store",
      headers: { "Content-Type": "application/json" },
    });

    const text = await upstream.text();
    const payload = text ? JSON.parse(text) : {};
    return NextResponse.json(payload, { status: upstream.status });
  } catch {
    return NextResponse.json({ languages: [], default_language: "ru" }, { status: 200 });
  }
}
