import { apiGet, apiPost } from "@/shared/api/client";
import type { PaginatedResponse } from "@/shared/api/types";
import type { Job, TriggerJobPayload } from "./types";

const BASE = "/api/v1/admin/jobs";

export const jobsApi = {
  list: (params?: { page?: number; page_size?: number; status?: string; job_type?: string }) =>
    apiGet<PaginatedResponse<Job>>(BASE, params),

  get: (id: string) => apiGet<Job>(`${BASE}/${id}`),

  trigger: (payload: TriggerJobPayload) => apiPost<Job>(BASE, payload),

  retry: (id: string) => apiPost<Job>(`${BASE}/${id}/retry`, {}),

  cancel: (id: string) => apiPost<Job>(`${BASE}/${id}/cancel`, {}),
};
