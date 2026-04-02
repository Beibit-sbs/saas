import { apiGet, apiPatch, apiPost } from "@/shared/api/client";
import { ApiRequestError } from "@/shared/api/client";
import type { PaginatedResponse } from "@/shared/api/types";
import type { CourseSection, CreateSectionPayload } from "./types";

const BASE = "/api/admin/scheduling/sections";

export const schedulingApi = {
  list: (params?: { page?: number; page_size?: number; semester?: string; status?: string; tenant_id?: string }) =>
    apiGet<PaginatedResponse<CourseSection>>(BASE, params).catch((error: unknown) => {
      if (error instanceof ApiRequestError && (error.status === 404 || error.status === 405)) {
        return {
          total: 0,
          page: params?.page ?? 1,
          page_size: params?.page_size ?? 20,
          items: [],
        } as PaginatedResponse<CourseSection>;
      }
      throw error;
    }),

  get: (id: string) => apiGet<CourseSection>(`${BASE}/${id}`),

  create: (payload: CreateSectionPayload) => apiPost<CourseSection>(BASE, payload),

  update: (id: string, payload: Partial<CreateSectionPayload & { status: CourseSection["status"] }>) =>
    apiPatch<CourseSection>(`${BASE}/${id}`, payload),
};
