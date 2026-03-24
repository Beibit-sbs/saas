import { apiGet, apiPatch, apiPost } from "@/shared/api/client";
import type { FeatureFlag, TenantFlagOverridePayload, UpdateFlagPayload } from "./types";

const BASE = "/api/v1/admin/features";

export const featureFlagsApi = {
  list: () => apiGet<FeatureFlag[]>(BASE),

  update: (key: string, payload: UpdateFlagPayload) =>
    apiPatch<FeatureFlag>(`${BASE}/${key}`, payload),

  setTenantOverride: (key: string, payload: TenantFlagOverridePayload) =>
    apiPost<FeatureFlag>(`${BASE}/${key}/overrides`, payload),
};
