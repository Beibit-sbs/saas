import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { featureFlagsApi } from "./api";
import type { TenantFlagOverridePayload, UpdateFlagPayload } from "./types";

export const FLAGS_KEY = "feature-flags";

export function useFeatureFlags() {
  return useQuery({
    queryKey: [FLAGS_KEY],
    queryFn: () => featureFlagsApi.list(),
  });
}

export function useUpdateFeatureFlag() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ key, payload }: { key: string; payload: UpdateFlagPayload }) =>
      featureFlagsApi.update(key, payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: [FLAGS_KEY] }),
  });
}

export function useSetTenantFlagOverride() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ key, payload }: { key: string; payload: TenantFlagOverridePayload }) =>
      featureFlagsApi.setTenantOverride(key, payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: [FLAGS_KEY] }),
  });
}
