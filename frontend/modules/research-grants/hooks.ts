import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiGet, apiPatch, apiPost } from "@/shared/api/client";
import type {
  ResearchGrantCreatePayload,
  ResearchGrantItemResponse,
  ResearchGrantListResponse,
  ResearchGrantStatus,
  ResearchGrantStatusUpdatePayload,
} from "./types";

const BASE = "/api/admin/research/grants";
const GRANT_KEY = "research-grants";

export function useResearchGrants(status?: ResearchGrantStatus) {
  const params: Record<string, string> = {};
  if (status) params.status = status;

  return useQuery({
    queryKey: [GRANT_KEY, status ?? "all"],
    queryFn: () =>
      apiGet<ResearchGrantListResponse>(
        BASE,
        Object.keys(params).length > 0 ? params : undefined,
      ),
  });
}

export function useCreateResearchGrant() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: ResearchGrantCreatePayload) =>
      apiPost<ResearchGrantItemResponse>(BASE, payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: [GRANT_KEY] }),
  });
}

export function useUpdateResearchGrantStatus() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({
      grantId,
      payload,
    }: {
      grantId: number;
      payload: ResearchGrantStatusUpdatePayload;
    }) =>
      apiPatch<ResearchGrantItemResponse>(`${BASE}/${grantId}/status`, payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: [GRANT_KEY] }),
  });
}
