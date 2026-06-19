import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { studentsApi } from "./api";
import type {
  BindStudentProgramPayload,
  ChangeStudentStatusPayload,
  CreateStudentPayload,
  UpdateStudentPayload,
} from "./types";

export const STUDENTS_KEY = "students";

export function useStudents(params?: {
  page?: number;
  page_size?: number;
  search?: string;
  status?: string;
  tenant_id?: string;
}) {
  return useQuery({
    queryKey: [STUDENTS_KEY, params],
    queryFn: () => studentsApi.list(params),
  });
}

export function useStudent(id: string) {
  return useQuery({
    queryKey: [STUDENTS_KEY, id],
    queryFn: () => studentsApi.get(id),
    enabled: !!id,
  });
}

export function useCreateStudent() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: CreateStudentPayload) => studentsApi.create(payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: [STUDENTS_KEY] }),
  });
}

export function useUpdateStudent() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: UpdateStudentPayload }) =>
      studentsApi.update(id, payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: [STUDENTS_KEY] }),
  });
}

export function useChangeStudentStatus() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: ChangeStudentStatusPayload }) =>
      studentsApi.changeStatus(id, payload),
    onSuccess: async (_student, variables) => {
      await qc.invalidateQueries({ queryKey: [STUDENTS_KEY, variables.id] });
      await qc.invalidateQueries({ queryKey: [STUDENTS_KEY] });
    },
  });
}

export function useDeleteStudent() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => studentsApi.delete(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: [STUDENTS_KEY] }),
  });
}

export function useActiveStudentProgram(studentId: string) {
  return useQuery({
    queryKey: [STUDENTS_KEY, studentId, "active-program"],
    queryFn: () => studentsApi.getActiveProgram(studentId),
    enabled: !!studentId,
  });
}

export function useBindStudentProgram(studentId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: BindStudentProgramPayload) => studentsApi.bindProgram(studentId, payload),
    onSuccess: async () => {
      await qc.invalidateQueries({ queryKey: [STUDENTS_KEY, studentId, "active-program"] });
      await qc.invalidateQueries({ queryKey: [STUDENTS_KEY] });
    },
  });
}
