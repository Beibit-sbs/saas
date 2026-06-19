import { apiDelete, apiGet, apiPost } from "@/shared/api/client";
import { ApiRequestError } from "@/shared/api/client";
import type { PaginatedResponse } from "@/shared/api/types";
import type { CreateEnrollmentPayload, DropEnrollmentPayload, Enrollment } from "./types";

const BASE = "/api/admin/enrollments";

export const enrollmentsApi = {
  list: (params?: { page?: number; page_size?: number; student_id?: string; student_profile_id?: string; course_id?: string; term_id?: string; section_id?: string; status?: string }) =>
    apiGet<PaginatedResponse<Enrollment>>(BASE, params).catch((error: unknown) => {
      if (error instanceof ApiRequestError && (error.status === 404 || error.status === 405)) {
        return {
          total: 0,
          page: params?.page ?? 1,
          page_size: params?.page_size ?? 20,
          items: [],
        } as PaginatedResponse<Enrollment>;
      }
      throw error;
    }),

  create: (payload: CreateEnrollmentPayload) => apiPost<Enrollment>(BASE, payload),

  drop: (id: string | number, payload: DropEnrollmentPayload) =>
    apiPost<Enrollment>(`${BASE}/${id}/drop`, payload),

  delete: (id: string | number) => apiDelete<void>(`${BASE}/${id}`),
};
