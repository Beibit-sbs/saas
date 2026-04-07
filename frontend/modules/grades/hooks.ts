import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { gradesApi } from "./api";
import type { UpsertGradePayload } from "./types";

export const GRADES_KEY = "grades";

export function useGrades(params?: { page?: number; page_size?: number; student_id?: string; section_id?: string }) {
  return useQuery({
    queryKey: [GRADES_KEY, params],
    queryFn: () => gradesApi.list(params),
  });
}

export function useUpsertGrade() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: UpsertGradePayload) => gradesApi.upsert(payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: [GRADES_KEY] }),
  });
}
