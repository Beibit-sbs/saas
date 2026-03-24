import { apiDelete, apiGet, apiPost } from "@/shared/api/client";
import type { PaginatedResponse } from "@/shared/api/types";
import type { CreateEnrollmentPayload, Enrollment } from "./types";

const BASE = "/api/admin/enrollments";

export const enrollmentsApi = {
  list: (params?: { page?: number; page_size?: number; student_id?: string; section_id?: string; status?: string }) =>
    apiGet<PaginatedResponse<Enrollment>>(BASE, params),

  create: (payload: CreateEnrollmentPayload) => apiPost<Enrollment>(BASE, payload),

  drop: (id: string) => apiPost<Enrollment>(`${BASE}/${id}/drop`, {}),

  delete: (id: string) => apiDelete<void>(`${BASE}/${id}`),
};
