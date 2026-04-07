import { apiDelete, apiGet, apiPost, apiPut } from "@/shared/api/client";
import type { PaginatedResponse } from "@/shared/api/types";
import type { CreateTenantPayload, Tenant, UpdateTenantPayload } from "./types";

const BASE = "/api/admin/tenants";

type BackendTenant = {
  id: number;
  slug: string;
  name: string;
  status: string;
  plan_id: number;
  created_at: string;
  updated_at: string;
};

type BackendTenantList = { tenants?: BackendTenant[] };
type BackendTenantItem = { tenant?: BackendTenant };

function toTenant(input: BackendTenant): Tenant {
  return {
    id: String(input.id),
    slug: String(input.slug),
    display_name: String(input.name),
    plan: String(input.plan_id ?? 1),
    status: (String(input.status || "active") as Tenant["status"]),
    max_students: 0,
    current_students: 0,
    created_at: String(input.created_at),
    updated_at: String(input.updated_at),
  };
}

export const tenantsApi = {
  list: async (params?: { page?: number; page_size?: number; search?: string; status?: string }) => {
    const payload = await apiGet<BackendTenantList>(BASE, params);
    const rows = Array.isArray(payload?.tenants) ? payload.tenants : [];
    const search = String(params?.search ?? "").trim().toLowerCase();
    const status = String(params?.status ?? "").trim().toLowerCase();
    const filtered = rows.filter((row) => {
      if (status && String(row.status).toLowerCase() !== status) return false;
      if (!search) return true;
      return String(row.name).toLowerCase().includes(search) || String(row.slug).toLowerCase().includes(search);
    });

    const page = Math.max(1, Number(params?.page ?? 1));
    const pageSize = Math.max(1, Number(params?.page_size ?? 20));
    const start = (page - 1) * pageSize;
    const pageRows = filtered.slice(start, start + pageSize).map(toTenant);

    return {
      total: filtered.length,
      page,
      page_size: pageSize,
      items: pageRows,
    } as PaginatedResponse<Tenant>;
  },

  get: async (id: string) => {
    const payload = await apiGet<BackendTenantList>(BASE);
    const rows = Array.isArray(payload?.tenants) ? payload.tenants : [];
    const found = rows.find((row) => String(row.id) === String(id));
    if (!found) {
      throw new Error(`Tenant ${id} not found`);
    }
    return toTenant(found);
  },

  create: async (payload: CreateTenantPayload) => {
    const created = await apiPost<BackendTenantItem>(BASE, {
      slug: payload.slug,
      name: payload.display_name,
      status: "active",
      plan_id: Number(payload.plan) || 1,
    });
    return toTenant(created.tenant as BackendTenant);
  },

  update: async (id: string, payload: UpdateTenantPayload) => {
    const updated = await apiPut<BackendTenantItem>(`${BASE}/${id}`, {
      name: payload.display_name,
      status: payload.status,
      plan_id: payload.plan ? Number(payload.plan) : undefined,
    });
    return toTenant(updated.tenant as BackendTenant);
  },

  suspend: (id: string) => tenantsApi.update(id, { status: "suspended" }),

  activate: (id: string) => tenantsApi.update(id, { status: "active" }),

  delete: (id: string) => apiDelete<void>(`${BASE}/${id}`),
};
