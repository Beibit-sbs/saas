import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiDelete, apiGet, apiPatch, apiPost, apiPut } from "@/shared/api/client";
import type {
  FacultyListResponse,
  FacultyItemResponse,
  CreateFacultyPayload,
  UpdateFacultyPayload,
  DeleteFacultyResponse,
  FacultyContractListResponse,
  FacultyContractItemResponse,
  CreateFacultyContractPayload,
  UpdateFacultyContractStatusPayload,
} from "./types";

const BASE = "/api/admin/org/faculty";
export const FACULTY_KEY = "faculty";
export const FACULTY_CONTRACTS_KEY = "faculty-contracts";

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

export function useFacultyContracts() {
  return useQuery({
    queryKey: [FACULTY_CONTRACTS_KEY],
    queryFn: () => apiGet<FacultyContractListResponse>(`${BASE}/contracts`),
  });
}

export function useCreateFacultyContract() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: CreateFacultyContractPayload) =>
      apiPost<FacultyContractItemResponse>(`${BASE}/contracts`, payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: [FACULTY_CONTRACTS_KEY] }),
  });
}

export function useUpdateFacultyContractStatus(contractId: number | null) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: UpdateFacultyContractStatusPayload) => {
      if (contractId == null) {
        throw new Error("Contract ID is required");
      }
      return apiPatch<FacultyContractItemResponse>(
        `${BASE}/contracts/${contractId}/status`,
        payload,
      );
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: [FACULTY_CONTRACTS_KEY] }),
  });
}
