import type { ApiError } from "./types";
import { emitBackendUnavailable, emitSessionInvalid } from "@/shared/auth/session-events";

export class ApiRequestError extends Error {
  status: number;
  code?: string;

  constructor(err: ApiError) {
    super(err.detail ?? `HTTP ${err.status}`);
    this.status = err.status;
    this.code = err.code;
  }
}

function mapToBffPath(path: string): string {
  if (path.startsWith("/api/bff/")) return path;
  if (path.startsWith("/api/v1/admin/")) return `/api/bff/${path.slice("/api/".length)}`;
  if (path.startsWith("/api/admin/")) return `/api/bff/${path.slice("/api/".length)}`;
  if (path === "/health" || path.startsWith("/health/")) return `/api/bff${path}`;
  if (path === "/metrics" || path.startsWith("/metrics/")) return `/api/bff${path}`;
  return path;
}

function buildHeaders(extra?: Record<string, string>): Record<string, string> {
  return {
    "Content-Type": "application/json",
    ...extra,
  };
}

async function parseResponse<T>(res: Response): Promise<T> {
  if (res.status === 204) return undefined as unknown as T;

  let body: unknown;
  try {
    body = await res.json();
  } catch {
    body = { detail: res.statusText };
  }

  if (!res.ok) {
    if (res.status === 401) {
      emitSessionInvalid({ status: res.status });
    }
    if (res.status === 503) {
      emitBackendUnavailable({ status: res.status });
    }
    const err = body as Partial<ApiError>;
    throw new ApiRequestError({
      status: res.status,
      detail: err.detail ?? String(body),
      code: err.code,
    });
  }

  return body as T;
}

export async function apiGet<T>(
  path: string,
  params?: Record<string, string | number | boolean | undefined>,
  signal?: AbortSignal,
): Promise<T> {
  const bffPath = mapToBffPath(path);
  const url = new URL(bffPath, typeof window !== "undefined" ? window.location.origin : "http://localhost");
  if (params) {
    for (const [k, v] of Object.entries(params)) {
      if (v !== undefined && v !== null && v !== "") {
        url.searchParams.set(k, String(v));
      }
    }
  }
  const res = await fetch(url.pathname + url.search, {
    method: "GET",
    headers: buildHeaders(),
    credentials: "include",
    signal,
  });
  return parseResponse<T>(res);
}

export async function apiPost<T>(path: string, body?: unknown, signal?: AbortSignal): Promise<T> {
  const res = await fetch(mapToBffPath(path), {
    method: "POST",
    headers: buildHeaders(),
    credentials: "include",
    body: body !== undefined ? JSON.stringify(body) : undefined,
    signal,
  });
  return parseResponse<T>(res);
}

export async function apiPut<T>(path: string, body?: unknown): Promise<T> {
  const res = await fetch(mapToBffPath(path), {
    method: "PUT",
    headers: buildHeaders(),
    credentials: "include",
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });
  return parseResponse<T>(res);
}

export async function apiPatch<T>(path: string, body?: unknown): Promise<T> {
  const res = await fetch(mapToBffPath(path), {
    method: "PATCH",
    headers: buildHeaders(),
    credentials: "include",
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });
  return parseResponse<T>(res);
}

export async function apiDelete<T = void>(path: string): Promise<T> {
  const res = await fetch(mapToBffPath(path), {
    method: "DELETE",
    headers: buildHeaders(),
    credentials: "include",
  });
  return parseResponse<T>(res);
}
