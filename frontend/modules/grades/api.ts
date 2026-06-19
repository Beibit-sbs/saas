import { apiGet, apiPatch, apiPost } from "@/shared/api/client";
import { ApiRequestError } from "@/shared/api/client";
import type { PaginatedResponse } from "@/shared/api/types";
import type {
  CreateGradingScalePayload,
  Grade,
  GradeMutationResponse,
  GradingScale,
  UpsertGradePayload,
} from "./types";

const BASE = "/api/admin/grades";

function toPositiveNumber(value: string | number): number {
  const parsed = Number(value);
  if (!Number.isInteger(parsed) || parsed <= 0) {
    throw new Error("Expected a positive numeric identifier");
  }
  return parsed;
}

function toGradeCode(payload: UpsertGradePayload): string {
  return (payload.grade_code ?? payload.grade_value ?? "").trim().toUpperCase();
}

export const gradesApi = {
  list: (params?: {
    page?: number;
    page_size?: number;
    student_id?: string;
    student_profile_id?: string;
    course_id?: string;
    term_id?: string;
    section_id?: string;
  }) =>
    apiGet<PaginatedResponse<Grade>>(BASE, {
      page: params?.page,
      page_size: params?.page_size,
      student_profile_id: params?.student_profile_id ?? params?.student_id,
      course_id: params?.course_id,
      term_id: params?.term_id,
      section_id: params?.section_id,
    }).catch((error: unknown) => {
      if (error instanceof ApiRequestError && (error.status === 404 || error.status === 405)) {
        return {
          total: 0,
          page: params?.page ?? 1,
          page_size: params?.page_size ?? 20,
          items: [],
        } as PaginatedResponse<Grade>;
      }
      throw error;
    }),

  submit: (payload: UpsertGradePayload) =>
    apiPost<GradeMutationResponse>(`${BASE}/submit`, {
      enrollment_id: toPositiveNumber(payload.enrollment_id),
      grading_scale_id: toPositiveNumber(payload.grading_scale_id),
      grade_code: toGradeCode(payload),
      grade_points: payload.grade_points ?? payload.numeric_value,
      metadata_json: {},
    }).then((response) => response.grade),

  change: (payload: UpsertGradePayload) =>
    apiPatch<GradeMutationResponse>(`${BASE}/change`, {
      enrollment_id: toPositiveNumber(payload.enrollment_id),
      grading_scale_id: toPositiveNumber(payload.grading_scale_id),
      new_grade_code: toGradeCode(payload),
      new_grade_points: payload.grade_points ?? payload.numeric_value,
      expected_version: payload.expected_version,
      reason: payload.reason ?? "admin_console_grade_update",
      metadata_json: {},
    }).then((response) => response.grade),

  upsert: (payload: UpsertGradePayload) =>
    payload.expected_version ? gradesApi.change(payload) : gradesApi.submit(payload),

  listScales: (params?: { page?: number; page_size?: number; active_only?: boolean }) =>
    apiGet<PaginatedResponse<GradingScale>>(`${BASE}/scales`, {
      page: params?.page,
      page_size: params?.page_size,
      active_only: params?.active_only ?? true,
    }),

  createScale: (payload: CreateGradingScalePayload) =>
    apiPost<GradingScale>(`${BASE}/scales`, payload),
};
