import { apiGet, apiPost } from "@/shared/api/client";
import type { PaginatedResponse } from "@/shared/api/types";
import type { Job, TriggerJobPayload } from "./types";

const BASE = "/api/bff/admin/jobs";

type BackendJob = {
  id: number;
  tenant_id: number;
  job_type: string;
  status: "queued" | "running" | "succeeded" | "failed" | "cancelled";
  error_message: string | null;
  created_at: string;
  started_at: string | null;
  finished_at: string | null;
  payload_json?: Record<string, unknown>;
  result_json?: Record<string, unknown> | null;
};

type BackendJobList = { jobs?: BackendJob[] };
type BackendJobItem = { job?: BackendJob };

function toJob(row: BackendJob): Job {
  return {
    id: String(row.id),
    job_type: String(row.job_type),
    status: row.status === "succeeded" ? "completed" : row.status,
    tenant_id: row.tenant_id != null ? String(row.tenant_id) : null,
    progress: null,
    error_message: row.error_message ?? null,
    created_at: String(row.created_at),
    started_at: row.started_at ?? null,
    completed_at: row.finished_at ?? null,
    metadata: row.payload_json ?? {},
  };
}

export const jobsApi = {
  list: async (params?: { page?: number; page_size?: number; status?: string; job_type?: string }) => {
    const payload = await apiGet<BackendJobList>(BASE, params);
    const rows = Array.isArray(payload?.jobs) ? payload.jobs : [];
    const statusFilter = String(params?.status ?? "").trim().toLowerCase();
    const typeFilter = String(params?.job_type ?? "").trim().toLowerCase();

    const filtered = rows.filter((row) => {
      const normalized = row.status === "succeeded" ? "completed" : row.status;
      if (statusFilter && normalized !== statusFilter) return false;
      if (typeFilter && !String(row.job_type).toLowerCase().includes(typeFilter)) return false;
      return true;
    });

    const page = Math.max(1, Number(params?.page ?? 1));
    const pageSize = Math.max(1, Number(params?.page_size ?? 20));
    const start = (page - 1) * pageSize;

    return {
      total: filtered.length,
      page,
      page_size: pageSize,
      items: filtered.slice(start, start + pageSize).map(toJob),
    } as PaginatedResponse<Job>;
  },

  listQueue: async (
    queuePath?: string,
    params?: { page?: number; page_size?: number; status?: string; job_type?: string },
  ) => {
    const suffix = queuePath ? `/queue/${queuePath.replace(/^\/+/, "")}` : "/queue";
    const payload = await apiGet<BackendJobList>(`${BASE}${suffix}`, params);
    const rows = Array.isArray(payload?.jobs) ? payload.jobs : [];
    const page = Math.max(1, Number(params?.page ?? 1));
    const pageSize = Math.max(1, Number(params?.page_size ?? 20));
    const start = (page - 1) * pageSize;
    return {
      total: rows.length,
      page,
      page_size: pageSize,
      items: rows.slice(start, start + pageSize).map(toJob),
    } as PaginatedResponse<Job>;
  },

  listHistory: async (params?: { page?: number; page_size?: number; status?: string; job_type?: string }) => {
    const payload = await apiGet<BackendJobList>(`${BASE}/history`, params);
    const rows = Array.isArray(payload?.jobs) ? payload.jobs : [];
    const page = Math.max(1, Number(params?.page ?? 1));
    const pageSize = Math.max(1, Number(params?.page_size ?? 20));
    const start = (page - 1) * pageSize;
    return {
      total: rows.length,
      page,
      page_size: pageSize,
      items: rows.slice(start, start + pageSize).map(toJob),
    } as PaginatedResponse<Job>;
  },

  get: async (id: string) => {
    const payload = await apiGet<BackendJobItem>(`${BASE}/${id}`);
    if (!payload?.job) {
      throw new Error(`Job ${id} not found`);
    }
    return toJob(payload.job);
  },

  trigger: async (payload: TriggerJobPayload) => {
    const created = await apiPost<BackendJobItem>(BASE, {
      job_type: payload.job_type,
      payload: payload.metadata ?? {},
      max_retries: 3,
    });
    if (!created?.job) {
      throw new Error("Job creation failed");
    }
    return toJob(created.job);
  },

  retry: async (id: string) => {
    const result = await apiPost<BackendJobItem>(`${BASE}/${id}/retry`, {});
    if (!result?.job) {
      throw new Error(`Job ${id} not found`);
    }
    return toJob(result.job);
  },

  cancel: async (id: string) => {
    const result = await apiPost<BackendJobItem>(`${BASE}/${id}/cancel`, {});
    if (!result?.job) {
      throw new Error(`Job ${id} not found`);
    }
    return toJob(result.job);
  },
};
