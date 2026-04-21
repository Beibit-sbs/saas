import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiGet, apiPatch, apiPost } from "@/shared/api/client";
import type {
  AidStatus,
  FinancialAidRecordCreatePayload,
  FinancialAidRecordItemResponse,
  FinancialAidRecordListResponse,
  FinancialAidStatusUpdatePayload,
} from "./types";

const BASE = "/api/admin/financial-aid";
const AID_KEY = "financial-aid-records";

export function useFinancialAidRecords(status?: AidStatus, studentId?: number) {
  const params: Record<string, string | number> = {};
  if (status) params.status = status;
  if (studentId) params.student_id = studentId;

  return useQuery({
    queryKey: [AID_KEY, status ?? "all", studentId ?? "all"],
    queryFn: () =>
      apiGet<FinancialAidRecordListResponse>(
        BASE,
        Object.keys(params).length > 0 ? params : undefined,
      ),
  });
}

export function useCreateFinancialAidRecord() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: FinancialAidRecordCreatePayload) =>
      apiPost<FinancialAidRecordItemResponse>(BASE, payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: [AID_KEY] }),
  });
}

export function useUpdateFinancialAidStatus() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({
      recordId,
      payload,
    }: {
      recordId: number;
      payload: FinancialAidStatusUpdatePayload;
    }) => apiPatch<FinancialAidRecordItemResponse>(`${BASE}/${recordId}/status`, payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: [AID_KEY] }),
  });
}
