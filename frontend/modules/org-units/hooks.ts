import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiGet, apiPost, apiPatch, apiDelete } from "@/shared/api/client";
import type {
  OrgUnit,
  OrgUnitTreeNode,
  CreateOrgUnitPayload,
  UpdateOrgUnitPayload,
} from "./types";

const BASE = "/api/admin/org-units";

type OrgUnitMutationResponse = {
  unit: OrgUnit;
  idempotent_replay: boolean;
};

export const ORG_UNITS_KEY = "org-units";
export const ORG_UNITS_TREE_KEY = "org-units-tree";

export function useOrgUnits(params?: {
  unit_type?: string;
  active_only?: boolean;
}) {
  return useQuery({
    queryKey: [ORG_UNITS_KEY, params],
    queryFn: () => apiGet<OrgUnit[]>(BASE, params),
  });
}

export function useOrgUnitsTree() {
  return useQuery({
    queryKey: [ORG_UNITS_TREE_KEY],
    queryFn: () => apiGet<OrgUnitTreeNode[]>(`${BASE}/tree`),
  });
}

export function useCreateOrgUnit() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: CreateOrgUnitPayload) =>
      apiPost<OrgUnitMutationResponse>(BASE, payload),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: [ORG_UNITS_KEY] });
      qc.invalidateQueries({ queryKey: [ORG_UNITS_TREE_KEY] });
    },
  });
}

export function useUpdateOrgUnit(unitId: number) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: UpdateOrgUnitPayload) =>
      apiPatch<OrgUnitMutationResponse>(`${BASE}/${unitId}`, payload),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: [ORG_UNITS_KEY] });
      qc.invalidateQueries({ queryKey: [ORG_UNITS_TREE_KEY] });
    },
  });
}

export function useDeactivateOrgUnit() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (unitId: number) => apiDelete<OrgUnitMutationResponse>(`${BASE}/${unitId}`),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: [ORG_UNITS_KEY] });
      qc.invalidateQueries({ queryKey: [ORG_UNITS_TREE_KEY] });
    },
  });
}
