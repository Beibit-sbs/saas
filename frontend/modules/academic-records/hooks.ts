import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiDelete, apiGet, apiPost, apiPut } from "@/shared/api/client";
import type {
  AcademicRecordsResponse,
  AcademicRecordItemResponse,
  CreateAcademicRecordPayload,
  UpdateAcademicRecordPayload,
  DeleteAcademicRecordResponse,
} from "./types";

const BASE = "/api/admin/university/records";
export const ACADEMIC_RECORDS_KEY = "academic-records";

export function useAcademicRecords() {
  return useQuery({
    queryKey: [ACADEMIC_RECORDS_KEY],
    queryFn: () => apiGet<AcademicRecordsResponse>(BASE),
  });
}

export function useCreateAcademicRecord() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: CreateAcademicRecordPayload) =>
      apiPost<AcademicRecordItemResponse>(BASE, payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: [ACADEMIC_RECORDS_KEY] }),
  });
}

export function useUpdateAcademicRecord(recordId: number | null) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: UpdateAcademicRecordPayload) => {
      if (recordId == null) {
        throw new Error("Record ID is required");
      }
      return apiPut<AcademicRecordItemResponse>(`${BASE}/${recordId}`, payload);
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: [ACADEMIC_RECORDS_KEY] }),
  });
}

export function useDeleteAcademicRecord() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (recordId: number) =>
      apiDelete<DeleteAcademicRecordResponse>(`${BASE}/${recordId}`),
    onSuccess: () => qc.invalidateQueries({ queryKey: [ACADEMIC_RECORDS_KEY] }),
  });
}
