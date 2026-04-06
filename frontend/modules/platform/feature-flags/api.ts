import { apiGet, apiPost } from "@/shared/api/client";
import type { FeatureFlag, UpsertFlagPayload } from "./types";

const BASE = "/api/admin/feature-flags";

export const featureFlagsApi = {
  list: () => apiGet<{ flags: FeatureFlag[] }>(BASE).then((r) => r.flags),

  upsert: (payload: UpsertFlagPayload) =>
    apiPost<{ flag: FeatureFlag }>(BASE, payload).then((r) => r.flag),
};
