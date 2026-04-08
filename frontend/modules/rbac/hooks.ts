import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiGet, apiPost, apiDelete } from "@/shared/api/client";
import type {
  RolesResponse,
  AssignmentsResponse,
  UpsertRolePayload,
  AssignRolePayload,
} from "./types";

const BASE = "/api/admin/rbac";

export const RBAC_ROLES_KEY = "rbac-roles";
export const RBAC_ASSIGNMENTS_KEY = "rbac-assignments";

export function useRbacRoles() {
  return useQuery({
    queryKey: [RBAC_ROLES_KEY],
    queryFn: () => apiGet<RolesResponse>(`${BASE}/roles`),
  });
}

export function useRbacAssignments(params?: { user_id?: string; role?: string }) {
  return useQuery({
    queryKey: [RBAC_ASSIGNMENTS_KEY, params],
    queryFn: () => apiGet<AssignmentsResponse>(`${BASE}/assignments`, params),
  });
}

export function useUpsertRole() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: UpsertRolePayload) =>
      apiPost<{ role: Record<string, string[]> }>(`${BASE}/roles`, payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: [RBAC_ROLES_KEY] }),
  });
}

export function useAssignRole() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: AssignRolePayload) =>
      apiPost<Record<string, unknown>>(`${BASE}/assign`, payload),
    onSuccess: () =>
      qc.invalidateQueries({ queryKey: [RBAC_ASSIGNMENTS_KEY] }),
  });
}

export function useRevokeAssignment() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ userId, role }: { userId: string; role: string }) =>
      apiDelete(`${BASE}/assignments/${encodeURIComponent(userId)}/${encodeURIComponent(role)}`),
    onSuccess: () =>
      qc.invalidateQueries({ queryKey: [RBAC_ASSIGNMENTS_KEY] }),
  });
}
