import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { schedulingApi } from "./api";
import type {
  AttendanceStatus,
  CreateLessonInstancePayload,
  CourseSection,
  CreateSectionPayload,
} from "./types";

export const SECTIONS_KEY = "sections";
export const LESSONS_KEY = "section-lessons";
export const LESSON_ATTENDANCE_KEY = "lesson-attendance";
export const STUDENT_LATEST_RISK_KEY = "student-latest-risk";
export const STUDENT_RISK_HISTORY_KEY = "student-risk-history";
export const INTERVENTION_RISK_SUMMARY_KEY = "intervention-risk-summary";

export function useSections(params?: {
  page?: number;
  page_size?: number;
  semester?: string;
  status?: string;
  tenant_id?: string;
}) {
  return useQuery({
    queryKey: [SECTIONS_KEY, params],
    queryFn: () => schedulingApi.list(params),
  });
}

export function useSection(id: string) {
  return useQuery({
    queryKey: [SECTIONS_KEY, id],
    queryFn: () => schedulingApi.get(id),
    enabled: !!id,
  });
}

export function useCreateSection() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: CreateSectionPayload) => schedulingApi.create(payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: [SECTIONS_KEY] }),
  });
}

export function useUpdateSection() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: Partial<CreateSectionPayload & { status: CourseSection["status"] }> }) =>
      schedulingApi.update(id, payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: [SECTIONS_KEY] }),
  });
}

export function useLessonAttendance(lessonInstanceId: string) {
  return useQuery({
    queryKey: [LESSON_ATTENDANCE_KEY, lessonInstanceId],
    queryFn: () => schedulingApi.listLessonAttendance(lessonInstanceId),
    enabled: !!lessonInstanceId,
  });
}

export function useSectionLessons(sectionId: string) {
  return useQuery({
    queryKey: [LESSONS_KEY, sectionId],
    queryFn: () => schedulingApi.listSectionLessons(sectionId),
    enabled: !!sectionId,
  });
}

export function useCreateSectionLesson(sectionId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: CreateLessonInstancePayload) =>
      schedulingApi.createSectionLesson(sectionId, payload),
    onSuccess: async () => {
      await qc.invalidateQueries({ queryKey: [LESSONS_KEY, sectionId] });
    },
  });
}

export function useUpsertLessonAttendance(lessonInstanceId: string) {
  const qc = useQueryClient();

  return useMutation({
    mutationFn: (payload: { student_profile_id: number; attendance_status: AttendanceStatus }) =>
      schedulingApi.upsertLessonAttendance(lessonInstanceId, payload),
    onSuccess: async () => {
      await qc.invalidateQueries({ queryKey: [LESSON_ATTENDANCE_KEY, lessonInstanceId] });
    },
  });
}

export function useStudentLatestRisk(studentProfileId: number | null) {
  return useQuery({
    queryKey: [STUDENT_LATEST_RISK_KEY, studentProfileId],
    queryFn: () => schedulingApi.getStudentLatestRisk(String(studentProfileId)),
    enabled: studentProfileId != null,
    retry: false,
  });
}

export function useStudentRiskHistory(studentProfileId: number | null, params?: { page?: number; page_size?: number }) {
  return useQuery({
    queryKey: [STUDENT_RISK_HISTORY_KEY, studentProfileId, params],
    queryFn: () => schedulingApi.getStudentRiskHistory(String(studentProfileId), params),
    enabled: studentProfileId != null,
    retry: false,
  });
}

export function useInterventionRiskSummary() {
  return useQuery({
    queryKey: [INTERVENTION_RISK_SUMMARY_KEY],
    queryFn: () => schedulingApi.getInterventionRiskSummary(),
    retry: false,
  });
}

export function useAttendanceTrends(sectionId: string, weeks: number = 4) {
  return useQuery({
    queryKey: ["attendance-trends", sectionId, weeks],
    queryFn: () => schedulingApi.getAttendanceTrends(sectionId, weeks),
    retry: false,
  });
}
