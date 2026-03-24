import { apiGet, apiPut } from "@/shared/api/client";
import type { PaginatedResponse } from "@/shared/api/types";
import type { Grade, UpsertGradePayload } from "./types";

const BASE = "/api/admin/grades";

export const gradesApi = {
  list: (params?: { page?: number; page_size?: number; student_id?: string; section_id?: string }) =>
    apiGet<PaginatedResponse<Grade>>(BASE, params),

  upsert: (payload: UpsertGradePayload) => apiPut<Grade>(BASE, payload),
};
