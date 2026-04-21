import { useQuery } from "@tanstack/react-query";
import { apiGet } from "@/shared/api/client";
import type {
  DegreeProgress,
  DegreeProgressConsistencyReport,
  GraduationEligibility,
} from "./types";

export const DEGREE_PROGRESS_KEY = "degree-progress";

export function useDegreeProgress(studentId: string) {
  return useQuery({
    queryKey: [DEGREE_PROGRESS_KEY, "progress", studentId],
    queryFn: () => apiGet<DegreeProgress>(`/api/admin/students/${studentId}/degree-progress`),
    enabled: !!studentId,
  });
}

export function useGraduationEligibility(studentId: string) {
  return useQuery({
    queryKey: [DEGREE_PROGRESS_KEY, "eligibility", studentId],
    queryFn: () => apiGet<GraduationEligibility>(`/api/admin/students/${studentId}/graduation-eligibility`),
    enabled: !!studentId,
  });
}

export function useDegreeProgressConsistency(enabled = true) {
  return useQuery({
    queryKey: [DEGREE_PROGRESS_KEY, "consistency"],
    queryFn: () => apiGet<DegreeProgressConsistencyReport>("/api/admin/degree-progress/consistency"),
    enabled,
  });
}
