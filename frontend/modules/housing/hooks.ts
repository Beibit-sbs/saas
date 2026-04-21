import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiGet, apiPatch, apiPost } from "@/shared/api/client";
import type {
  HousingRequestCreatePayload,
  HousingRequestItemResponse,
  HousingRequestListResponse,
  HousingRequestStatus,
  HousingRequestStatusUpdatePayload,
} from "./types";

const BASE = "/api/admin/housing";
const HOUSING_KEY = "housing-requests";

export function useHousingRequests(status?: HousingRequestStatus, studentId?: number) {
  const params: Record<string, string | number> = {};
  if (status) params.status = status;
  if (studentId) params.student_id = studentId;

  return useQuery({
    queryKey: [HOUSING_KEY, status ?? "all", studentId ?? "all"],
    queryFn: () =>
      apiGet<HousingRequestListResponse>(
        BASE,
        Object.keys(params).length > 0 ? params : undefined,
      ),
  });
}

export function useCreateHousingRequest() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: HousingRequestCreatePayload) =>
      apiPost<HousingRequestItemResponse>(BASE, payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: [HOUSING_KEY] }),
  });
}

export function useUpdateHousingRequestStatus() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({
      requestId,
      payload,
    }: {
      requestId: number;
      payload: HousingRequestStatusUpdatePayload;
    }) => apiPatch<HousingRequestItemResponse>(`${BASE}/${requestId}/status`, payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: [HOUSING_KEY] }),
  });
}
