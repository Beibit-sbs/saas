import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { tenantsApi } from "./api";
import type { CreateTenantPayload, UpdateTenantPayload } from "./types";

export const TENANTS_KEY = "tenants";

export function useTenants(params?: { page?: number; page_size?: number; search?: string; status?: string }) {
  return useQuery({
    queryKey: [TENANTS_KEY, params],
    queryFn: () => tenantsApi.list(params),
  });
}

export function useTenant(id: string) {
  return useQuery({
    queryKey: [TENANTS_KEY, id],
    queryFn: () => tenantsApi.get(id),
    enabled: !!id,
  });
}

export function useCreateTenant() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: CreateTenantPayload) => tenantsApi.create(payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: [TENANTS_KEY] }),
  });
}

export function useUpdateTenant() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: UpdateTenantPayload }) =>
      tenantsApi.update(id, payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: [TENANTS_KEY] }),
  });
}

export function useSuspendTenant() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => tenantsApi.suspend(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: [TENANTS_KEY] }),
  });
}

export function useActivateTenant() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => tenantsApi.activate(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: [TENANTS_KEY] }),
  });
}

export function useDeleteTenant() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => tenantsApi.delete(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: [TENANTS_KEY] }),
  });
}
