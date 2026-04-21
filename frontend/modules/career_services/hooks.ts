import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiGet, apiPatch, apiPost } from "@/shared/api/client";
import type {
  CareerOpportunityCreatePayload,
  CareerOpportunityItemResponse,
  CareerOpportunityListResponse,
  CareerOpportunityStatus,
  CareerOpportunityStatusUpdatePayload,
} from "./types";

const BASE = "/api/admin/career-services";
const CAREER_KEY = "career-opportunities";

export function useCareerOpportunities(status?: CareerOpportunityStatus, studentId?: number) {
  const params: Record<string, string | number> = {};
  if (status) params.status = status;
  if (studentId) params.student_id = studentId;

  return useQuery({
    queryKey: [CAREER_KEY, status ?? "all", studentId ?? "all"],
    queryFn: () =>
      apiGet<CareerOpportunityListResponse>(
        BASE,
        Object.keys(params).length > 0 ? params : undefined,
      ),
  });
}

export function useCreateCareerOpportunity() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: CareerOpportunityCreatePayload) =>
      apiPost<CareerOpportunityItemResponse>(BASE, payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: [CAREER_KEY] }),
  });
}

export function useUpdateCareerOpportunityStatus() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({
      opportunityId,
      payload,
    }: {
      opportunityId: number;
      payload: CareerOpportunityStatusUpdatePayload;
    }) => apiPatch<CareerOpportunityItemResponse>(`${BASE}/${opportunityId}/status`, payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: [CAREER_KEY] }),
  });
}
