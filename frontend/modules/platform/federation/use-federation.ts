import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiGet, apiPost } from "@/shared/api/client";
import type {
  Institution,
  InstitutionCreateRequest,
  InstitutionOverview,
  FederationMember,
  LinkTenantRequest,
} from "./types";

export const INSTITUTIONS_KEY = "platform-federation-institutions";
export const INSTITUTION_OVERVIEW_KEY = "platform-federation-institution-overview";

export function useInstitutions() {
  return useQuery({
    queryKey: [INSTITUTIONS_KEY],
    queryFn: () => apiGet<Institution[]>("/api/bff/admin/platform/federation/institutions"),
    staleTime: 30_000,
  });
}

export function useInstitution(id: number) {
  return useQuery({
    queryKey: [INSTITUTIONS_KEY, id],
    queryFn: () => apiGet<Institution>(`/api/bff/admin/platform/federation/institutions/${id}`),
    enabled: id > 0,
    staleTime: 30_000,
  });
}

export function useInstitutionOverview(id: number) {
  return useQuery({
    queryKey: [INSTITUTION_OVERVIEW_KEY, id],
    queryFn: () =>
      apiGet<InstitutionOverview>(
        `/api/bff/admin/platform/federation/institutions/${id}/overview`,
      ),
    enabled: id > 0,
    staleTime: 15_000,
  });
}

export function useCreateInstitution() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: InstitutionCreateRequest) =>
      apiPost<Institution>("/api/bff/admin/platform/federation/institutions", payload),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: [INSTITUTIONS_KEY] });
    },
  });
}

export function useLinkTenant(institutionId: number) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: LinkTenantRequest) =>
      apiPost<FederationMember>(
        `/api/bff/admin/platform/federation/institutions/${institutionId}/tenants`,
        payload,
      ),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: [INSTITUTION_OVERVIEW_KEY, institutionId] });
    },
  });
}
