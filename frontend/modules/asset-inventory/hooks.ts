import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiGet, apiPatch, apiPost } from "@/shared/api/client";
import type {
  AssetCategory,
  AssetCondition,
  AssetItemCreatePayload,
  AssetItemResponse,
  AssetItemStatusUpdatePayload,
  AssetListResponse,
  AssetStatus,
  DepreciationItemResponse,
  DepreciationListResponse,
  DepreciationRecordCreatePayload,
  DepreciationStatus,
} from "./types";

const BASE = "/api/admin/asset-inventory";
const ASSETS_KEY = "asset-inventory-items";
const DEPR_KEY = "asset-depreciation-records";

export function useAssetItems(filters?: {
  status?: AssetStatus;
  category?: AssetCategory;
  condition?: AssetCondition;
}) {
  const params: Record<string, string> = {};
  if (filters?.status) params.status = filters.status;
  if (filters?.category) params.category = filters.category;
  if (filters?.condition) params.condition = filters.condition;

  return useQuery({
    queryKey: [ASSETS_KEY, filters?.status ?? "all", filters?.category ?? "all"],
    queryFn: () =>
      apiGet<AssetListResponse>(
        `${BASE}/items`,
        Object.keys(params).length > 0 ? params : undefined,
      ),
  });
}

export function useCreateAssetItem() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: AssetItemCreatePayload) =>
      apiPost<AssetItemResponse>(`${BASE}/items`, payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: [ASSETS_KEY] }),
  });
}

export function useUpdateAssetItemStatus() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({
      assetId,
      payload,
    }: {
      assetId: number;
      payload: AssetItemStatusUpdatePayload;
    }) => apiPatch<AssetItemResponse>(`${BASE}/items/${assetId}/status`, payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: [ASSETS_KEY] }),
  });
}

export function useDepreciationRecords(filters?: { status?: DepreciationStatus }) {
  return useQuery({
    queryKey: [DEPR_KEY, filters?.status ?? "all"],
    queryFn: () =>
      apiGet<DepreciationListResponse>(
        `${BASE}/depreciation`,
        filters?.status ? { status: filters.status } : undefined,
      ),
  });
}

export function useCreateDepreciationRecord() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: DepreciationRecordCreatePayload) =>
      apiPost<DepreciationItemResponse>(`${BASE}/depreciation`, payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: [DEPR_KEY] }),
  });
}
