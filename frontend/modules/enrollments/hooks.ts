import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { enrollmentsApi } from "./api";
import type { CreateEnrollmentPayload } from "./types";

export const ENROLLMENTS_KEY = "enrollments";

export function useEnrollments(params?: {
  page?: number;
  page_size?: number;
  student_id?: string;
  section_id?: string;
  status?: string;
}) {
  return useQuery({
    queryKey: [ENROLLMENTS_KEY, params],
    queryFn: () => enrollmentsApi.list(params),
  });
}

export function useCreateEnrollment() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: CreateEnrollmentPayload) => enrollmentsApi.create(payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: [ENROLLMENTS_KEY] }),
  });
}

export function useDropEnrollment() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => enrollmentsApi.drop(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: [ENROLLMENTS_KEY] }),
  });
}
