import { NextRequest, NextResponse } from "next/server";
import { getServerApiBaseUrl } from "@/shared/server/runtime-env";

function unauthorized() {
  return NextResponse.json({ detail: "Authentication required" }, { status: 401 });
}

function misconfigured() {
  return NextResponse.json({ detail: "INTERNAL_API_TOKEN is not configured" }, { status: 503 });
}

export async function POST(request: NextRequest) {
  const token = request.cookies.get("app_access_token")?.value ?? request.cookies.get("admin_token")?.value;
  if (!token) return unauthorized();

  const internalApiToken = process.env.INTERNAL_API_TOKEN?.trim();
  if (!internalApiToken) return misconfigured();

  const apiBase = getServerApiBaseUrl();

  try {
    const [outboxRun, moduleJobsRun] = await Promise.all([
      fetch(new URL("/api/v1/internal/events/outbox/run-once", apiBase), {
        method: "POST",
        headers: {
          authorization: `Bearer ${internalApiToken}`,
          "content-type": "application/json",
        },
        cache: "no-store",
      }),
      fetch(new URL("/api/v1/internal/module-jobs/run-once", apiBase), {
        method: "POST",
        headers: {
          authorization: `Bearer ${internalApiToken}`,
          "content-type": "application/json",
        },
        cache: "no-store",
      }),
    ]);

    const outboxPayload = await outboxRun.json().catch(() => ({}));
    const moduleJobsPayload = await moduleJobsRun.json().catch(() => ({}));
    const ok = outboxRun.ok && moduleJobsRun.ok;

    return NextResponse.json(
      {
        outbox: outboxPayload,
        module_jobs: moduleJobsPayload,
      },
      { status: ok ? 200 : 502 },
    );
  } catch {
    return NextResponse.json({ detail: "upstream unavailable" }, { status: 503 });
  }
}