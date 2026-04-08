import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiDelete, apiGet, apiPost, apiPut } from "@/shared/api/client";
import type {
  FacultyListResponse,
  FacultyItemResponse,
  CreateFacultyPayload,
  UpdateFacultyPayload,
  DeleteFacultyResponse,
} from "./types";

const BASE = "/api/admin/org/faculty";
export const FACULTY_KEY = "faculty";

export function useFaculty() {
  return useQuery({
    queryKey: [FACULTY_KEY],
    queryFn: () => apiGet<FacultyListResponse>(BASE),
  });
}

export function useCreateFaculty() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: CreateFacultyPayload) =>
      apiPost<FacultyItemResponse>(BASE, payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: [FACULTY_KEY] }),
  });
}

export function useUpdateFaculty(facultyRowId: number | null) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: UpdateFacultyPayload) => {
      if (facultyRowId == null) {
        throw new Error("Faculty row ID is required");
      }
      return apiPut<FacultyItemResponse>(`${BASE}/${facultyRowId}`, payload);
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: [FACULTY_KEY] }),
  });
}

export function useDeleteFaculty() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (facultyRowId: number) =>
      apiDelete<DeleteFacultyResponse>(`${BASE}/${facultyRowId}`),
    onSuccess: () => qc.invalidateQueries({ queryKey: [FACULTY_KEY] }),
  });
}
