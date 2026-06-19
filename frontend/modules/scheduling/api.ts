import { apiGet, apiPatch, apiPost } from "@/shared/api/client";
import { apiPut } from "@/shared/api/client";
import { ApiRequestError } from "@/shared/api/client";
import type { PaginatedResponse } from "@/shared/api/types";
import type {
  CourseSection,
  CreateLessonInstancePayload,
  CreateSectionPayload,
  LessonAttendanceItem,
  LessonAttendanceListResponse,
  LessonInstance,
  LessonInstanceListResponse,
  LessonAttendanceUpsertPayload,
  InterventionRiskSummary,
  StudentLatestRisk,
  StudentRiskHistoryResponse,
  AttendanceTrend,
} from "./types";

const BASE = "/api/admin/scheduling/sections";
const LESSONS_BASE = "/api/admin/scheduling/lessons";

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

  listSectionLessons: (sectionId: string, params?: { page?: number; page_size?: number; status?: string }) =>
    apiGet<LessonInstanceListResponse>(`${BASE}/${sectionId}/lessons`, params),

  createSectionLesson: (sectionId: string, payload: CreateLessonInstancePayload) =>
    apiPost<LessonInstance>(`${BASE}/${sectionId}/lessons`, payload),

  listLessonAttendance: (lessonInstanceId: string) =>
    apiGet<LessonAttendanceListResponse>(`${LESSONS_BASE}/${lessonInstanceId}/attendance`),

  upsertLessonAttendance: (lessonInstanceId: string, payload: LessonAttendanceUpsertPayload) =>
    apiPut<LessonAttendanceItem>(`${LESSONS_BASE}/${lessonInstanceId}/attendance`, payload),

  getStudentLatestRisk: (studentProfileId: string) =>
    apiGet<StudentLatestRisk>(`/api/admin/interventions/risk/students/${studentProfileId}/latest`),

  getStudentRiskHistory: (studentProfileId: string, params?: { page?: number; page_size?: number }) =>
    apiGet<StudentRiskHistoryResponse>(`/api/admin/interventions/risk/students/${studentProfileId}/history`, params),

  getInterventionRiskSummary: () =>
    apiGet<InterventionRiskSummary>("/api/admin/interventions/risk/kpi-summary"),

  getAttendanceTrends: (sectionId: string, weeks?: number) =>
    apiGet<AttendanceTrend>(`${BASE}/${sectionId}/attendance-trends`, { weeks }),
};
