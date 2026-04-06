import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { featureFlagsApi } from "./api";
import type { UpsertFlagPayload } from "./types";

export const FLAGS_KEY = "feature-flags";

export function useFeatureFlags() {
  return useQuery({
    queryKey: [FLAGS_KEY],
    queryFn: () => featureFlagsApi.list(),
  });
}

export function useUpsertFeatureFlag() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: UpsertFlagPayload) => featureFlagsApi.upsert(payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: [FLAGS_KEY] }),
  });
}
