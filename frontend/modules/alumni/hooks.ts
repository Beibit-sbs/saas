import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiGet, apiPatch, apiPost } from "@/shared/api/client";
import type {
  AlumniBrainContext,
  AlumniRecordCreatePayload,
  AlumniRecordItemResponse,
  AlumniRecordListResponse,
  AlumniStatus,
  AlumniStatusUpdatePayload,
} from "./types";

const BASE = "/api/admin/alumni";
const ALUMNI_KEY = "alumni-records";

export function useAlumniRecords(status?: AlumniStatus, studentId?: number) {
  const params: Record<string, string | number> = {};
  if (status) params.status = status;
  if (studentId) params.student_id = studentId;

  return useQuery({
    queryKey: [ALUMNI_KEY, status ?? "all", studentId ?? "all"],
    queryFn: () =>
      apiGet<AlumniRecordListResponse>(
        BASE,
        Object.keys(params).length > 0 ? params : undefined,
      ),
  });
}

export function useAlumniBrainContext() {
  return useQuery({
    queryKey: [ALUMNI_KEY, "brain-context"],
    queryFn: () => apiGet<AlumniBrainContext>(`${BASE}/brain-context`),
  });
}

export function useCreateAlumniRecord() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: AlumniRecordCreatePayload) =>
      apiPost<AlumniRecordItemResponse>(BASE, payload),
    onSuccess: async () => {
      await qc.invalidateQueries({ queryKey: [ALUMNI_KEY] });
    },
  });
}

export function useUpdateAlumniStatus() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({
      recordId,
      payload,
    }: {
      recordId: number;
      payload: AlumniStatusUpdatePayload;
    }) => apiPatch<AlumniRecordItemResponse>(`${BASE}/${recordId}/status`, payload),
    onSuccess: async () => {
      await qc.invalidateQueries({ queryKey: [ALUMNI_KEY] });
    },
  });
}
