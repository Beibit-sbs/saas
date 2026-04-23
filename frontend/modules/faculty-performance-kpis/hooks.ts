import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiGet, apiPatch, apiPost } from "@/shared/api/client";
import type {
  FacultyKpiCreatePayload,
  FacultyKpiItemResponse,
  FacultyKpiListResponse,
  FacultyKpiStatus,
  FacultyKpiStatusUpdatePayload,
} from "./types";

const BASE = "/api/admin/faculty-performance-kpis";
const KPI_KEY = "faculty-performance-kpis";

export function useFacultyKpis(filters?: {
  status?: FacultyKpiStatus;
  department_id?: string;
}) {
  const params: Record<string, string> = {};
  if (filters?.status) params.status = filters.status;
  if (filters?.department_id) params.department_id = filters.department_id;

  return useQuery({
    queryKey: [KPI_KEY, filters?.status ?? "all", filters?.department_id ?? "all"],
    queryFn: () =>
      apiGet<FacultyKpiListResponse>(
        BASE,
        Object.keys(params).length > 0 ? params : undefined,
      ),
  });
}

export function useCreateFacultyKpi() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: FacultyKpiCreatePayload) =>
      apiPost<FacultyKpiItemResponse>(BASE, payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: [KPI_KEY] }),
  });
}

export function useUpdateFacultyKpiStatus() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({
      kpiId,
      payload,
    }: {
      kpiId: number;
      payload: FacultyKpiStatusUpdatePayload;
    }) => apiPatch<FacultyKpiItemResponse>(`${BASE}/${kpiId}/status`, payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: [KPI_KEY] }),
  });
}
