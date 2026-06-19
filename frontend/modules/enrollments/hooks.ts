import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { enrollmentsApi } from "./api";
import type { CreateEnrollmentPayload, DropEnrollmentPayload } from "./types";

export const ENROLLMENTS_KEY = "enrollments";

export function useEnrollments(params?: {
  page?: number;
  page_size?: number;
  student_id?: string;
  student_profile_id?: string;
  course_id?: string;
  term_id?: string;
  section_id?: string;
  status?: string;
}, options?: { enabled?: boolean }) {
  return useQuery({
    queryKey: [ENROLLMENTS_KEY, params],
    queryFn: () => enrollmentsApi.list(params),
    enabled: options?.enabled ?? true,
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
    mutationFn: ({ id, payload }: { id: string | number; payload: DropEnrollmentPayload }) =>
      enrollmentsApi.drop(id, payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: [ENROLLMENTS_KEY] }),
  });
}
