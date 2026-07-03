import type { ApiError, RequestConfig } from "./types";
import { emitBackendUnavailable, emitSessionInvalid } from "@/shared/auth/session-events";

const REQUEST_TIMEOUT_MS = 10_000;
const API_DEBUG = process.env.NEXT_PUBLIC_API_DEBUG === "1";

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
  if (path.startsWith("/platform/")) return `/api/bff${path}`;
  // Route all versioned /api/v1/* backend routes through the BFF proxy. This
  // covers platform admin/ops (/api/v1/admin, /api/v1/platform) as well as the
  // domain runtime-shell routers mounted under /api/v1 (e.g.
  // /api/v1/quality-accreditation, /api/v1/student-success,
  // /api/v1/academic-operations, /api/v1/reporting, /api/v1/executive-governance).
  if (path.startsWith("/api/v1/")) return `/api/bff/${path.slice("/api/".length)}`;
  // Academic Operations sub-runtime routers are mounted under a non-standard
  // backend prefix (/api/academic-operations/runtime/*) instead of /api/v1;
  // proxy them through the BFF as well so the runtime sub-pages can load.
  if (path.startsWith("/api/academic-operations/runtime/")) return `/api/bff/${path.slice("/api/".length)}`;
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

function isRequestConfig(value: unknown): value is RequestConfig {
  return !!value && typeof value === "object" && ("headers" in value || "signal" in value);
}

async function fetchWithTimeout(input: string, init: RequestInit, signal?: AbortSignal): Promise<Response> {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);

  let onAbort: (() => void) | undefined;
  if (signal) {
    if (signal.aborted) {
      clearTimeout(timeoutId);
      controller.abort();
    } else {
      onAbort = () => controller.abort();
      signal.addEventListener("abort", onAbort, { once: true });
    }
  }

  try {
    return await fetch(input, { ...init, signal: controller.signal });
  } catch (error) {
    if (error instanceof Error && error.name === "AbortError") {
      throw new Error(`Request timeout after ${REQUEST_TIMEOUT_MS}ms`);
    }
    throw error;
  } finally {
    clearTimeout(timeoutId);
    if (signal && onAbort) {
      signal.removeEventListener("abort", onAbort);
    }
  }
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return !!value && typeof value === "object" && !Array.isArray(value);
}

function extractError(body: unknown, status: number): ApiError {
  if (isRecord(body)) {
    const detail = body.detail;
    if (typeof detail === "string" && detail.trim().length > 0) {
      return {
        status,
        detail,
        code: typeof body.code === "string" ? body.code : undefined,
      };
    }

    const nestedError = body.error;
    if (isRecord(nestedError)) {
      const nestedDetail = nestedError.detail;
      if (typeof nestedDetail === "string" && nestedDetail.trim().length > 0) {
        return {
          status,
          detail: nestedDetail,
          code: typeof nestedError.code === "string" ? nestedError.code : undefined,
        };
      }
    }
  }

  return {
    status,
    detail: `HTTP ${status}`,
  };
}

function shouldEmitBackendUnavailable(path: string, status: number, code?: string): boolean {
  if (status !== 503) return false;
  if (code !== "BACKEND_UNAVAILABLE") return false;
  // Ops console regularly tolerates partial data; avoid global noisy toasts for these probes.
  return !(
    path.startsWith("/health")
    || path.startsWith("/metrics")
    || path.startsWith("/api/bff/health")
    || path.startsWith("/api/bff/metrics")
  );
}

function debugApiError(payload: {
  requestPath: string;
  status: number;
  body: unknown;
  mapped: ApiError;
}) {
  if (!API_DEBUG) return;
  // Dev-only diagnostics — sanitised: raw body/detail stripped to prevent leaking internals.
  const safe = {
    requestPath: payload.requestPath,
    status: payload.status,
    code: payload.mapped?.code,
  };
  try {
    console.error("[api-debug:error]", JSON.stringify(safe));
  } catch {
    console.error("[api-debug:error]", safe);
  }
}

async function parseResponse<T>(res: Response, requestPath: string): Promise<T> {
  if (res.status === 204) return undefined as unknown as T;

  let body: unknown;
  try {
    body = await res.json();
  } catch {
    body = { detail: res.statusText };
  }

  if (!res.ok) {
    const mapped = extractError(body, res.status);
    debugApiError({
      requestPath,
      status: res.status,
      body,
      mapped,
    });
    if (res.status === 401) {
      emitSessionInvalid({ status: res.status });
    }
    if (shouldEmitBackendUnavailable(requestPath, res.status, mapped.code)) {
      emitBackendUnavailable({ status: res.status });
    }
    throw new ApiRequestError(mapped);
  }

  return body as T;
}

export async function apiGet<T>(
  path: string,
  paramsOrConfig?: Record<string, string | number | boolean | undefined> | RequestConfig,
  signal?: AbortSignal,
): Promise<T> {
  const bffPath = mapToBffPath(path);
  const config = isRequestConfig(paramsOrConfig) ? paramsOrConfig : undefined;
  const params = config ? undefined : paramsOrConfig;
  const effectiveSignal = config?.signal ?? signal;
  const query = new URLSearchParams();
  if (params) {
    for (const [k, v] of Object.entries(params)) {
      if (v !== undefined && v !== null && v !== "") {
        query.set(k, String(v));
      }
    }
  }
  const requestPath = query.size > 0 ? `${bffPath}?${query.toString()}` : bffPath;
  const res = await fetchWithTimeout(requestPath, {
    method: "GET",
    headers: buildHeaders(config?.headers),
    credentials: "include",
  }, effectiveSignal);
  return parseResponse<T>(res, bffPath);
}

export async function apiPost<T>(path: string, body?: unknown, config?: RequestConfig): Promise<T> {
  const res = await fetchWithTimeout(mapToBffPath(path), {
    method: "POST",
    headers: buildHeaders(config?.headers),
    credentials: "include",
    body: body !== undefined ? JSON.stringify(body) : undefined,
  }, config?.signal);
  return parseResponse<T>(res, path);
}

export async function apiPut<T>(path: string, body?: unknown, config?: RequestConfig): Promise<T> {
  const res = await fetchWithTimeout(mapToBffPath(path), {
    method: "PUT",
    headers: buildHeaders(config?.headers),
    credentials: "include",
    body: body !== undefined ? JSON.stringify(body) : undefined,
  }, config?.signal);
  return parseResponse<T>(res, path);
}

export async function apiPatch<T>(path: string, body?: unknown, config?: RequestConfig): Promise<T> {
  const res = await fetchWithTimeout(mapToBffPath(path), {
    method: "PATCH",
    headers: buildHeaders(config?.headers),
    credentials: "include",
    body: body !== undefined ? JSON.stringify(body) : undefined,
  }, config?.signal);
  return parseResponse<T>(res, path);
}

export async function apiDelete<T = void>(path: string, config?: RequestConfig): Promise<T> {
  const res = await fetchWithTimeout(mapToBffPath(path), {
    method: "DELETE",
    headers: buildHeaders(config?.headers),
    credentials: "include",
  }, config?.signal);
  return parseResponse<T>(res, path);
}

export const apiClient = {
  get: apiGet,
  post: apiPost,
  put: apiPut,
  patch: apiPatch,
  delete: apiDelete,
};
