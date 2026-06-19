import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiGet, apiPost } from "@/shared/api/client";
import type {
  CreateProgramRequirementPayload,
  DegreeProgress,
  DegreeProgressConsistencyReport,
  GraduationEligibility,
  ProgramRequirement,
  ProgramRequirementListResponse,
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

export function useProgramRequirements(params?: { program_id?: string; active_only?: boolean }) {
  return useQuery({
    queryKey: [DEGREE_PROGRESS_KEY, "requirements", params],
    queryFn: () =>
      apiGet<ProgramRequirementListResponse>("/api/admin/degree-progress/requirements", {
        program_id: params?.program_id,
        active_only: params?.active_only ?? true,
      }),
  });
}

export function useCreateProgramRequirement() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: CreateProgramRequirementPayload) =>
      apiPost<ProgramRequirement>("/api/admin/degree-progress/requirements", payload),
    onSuccess: async () => {
      await qc.invalidateQueries({ queryKey: [DEGREE_PROGRESS_KEY, "requirements"] });
      await qc.invalidateQueries({ queryKey: [DEGREE_PROGRESS_KEY, "consistency"] });
    },
  });
}
