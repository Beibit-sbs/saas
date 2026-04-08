import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiDelete, apiGet, apiPost, apiPut } from "@/shared/api/client";
import type {
  CoursesResponse,
  CourseItemResponse,
  CreateCoursePayload,
  UpdateCoursePayload,
  DeleteCourseResponse,
} from "./types";

const BASE = "/api/admin/org/courses";
export const COURSES_KEY = "courses";

export function useCourses() {
  return useQuery({
    queryKey: [COURSES_KEY],
    queryFn: () => apiGet<CoursesResponse>(BASE),
  });
}

export function useCreateCourse() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: CreateCoursePayload) =>
      apiPost<CourseItemResponse>(BASE, payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: [COURSES_KEY] }),
  });
}

export function useUpdateCourse(courseId: number | null) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: UpdateCoursePayload) => {
      if (courseId == null) {
        throw new Error("Course ID is required");
      }
      return apiPut<CourseItemResponse>(`${BASE}/${courseId}`, payload);
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: [COURSES_KEY] }),
  });
}

export function useDeleteCourse() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (courseId: number) =>
      apiDelete<DeleteCourseResponse>(`${BASE}/${courseId}`),
    onSuccess: () => qc.invalidateQueries({ queryKey: [COURSES_KEY] }),
  });
}
