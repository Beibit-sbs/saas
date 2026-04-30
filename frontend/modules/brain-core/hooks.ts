import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiGet, apiPost, apiPut } from "@/shared/api/client";
import type {
  BrainAnomalyRequest,
  BrainAnomalyResult,
  BrainCollectionResponse,
  BrainDecision,
  BrainExplanation,
  BrainKPIDashboard,
  BrainLearningEvaluationResult,
  BrainOptimizationResult,
  BrainOptimizeRequest,
  BrainOutcome,
  BrainPolicyProfile,
  BrainPolicyTuningApplyResult,
  BrainPolicyTuningSuggestion,
  BrainPolicyUpdatePayload,
  BrainPolicyUpdateResult,
  BrainPredictionRequest,
  BrainPredictionResult,
  BrainRecommendationsResponse,
} from "./types";

const BASE = "/api/admin/brain";

const DECISIONS_KEY = "brain-core-decisions";
const OUTCOMES_KEY = "brain-core-outcomes";
const POLICY_PROFILE_KEY = "brain-core-policy-profile";
const POLICY_TUNING_KEY = "brain-core-policy-tuning";
const EXPLANATION_KEY = "brain-core-explanation";

export function useBrainDecisions() {
  return useQuery({
    queryKey: [DECISIONS_KEY],
    queryFn: () => apiGet<BrainCollectionResponse<BrainDecision>>(`${BASE}/decisions`),
    staleTime: 15_000,
  });
}

export function useBrainOutcomes() {
  return useQuery({
    queryKey: [OUTCOMES_KEY],
    queryFn: () => apiGet<BrainCollectionResponse<BrainOutcome>>(`${BASE}/outcomes`),
    staleTime: 15_000,
  });
}

export function useBrainExplanation(decisionId: string | null) {
  return useQuery({
    queryKey: [EXPLANATION_KEY, decisionId],
    queryFn: () => apiGet<BrainExplanation>(`${BASE}/explanations/${decisionId}`),
    enabled: Boolean(decisionId),
    staleTime: 15_000,
  });
}

export function useBrainPolicyProfile(tenantId: number) {
  return useQuery({
    queryKey: [POLICY_PROFILE_KEY, tenantId],
    queryFn: () => apiGet<BrainPolicyProfile>(`${BASE}/policy/${tenantId}`),
    enabled: tenantId > 0,
    staleTime: 15_000,
  });
}

export function useBrainPolicyTuning(tenantId: number) {
  return useQuery({
    queryKey: [POLICY_TUNING_KEY, tenantId],
    queryFn: () => apiGet<BrainPolicyTuningSuggestion>(`${BASE}/learning/policy-tuning/${tenantId}`),
    enabled: tenantId > 0,
    staleTime: 15_000,
  });
}

export function useApplyBrainPolicyTuning(tenantId: number) {
  const qc = useQueryClient();

  return useMutation({
    mutationFn: (payload: { actor: string }) =>
      apiPost<BrainPolicyTuningApplyResult>(`${BASE}/learning/policy-tuning/${tenantId}/apply`, payload),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: [POLICY_PROFILE_KEY, tenantId] });
      qc.invalidateQueries({ queryKey: [POLICY_TUNING_KEY, tenantId] });
      qc.invalidateQueries({ queryKey: [DECISIONS_KEY] });
      qc.invalidateQueries({ queryKey: [OUTCOMES_KEY] });
    },
  });
}

export function useUpdateBrainPolicyProfile(tenantId: number) {
  const qc = useQueryClient();

  return useMutation({
    mutationFn: (payload: BrainPolicyUpdatePayload) =>
      apiPut<BrainPolicyUpdateResult>(`${BASE}/policy/${tenantId}`, payload),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: [POLICY_PROFILE_KEY, tenantId] });
    },
  });
}

// XVII1 — Executive KPI Dashboard
export function useBrainExecutiveKPI(tenantId: number) {
  return useQuery({
    queryKey: ["brain-executive-kpi", tenantId],
    queryFn: () => apiGet<BrainKPIDashboard>(`${BASE}/executive-kpi/${tenantId}`),
    enabled: tenantId > 0,
    staleTime: 30_000,
  });
}

// XVII1 — Proactive Recommendations
export function useBrainRecommendations(tenantId: number) {
  return useQuery({
    queryKey: ["brain-recommendations", tenantId],
    queryFn: () => apiGet<BrainRecommendationsResponse>(`${BASE}/recommendations/${tenantId}`),
    enabled: tenantId > 0,
    staleTime: 30_000,
  });
}

// XVII2 — Predictive Risk
export function useBrainPredictRisk() {
  return useMutation({
    mutationFn: (payload: BrainPredictionRequest) =>
      apiPost<BrainPredictionResult>(`${BASE}/predict`, payload),
  });
}

// XVII2 — Anomaly Detection
export function useBrainDetectAnomalies() {
  return useMutation({
    mutationFn: (payload: BrainAnomalyRequest) =>
      apiPost<BrainAnomalyResult>(`${BASE}/anomalies`, payload),
  });
}

// XVII3 — Learning Evaluation
export function useBrainLearningEvaluation(tenantId: number) {
  return useQuery({
    queryKey: ["brain-learning-eval", tenantId],
    queryFn: () => apiGet<BrainLearningEvaluationResult>(`${BASE}/learning/evaluate/${tenantId}`),
    enabled: tenantId > 0,
    staleTime: 60_000,
  });
}

// XVII4 — Brain Optimization
export function useBrainOptimize() {
  return useMutation({
    mutationFn: (payload: BrainOptimizeRequest) =>
      apiPost<BrainOptimizationResult>(`${BASE}/optimize`, payload),
  });
}
