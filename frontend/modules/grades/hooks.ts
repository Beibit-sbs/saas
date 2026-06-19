import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { gradesApi } from "./api";
import type { CreateGradingScalePayload, UpsertGradePayload } from "./types";

export const GRADES_KEY = "grades";
export const GRADING_SCALES_KEY = "grading-scales";

export function useGrades(params?: {
  page?: number;
  page_size?: number;
  student_id?: string;
  student_profile_id?: string;
  course_id?: string;
  term_id?: string;
  section_id?: string;
}) {
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

export function useGradingScales(params?: { page?: number; page_size?: number; active_only?: boolean }) {
  return useQuery({
    queryKey: [GRADING_SCALES_KEY, params],
    queryFn: () => gradesApi.listScales(params),
  });
}

export function useCreateGradingScale() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: CreateGradingScalePayload) => gradesApi.createScale(payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: [GRADING_SCALES_KEY] }),
  });
}
