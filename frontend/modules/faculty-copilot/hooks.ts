import { useMutation } from "@tanstack/react-query";
import { apiPost } from "@/shared/api/client";
import type {
  CopilotAnswer,
  FacultyQnAPayload,
  LessonPlanPayload,
  MaterialPackPayload,
} from "./types";

const BASE = "/api/admin/faculty-copilot";

export function useGenerateLessonPlan() {
  return useMutation({
    mutationFn: (payload: LessonPlanPayload) =>
      apiPost<CopilotAnswer>(`${BASE}/lesson-plan`, payload),
  });
}

export function useGenerateMaterialPack() {
  return useMutation({
    mutationFn: (payload: MaterialPackPayload) =>
      apiPost<CopilotAnswer>(`${BASE}/materials`, payload),
  });
}

export function useFacultyQnA() {
  return useMutation({
    mutationFn: (payload: FacultyQnAPayload) =>
      apiPost<CopilotAnswer>(`${BASE}/qna`, payload),
  });
}
