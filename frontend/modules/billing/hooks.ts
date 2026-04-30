import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiGet, apiPatch, apiPost, apiPut } from "@/shared/api/client";
import type {
  BillingDelinquencyDashboard,
  BillingDelinquencyListResponse,
  BillingDelinquencyRecord,
  BillingDunningPolicy,
  BillingPlan,
  BillingPlanChangePayload,
  BillingPlanCreatePayload,
  BillingPlanUpdatePayload,
  BillingState,
  BillingSubscriptionAssignPayload,
  BillingTransitionPayload,
  BillingUsage,
} from "./types";

const BASE = "/api/admin/billing";
const PLANS_KEY = "billing-plans";
const STATE_KEY = "billing-state";
const USAGE_KEY = "billing-usage";
const DELINQUENCY_KEY = "billing-delinquency";

// ─── Plans ───────────────────────────────────────────────────────────────────

export function useBillingPlans() {
  return useQuery({
    queryKey: [PLANS_KEY],
    queryFn: () => apiGet<BillingPlan[]>(`${BASE}/plans`),
  });
}

export function useCreateBillingPlan() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: BillingPlanCreatePayload) =>
      apiPost<BillingPlan>(`${BASE}/plans`, payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: [PLANS_KEY] }),
  });
}

export function useUpdateBillingPlan() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ planId, payload }: { planId: number; payload: BillingPlanUpdatePayload }) =>
      apiPatch<BillingPlan>(`${BASE}/plans/${planId}`, payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: [PLANS_KEY] }),
  });
}

// ─── Tenant Billing State & Subscription ────────────────────────────────────

export function useTenantBillingState(tenantId: number) {
  return useQuery({
    queryKey: [STATE_KEY, tenantId],
    queryFn: () => apiGet<BillingState>(`${BASE}/tenants/${tenantId}/state`),
    enabled: tenantId > 0,
  });
}

export function useAssignBillingSubscription(tenantId: number) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: BillingSubscriptionAssignPayload) =>
      apiPut<BillingState>(`${BASE}/tenants/${tenantId}/subscription`, payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: [STATE_KEY, tenantId] }),
  });
}

export function useTransitionBillingSubscription(tenantId: number) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: BillingTransitionPayload) =>
      apiPost<BillingState>(
        `${BASE}/tenants/${tenantId}/subscription/transition`,
        payload,
      ),
    onSuccess: () => qc.invalidateQueries({ queryKey: [STATE_KEY, tenantId] }),
  });
}

export function useChangeBillingPlan(tenantId: number) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: BillingPlanChangePayload) =>
      apiPost(`${BASE}/tenants/${tenantId}/subscription/plan-change`, payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: [STATE_KEY, tenantId] }),
  });
}

// ─── Usage ───────────────────────────────────────────────────────────────────

export function useTenantBillingUsage(tenantId: number) {
  return useQuery({
    queryKey: [USAGE_KEY, tenantId],
    queryFn: () => apiGet<BillingUsage>(`${BASE}/tenants/${tenantId}/usage`),
    enabled: tenantId > 0,
  });
}

// ─── Delinquency ─────────────────────────────────────────────────────────────

export function useTenantDelinquencyRecords(
  tenantId: number,
  status?: string,
) {
  const params: Record<string, string> = {};
  if (status) params.status = status;
  return useQuery({
    queryKey: [DELINQUENCY_KEY, tenantId, status ?? "all"],
    queryFn: () =>
      apiGet<BillingDelinquencyListResponse>(
        `${BASE}/tenants/${tenantId}/delinquency`,
        Object.keys(params).length > 0 ? params : undefined,
      ),
    enabled: tenantId > 0,
  });
}

export function useTenantDelinquencyDashboard(tenantId: number) {
  return useQuery({
    queryKey: [DELINQUENCY_KEY, tenantId, "dashboard"],
    queryFn: () =>
      apiGet<BillingDelinquencyDashboard>(
        `${BASE}/tenants/${tenantId}/delinquency/dashboard`,
      ),
    enabled: tenantId > 0,
  });
}

export function useTenantDunningPolicy(tenantId: number) {
  return useQuery({
    queryKey: [DELINQUENCY_KEY, tenantId, "policy"],
    queryFn: () =>
      apiGet<BillingDunningPolicy>(`${BASE}/tenants/${tenantId}/delinquency/policy`),
    enabled: tenantId > 0,
  });
}

export function useEscalateDelinquency(tenantId: number) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ recordId, notes }: { recordId: number; notes?: string }) =>
      apiPost<BillingDelinquencyRecord>(
        `${BASE}/tenants/${tenantId}/delinquency/${recordId}/escalate`,
        { notes },
      ),
    onSuccess: () => qc.invalidateQueries({ queryKey: [DELINQUENCY_KEY, tenantId] }),
  });
}

export function useResolveDelinquency(tenantId: number) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({
      recordId,
      resolution,
      notes,
    }: {
      recordId: number;
      resolution: string;
      notes?: string;
    }) =>
      apiPost<BillingDelinquencyRecord>(
        `${BASE}/tenants/${tenantId}/delinquency/${recordId}/resolve`,
        { resolution, notes },
      ),
    onSuccess: () => qc.invalidateQueries({ queryKey: [DELINQUENCY_KEY, tenantId] }),
  });
}

export function useSendDelinquencyReminder(tenantId: number) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ recordId, notes }: { recordId: number; notes?: string }) =>
      apiPost<BillingDelinquencyRecord>(
        `${BASE}/tenants/${tenantId}/delinquency/${recordId}/reminder`,
        { notes },
      ),
    onSuccess: () => qc.invalidateQueries({ queryKey: [DELINQUENCY_KEY, tenantId] }),
  });
}
