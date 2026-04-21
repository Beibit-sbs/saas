import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiGet, apiPatch, apiPost } from "@/shared/api/client";
import type {
  AdvisingSessionCreatePayload,
  AdvisingSessionItemResponse,
  AdvisingSessionListResponse,
  AdvisingSessionStatus,
  AdvisingSessionStatusUpdatePayload,
} from "./types";

const BASE = "/api/admin/advising";
const ADVISING_KEY = "advising-sessions";

export function useAdvisingSessions(
  status?: AdvisingSessionStatus,
  studentId?: number,
) {
  const params: Record<string, string | number> = {};
  if (status) params.status = status;
  if (studentId) params.student_id = studentId;
  return useQuery({
    queryKey: [ADVISING_KEY, status ?? "all", studentId ?? "all"],
    queryFn: () =>
      apiGet<AdvisingSessionListResponse>(
        BASE,
        Object.keys(params).length > 0 ? params : undefined,
      ),
  });
}

export function useCreateAdvisingSession() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: AdvisingSessionCreatePayload) =>
      apiPost<AdvisingSessionItemResponse>(BASE, payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: [ADVISING_KEY] }),
  });
}

export function useUpdateAdvisingSessionStatus() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({
      sessionId,
      payload,
    }: {
      sessionId: number;
      payload: AdvisingSessionStatusUpdatePayload;
    }) => apiPatch<AdvisingSessionItemResponse>(`${BASE}/${sessionId}/status`, payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: [ADVISING_KEY] }),
  });
}
