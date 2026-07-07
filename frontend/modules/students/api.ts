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

type StudentProfileApiResponse = {
  id: number | string;
  tenant_id: number | string;
  person_id: number | string;
  student_number: string;
  cohort_year: number | null;
  academic_level?: string | null;
  current_status: Student["status"];
  admission_source?: string;
  metadata_json?: Record<string, unknown>;
  version?: number;
  created_at: string;
  updated_at: string;
};

type StudentProfileMutationApiResponse = {
  student: StudentProfileApiResponse;
  idempotent_replay: boolean;
};

function normalizeStudent(profile: StudentProfileApiResponse): Student {
  const personId = String(profile.person_id);
  const displayName =
    typeof profile.metadata_json?.display_name === "string" && profile.metadata_json.display_name.trim()
      ? profile.metadata_json.display_name.trim()
      : `Person #${personId}`;
  const [firstName, ...lastNameParts] = displayName.split(/\s+/);
  const email =
    typeof profile.metadata_json?.email === "string" && profile.metadata_json.email.trim()
      ? profile.metadata_json.email.trim()
      : "-";

  return {
    id: String(profile.id),
    student_number: profile.student_number,
    first_name: firstName || `Person #${personId}`,
    last_name: lastNameParts.join(" "),
    email,
    status: profile.current_status,
    current_status: profile.current_status,
    tenant_id: String(profile.tenant_id),
    program: typeof profile.academic_level === "string" ? profile.academic_level : null,
    enrollment_year: profile.cohort_year,
    version: profile.version,
    created_at: profile.created_at,
    updated_at: profile.updated_at,
  };
}

function normalizeStudentPage(response: PaginatedResponse<StudentProfileApiResponse>): PaginatedResponse<Student> {
  return {
    ...response,
    items: response.items.map(normalizeStudent),
  };
}

export const studentsApi = {
  list: (params?: {
    page?: number;
    page_size?: number;
    search?: string;
    status?: string;
    tenant_id?: string;
  }) => apiGet<PaginatedResponse<StudentProfileApiResponse>>(BASE, params).then(normalizeStudentPage),

  get: (id: string) => apiGet<StudentProfileApiResponse>(`${BASE}/${id}`).then(normalizeStudent),

  create: (payload: CreateStudentPayload) =>
    apiPost<StudentProfileMutationApiResponse>(BASE, payload).then((response) => normalizeStudent(response.student)),

  update: (id: string, payload: UpdateStudentPayload) =>
    apiPatch<StudentProfileApiResponse>(`${BASE}/${id}`, payload).then(normalizeStudent),

  changeStatus: (id: string, payload: ChangeStudentStatusPayload) =>
    apiPatch<StudentProfileMutationResponse>(`${BASE}/${id}/status`, payload).then((response) =>
      normalizeStudent(response.student as unknown as StudentProfileApiResponse),
    ),

  delete: (id: string) => apiDelete<void>(`${BASE}/${id}`),

  getActiveProgram: (id: string) => apiGet<StudentProgramBinding | null>(`${BASE}/${id}/program`),

  bindProgram: (id: string, payload: BindStudentProgramPayload) =>
    apiPost<StudentProgramBindingMutationResponse>(`${BASE}/${id}/program-bindings`, payload)
      .then((response) => response.binding),
};
