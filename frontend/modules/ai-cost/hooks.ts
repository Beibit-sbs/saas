import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiGet, apiPut } from "@/shared/api/client";
import type {
  AIUsageCostSummary,
  AIUsageCostProjection,
  AIUsageCostAnomaly,
  AIUsageCostTrendPoint,
  AIUsageBudget,
  AIUsageBudgetPayload,
  AIUsageBudgetStatus,
  AISLOPolicy,
  AISLOCompliance,
  AISLOViolation,
} from "./types";

const BASE = "/api/admin/ai";
const SUMMARY_KEY = "ai-cost-summary";
const BUDGET_KEY = "ai-cost-budget";
const BUDGET_STATUS_KEY = "ai-cost-budget-status";
const PROJECTION_KEY = "ai-cost-projection";
const ANOMALIES_KEY = "ai-cost-anomalies";
const TREND_KEY = "ai-cost-trend";
const SLO_POLICIES_KEY = "ai-slo-policies";
const SLO_COMPLIANCE_KEY = "ai-slo-compliance";
const SLO_VIOLATIONS_KEY = "ai-slo-violations";

export function useAICostSummary() {
  return useQuery({
    queryKey: [SUMMARY_KEY],
    queryFn: () => apiGet<AIUsageCostSummary>(`${BASE}/usage/summary`),
  });
}

export function useAICostProjection() {
  return useQuery({
    queryKey: [PROJECTION_KEY],
    queryFn: () => apiGet<AIUsageCostProjection>(`${BASE}/usage/projection`),
  });
}

export function useAICostAnomalies() {
  return useQuery({
    queryKey: [ANOMALIES_KEY],
    queryFn: () => apiGet<AIUsageCostAnomaly[]>(`${BASE}/usage/anomalies`),
  });
}

export function useAICostTrend(days = 30) {
  return useQuery({
    queryKey: [TREND_KEY, days],
    queryFn: () => apiGet<AIUsageCostTrendPoint[]>(`${BASE}/usage/trend`, { days }),
  });
}

export function useAICostBudget() {
  return useQuery({
    queryKey: [BUDGET_KEY],
    queryFn: () => apiGet<AIUsageBudget>(`${BASE}/usage/budget`),
  });
}

export function useUpdateAICostBudget() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: AIUsageBudgetPayload) =>
      apiPut<AIUsageBudget>(`${BASE}/usage/budget`, payload),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: [BUDGET_KEY] });
      qc.invalidateQueries({ queryKey: [BUDGET_STATUS_KEY] });
      qc.invalidateQueries({ queryKey: [SUMMARY_KEY] });
    },
  });
}

export function useAICostBudgetStatus() {
  return useQuery({
    queryKey: [BUDGET_STATUS_KEY],
    queryFn: () => apiGet<AIUsageBudgetStatus[]>(`${BASE}/usage/budgets/status`),
  });
}

export function useAISLOPolicies() {
  return useQuery({
    queryKey: [SLO_POLICIES_KEY],
    queryFn: () => apiGet<AISLOPolicy[]>(`${BASE}/slo`),
  });
}

export function useAISLOCompliance() {
  return useQuery({
    queryKey: [SLO_COMPLIANCE_KEY],
    queryFn: () => apiGet<AISLOCompliance[]>(`${BASE}/slo/compliance`),
  });
}

export function useAISLOViolations() {
  return useQuery({
    queryKey: [SLO_VIOLATIONS_KEY],
    queryFn: () => apiGet<AISLOViolation[]>(`${BASE}/slo/violations`),
  });
}
