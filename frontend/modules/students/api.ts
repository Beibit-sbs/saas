import { apiDelete, apiGet, apiPatch, apiPost } from "@/shared/api/client";
import type { PaginatedResponse } from "@/shared/api/types";
import type {
  BindStudentProgramPayload,
  ChangeStudentStatusPayload,
  CreateStudentPayload,
  Student,
  StudentProgramBinding,
  StudentProgramBindingMutationResponse,
  StudentProfileMutationResponse,
  UpdateStudentPayload,
} from "./types";

const BASE = "/api/admin/students";

export const studentsApi = {
  list: (params?: {
    page?: number;
    page_size?: number;
    search?: string;
    status?: string;
    tenant_id?: string;
  }) => apiGet<PaginatedResponse<Student>>(BASE, params),

  get: (id: string) => apiGet<Student>(`${BASE}/${id}`),

  create: (payload: CreateStudentPayload) => apiPost<Student>(BASE, payload),

  update: (id: string, payload: UpdateStudentPayload) =>
    apiPatch<Student>(`${BASE}/${id}`, payload),

  changeStatus: (id: string, payload: ChangeStudentStatusPayload) =>
    apiPatch<StudentProfileMutationResponse>(`${BASE}/${id}/status`, payload)
      .then((response) => response.student),

  delete: (id: string) => apiDelete<void>(`${BASE}/${id}`),

  getActiveProgram: (id: string) => apiGet<StudentProgramBinding | null>(`${BASE}/${id}/program`),

  bindProgram: (id: string, payload: BindStudentProgramPayload) =>
    apiPost<StudentProgramBindingMutationResponse>(`${BASE}/${id}/program-bindings`, payload)
      .then((response) => response.binding),
};
