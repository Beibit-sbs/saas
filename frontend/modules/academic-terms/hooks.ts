import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiGet, apiPost } from "@/shared/api/client";
import type {
  AcademicTerm,
  AcademicTermsResponse,
  CreateAcademicTermPayload,
} from "./types";

const BASE = "/api/admin/academic-terms";
export const ACADEMIC_TERMS_KEY = "academic-terms";

export function useAcademicTerms(params?: {
  page?: number;
  page_size?: number;
  status?: AcademicTerm["status"];
}) {
  return useQuery({
    queryKey: [ACADEMIC_TERMS_KEY, params],
    queryFn: () => apiGet<AcademicTermsResponse>(BASE, params),
  });
}

export function useCreateAcademicTerm() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: CreateAcademicTermPayload) => apiPost<AcademicTerm>(BASE, payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: [ACADEMIC_TERMS_KEY] }),
  });
}
