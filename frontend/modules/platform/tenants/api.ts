import { apiDelete, apiGet, apiPatch, apiPost } from "@/shared/api/client";
import type { PaginatedResponse } from "@/shared/api/types";
import type { CreateTenantPayload, Tenant, UpdateTenantPayload } from "./types";

const BASE = "/api/v1/admin/tenants";

export const tenantsApi = {
  list: (params?: { page?: number; page_size?: number; search?: string; status?: string }) =>
    apiGet<PaginatedResponse<Tenant>>(BASE, params),

  get: (id: string) => apiGet<Tenant>(`${BASE}/${id}`),

  create: (payload: CreateTenantPayload) => apiPost<Tenant>(BASE, payload),

  update: (id: string, payload: UpdateTenantPayload) => apiPatch<Tenant>(`${BASE}/${id}`, payload),

  suspend: (id: string) => apiPost<Tenant>(`${BASE}/${id}/suspend`, {}),

  activate: (id: string) => apiPost<Tenant>(`${BASE}/${id}/activate`, {}),

  delete: (id: string) => apiDelete<void>(`${BASE}/${id}`),
};
