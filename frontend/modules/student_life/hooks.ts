import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiGet, apiPost } from "@/shared/api/client";
import type {
  AccessibilitySupportCreatePayload,
  AccessibilitySupportListResponse,
  CounselingCaseCreatePayload,
  CounselingCaseListResponse,
  DisciplinaryCaseCreatePayload,
  DisciplinaryCaseListResponse,
  StudentLifeHealthResponse,
  WellbeingCheckinCreatePayload,
  WellbeingCheckinListResponse,
} from "./types";

const BASE = "/api/admin/student-life";
const SL_KEY = "student-life";

export function useStudentLifeHealth() {
  return useQuery({
    queryKey: [SL_KEY, "health"],
    queryFn: () => apiGet<StudentLifeHealthResponse>(`${BASE}/health`),
  });
}

export function useCounselingCases() {
  return useQuery({
    queryKey: [SL_KEY, "counseling-cases"],
    queryFn: () => apiGet<CounselingCaseListResponse>(`${BASE}/counseling-cases`),
  });
}

export function useWellbeingCheckins() {
  return useQuery({
    queryKey: [SL_KEY, "wellbeing-checkins"],
    queryFn: () => apiGet<WellbeingCheckinListResponse>(`${BASE}/wellbeing-checkins`),
  });
}

export function useAccessibilitySupports() {
  return useQuery({
    queryKey: [SL_KEY, "accessibility-supports"],
    queryFn: () => apiGet<AccessibilitySupportListResponse>(`${BASE}/accessibility-supports`),
  });
}

export function useDisciplinaryCases() {
  return useQuery({
    queryKey: [SL_KEY, "disciplinary-cases"],
    queryFn: () => apiGet<DisciplinaryCaseListResponse>(`${BASE}/disciplinary-cases`),
  });
}

export function useCreateCounselingCase() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: CounselingCaseCreatePayload) =>
      apiPost<{ item: { id: number } }>(`${BASE}/counseling-cases`, payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: [SL_KEY] }),
  });
}

export function useCreateWellbeingCheckin() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: WellbeingCheckinCreatePayload) =>
      apiPost<{ item: { id: number } }>(`${BASE}/wellbeing-checkins`, payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: [SL_KEY] }),
  });
}

export function useCreateAccessibilitySupport() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: AccessibilitySupportCreatePayload) =>
      apiPost<{ item: { id: number } }>(`${BASE}/accessibility-supports`, payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: [SL_KEY] }),
  });
}

export function useCreateDisciplinaryCase() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: DisciplinaryCaseCreatePayload) =>
      apiPost<{ item: { id: number } }>(`${BASE}/disciplinary-cases`, payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: [SL_KEY] }),
  });
}
