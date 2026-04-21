import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiGet, apiPatch, apiPost } from "@/shared/api/client";
import type {
  ThesisCreatePayload,
  ThesisItemResponse,
  ThesisListResponse,
  ThesisStatus,
  ThesisStatusUpdatePayload,
} from "./types";

const BASE = "/api/admin/thesis";
const THESIS_KEY = "thesis-records";

export function useThesis(status?: ThesisStatus) {
  return useQuery({
    queryKey: [THESIS_KEY, status ?? "all"],
    queryFn: () => apiGet<ThesisListResponse>(BASE, status ? { status } : undefined),
  });
}

export function useCreateThesis() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: ThesisCreatePayload) => apiPost<ThesisItemResponse>(BASE, payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: [THESIS_KEY] }),
  });
}

export function useUpdateThesisStatus() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ thesisId, payload }: { thesisId: number; payload: ThesisStatusUpdatePayload }) =>
      apiPatch<ThesisItemResponse>(`${BASE}/${thesisId}/status`, payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: [THESIS_KEY] }),
  });
}
