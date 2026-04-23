import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiGet, apiPatch, apiPost } from "@/shared/api/client";
import type {
  DelinquencyCreatePayload,
  DelinquencyEscalationUpdatePayload,
  DelinquencyItemResponse,
  DelinquencyListResponse,
  DelinquencyStatus,
  DelinquencyStatusUpdatePayload,
  EscalationStage,
} from "./types";

const BASE = "/api/admin/delinquency-collections";
const KEY = "delinquency-collections";

export function useDelinquencyRecords(filters?: {
  status?: DelinquencyStatus;
  escalation_stage?: EscalationStage;
}) {
  const params: Record<string, string> = {};
  if (filters?.status) params.status = filters.status;
  if (filters?.escalation_stage) params.escalation_stage = filters.escalation_stage;

  return useQuery({
    queryKey: [KEY, filters?.status ?? "all", filters?.escalation_stage ?? "all"],
    queryFn: () =>
      apiGet<DelinquencyListResponse>(
        BASE,
        Object.keys(params).length > 0 ? params : undefined,
      ),
  });
}

export function useCreateDelinquencyRecord() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: DelinquencyCreatePayload) =>
      apiPost<DelinquencyItemResponse>(BASE, payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: [KEY] }),
  });
}

export function useUpdateDelinquencyStatus() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({
      recordId,
      payload,
    }: {
      recordId: number;
      payload: DelinquencyStatusUpdatePayload;
    }) => apiPatch<DelinquencyItemResponse>(`${BASE}/${recordId}/status`, payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: [KEY] }),
  });
}

export function useUpdateDelinquencyEscalation() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({
      recordId,
      payload,
    }: {
      recordId: number;
      payload: DelinquencyEscalationUpdatePayload;
    }) => apiPatch<DelinquencyItemResponse>(`${BASE}/${recordId}/escalation`, payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: [KEY] }),
  });
}
