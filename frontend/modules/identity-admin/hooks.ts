import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiGet, apiPost } from "@/shared/api/client";
import type {
  IdentityProvidersResponse,
  DirectoryProvidersResponse,
  IdentityMappingsResponse,
  CreateIdentityMappingPayload,
} from "./types";

const BASE = "/api/admin/identity";
export const IDENTITY_PROVIDERS_KEY = "identity-providers";
export const DIRECTORY_PROVIDERS_KEY = "directory-providers";
export const IDENTITY_MAPPINGS_KEY = "identity-mappings";

export function useIdentityProviders() {
  return useQuery({
    queryKey: [IDENTITY_PROVIDERS_KEY],
    queryFn: () => apiGet<IdentityProvidersResponse>(`${BASE}/providers`),
  });
}

export function useDirectoryProviders() {
  return useQuery({
    queryKey: [DIRECTORY_PROVIDERS_KEY],
    queryFn: () =>
      apiGet<DirectoryProvidersResponse>(`${BASE}/directory-providers`),
  });
}

export function useIdentityMappings() {
  return useQuery({
    queryKey: [IDENTITY_MAPPINGS_KEY],
    queryFn: () => apiGet<IdentityMappingsResponse>(`${BASE}/mappings`),
  });
}

export function useTestDirectoryProvider() {
  return useMutation({
    mutationFn: ({
      providerId,
      login,
    }: {
      providerId: number;
      login?: string;
    }) =>
      apiPost<{ result: Record<string, unknown> }>(
        `${BASE}/directory-providers/${providerId}/test`,
        {
          login,
        },
      ),
  });
}

export function useCreateIdentityMapping() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: CreateIdentityMappingPayload) =>
      apiPost<{ mapping: { id: number } }>(`${BASE}/mappings`, payload),
    onSuccess: () =>
      qc.invalidateQueries({ queryKey: [IDENTITY_MAPPINGS_KEY] }),
  });
}
