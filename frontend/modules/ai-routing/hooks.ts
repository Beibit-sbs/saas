import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiDelete, apiGet, apiPost, apiPut } from "@/shared/api/client";
import type {
  AIRoutingPolicy,
  AIRoutingPolicyCreatePayload,
  AIRoutingSelectionLogEntry,
} from "./types";

const BASE = "/api/admin/ai/routing";
const POLICIES_KEY = "ai-routing-policies";
const LOG_KEY = "ai-routing-selection-log";

export function useAIRoutingPolicies() {
  return useQuery({
    queryKey: [POLICIES_KEY],
    queryFn: () => apiGet<AIRoutingPolicy[]>(`${BASE}/policies`),
  });
}

export function useCreateAIRoutingPolicy() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: AIRoutingPolicyCreatePayload) =>
      apiPost<AIRoutingPolicy>(`${BASE}/policies`, payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: [POLICIES_KEY] }),
  });
}

export function useUpdateAIRoutingPolicy() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({
      policyId,
      payload,
    }: {
      policyId: number;
      payload: AIRoutingPolicyCreatePayload;
    }) => apiPut<AIRoutingPolicy>(`${BASE}/policies/${policyId}`, payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: [POLICIES_KEY] }),
  });
}

export function useDeleteAIRoutingPolicy() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (policyId: number) => apiDelete(`${BASE}/policies/${policyId}`),
    onSuccess: () => qc.invalidateQueries({ queryKey: [POLICIES_KEY] }),
  });
}

export function useAIRoutingSelectionLog(limit = 50) {
  return useQuery({
    queryKey: [LOG_KEY, limit],
    queryFn: () =>
      apiGet<AIRoutingSelectionLogEntry[]>(`${BASE}/selection-log`, { limit }),
  });
}
