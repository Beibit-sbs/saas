import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiDelete, apiGet, apiPost, apiPut } from "@/shared/api/client";
import type {
  ProgramsResponse,
  ProgramItemResponse,
  CreateProgramPayload,
  UpdateProgramPayload,
  DeleteProgramResponse,
} from "./types";

const BASE = "/api/admin/org/programs";
export const PROGRAMS_KEY = "programs";

export function usePrograms() {
  return useQuery({
    queryKey: [PROGRAMS_KEY],
    queryFn: () => apiGet<ProgramsResponse>(BASE),
  });
}

export function useCreateProgram() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: CreateProgramPayload) =>
      apiPost<ProgramItemResponse>(BASE, payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: [PROGRAMS_KEY] }),
  });
}

export function useUpdateProgram(programId: number | null) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: UpdateProgramPayload) => {
      if (programId == null) {
        throw new Error("Program ID is required");
      }
      return apiPut<ProgramItemResponse>(`${BASE}/${programId}`, payload);
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: [PROGRAMS_KEY] }),
  });
}

export function useDeleteProgram() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (programId: number) =>
      apiDelete<DeleteProgramResponse>(`${BASE}/${programId}`),
    onSuccess: () => qc.invalidateQueries({ queryKey: [PROGRAMS_KEY] }),
  });
}
