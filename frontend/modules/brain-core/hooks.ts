import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiGet, apiPost, apiPut } from "@/shared/api/client";
import type {
  BrainAnomalyRequest,
  BrainAnomalyResult,
  BrainAgentHandoffResult,
  BrainAgentHandoffStatus,
  BrainAgentMergeResult,
  BrainCollectionResponse,
  BrainCrossTenantRecommendationsResult,
  BrainDecision,
  BrainExplanation,
  BrainKPIDashboard,
  BrainLearningApplyRequest,
  BrainLearningApplyResult,
  BrainLearningEvaluationResult,
  BrainOptimizationResult,
  BrainOptimizeRequest,
  BrainOutcome,
  BrainPolicyReasoningResult,
  BrainPolicyRolloutPlanResult,
  BrainPolicyProfile,
  BrainPolicyTuningApplyResult,
  BrainPolicyTuningSuggestion,
  BrainPredictivePolicyOptimizationResult,
  BrainPolicyUpdatePayload,
  BrainPolicyUpdateResult,
  BrainPredictionRequest,
  BrainPredictionResult,
  BrainRecommendationsResponse,
  BrainPolicyRolloutPhaseExecutionResult,
  BrainPolicyRollbackResult,
  BrainCrossTenantRolloutResult,
  BrainAgentTask,
  BrainAgentStepResult,
  BrainAgentTaskStatus,
  BrainAgentPolicy,
  BrainAgentClaimResult,
  BrainAgentCompleteResult,
  BrainAgentSlaReport,
  BrainAgentQueueMetrics,
  BrainAgentStepEventLogResult,
  BrainAgentStepLog,
  BrainAgentTaskAudit,
  BrainAgentPerformanceReport,
  BrainAgentStepDependencies,
  BrainAgentReadyQueue,
  BrainAgentResourceBudget,
  BrainAgentResourceUsage,
  BrainAgentSplitResult,
  BrainAgentOutcomeFeedbackResult,
  BrainAgentOutcomeSummary,
  BrainAgentLearningSignalResult,
  BrainAgentLearningSummary,
  BrainAgentOptimizationResult,
  BrainAgentOptimizationHistory,
  BrainAgentBenchmarkRecord,
  BrainAgentBenchmarkSummary,
  BrainAgentKnowledgeRecord,
  BrainAgentKnowledgeShareResult,
  BrainAgentSharedKnowledgeSummary,
  BrainAgentKnowledgeExpireResult,
  BrainAgentKnowledgeHealth,
  BrainReplayRequest,
  BrainReplayResult,
  BrainReplayAuditResponse,
  BrainReplayApproveRequest,
  BrainReplayApproveResult,
  BrainReplayRejectRequest,
  BrainReplayRejectResult,
  BrainReplayCancelRequest,
  BrainReplayCancelResult,
  BrainReplayAnalytics,
  BrainReplayTrendAlert,
  BrainReplayOperatorSummary,
  BrainReplayPolicy,
  BrainReplayPolicyHistoryEntry,
  BrainReplayPolicyCheckResult,
  BrainPolicyReasoningResult_XIX,
  BrainCrossTenantRecommendationsResult_XIX,
  BrainPredictivePolicyOptimizationResult_XIX,
  BrainPolicyRolloutPlanResult_XX,
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

// XVIII1 — Learning Apply (Governance)
export function useBrainLearningApply(tenantId: number) {
  const qc = useQueryClient();

  return useMutation({
    mutationFn: (payload: Omit<BrainLearningApplyRequest, "tenant_id">) =>
      apiPost<BrainLearningApplyResult>(`${BASE}/learning/apply`, {
        ...payload,
        tenant_id: tenantId,
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: [POLICY_PROFILE_KEY, tenantId] });
      qc.invalidateQueries({ queryKey: [POLICY_TUNING_KEY, tenantId] });
      qc.invalidateQueries({ queryKey: ["brain-learning-eval", tenantId] });
    },
  });
}

export function useBrainExecutePolicyRolloutPhase() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({
      tenantId,
      planId,
      phase,
    }: {
      tenantId: number;
      planId: string;
      phase: string;
    }) =>
      apiPost<BrainPolicyRolloutPhaseExecutionResult>(
        `${BASE}/policy-rollout-phase/${tenantId}/execute?plan_id=${planId}&phase=${phase}`,
        {},
      ),
    onSuccess: (data, variables) => {
      // Invalidate related queries after phase execution
      queryClient.invalidateQueries({
        queryKey: ["brain-policy-rollout-plan", variables.tenantId],
      });
    },
  });
}

export function useBrainRollbackPolicyRollout() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({
      tenantId,
      planId,
      trigger,
    }: {
      tenantId: number;
      planId: string;
      trigger: string;
    }) =>
      apiPost<BrainPolicyRollbackResult>(
        `${BASE}/policy-rollout-phase/${tenantId}/rollback?plan_id=${planId}&trigger=${trigger}`,
        {},
      ),
    onSuccess: (data, variables) => {
      queryClient.invalidateQueries({
        queryKey: ["brain-policy-rollout-plan", variables.tenantId],
      });
    },
  });
}

export function useBrainCoordinateCrossTenantRollout() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({
      planId,
      phase,
      tenantIds,
    }: {
      planId: string;
      phase: string;
      tenantIds: number[];
    }) =>
      apiPost<BrainCrossTenantRolloutResult>(
        `${BASE}/policy-rollout-coordination?plan_id=${planId}&phase=${phase}&${tenantIds.map((id) => `tenant_ids=${id}`).join("&")}`,
        {},
      ),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["brain-policy-rollout-plan"] });
    },
  });
}

// XXI — Autonomous Agent Workflows & Self-Governance
export function useBrainCreateAgentTask() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({
      tenantId,
      workflowType,
    }: {
      tenantId: number;
      workflowType: string;
    }) =>
      apiPost<BrainAgentTask>(
        `${BASE}/agent/tasks?tenant_id=${tenantId}&workflow_type=${workflowType}`,
        {},
      ),
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({
        queryKey: ["brain-agent-policy", variables.tenantId],
      });
    },
  });
}

export function useBrainExecuteAgentStep() {
  return useMutation({
    mutationFn: ({
      taskId,
      stepId,
    }: {
      taskId: string;
      stepId: string;
    }) =>
      apiPost<BrainAgentStepResult>(
        `${BASE}/agent/tasks/${taskId}/steps/${stepId}/execute`,
        {},
      ),
  });
}

export function useBrainAgentTaskStatus(taskId: string | null) {
  return useQuery<BrainAgentTaskStatus>({
    queryKey: ["brain-agent-task-status", taskId],
    queryFn: () => apiGet<BrainAgentTaskStatus>(`${BASE}/agent/tasks/${taskId}/status`),
    enabled: !!taskId,
  });
}

export function useBrainAgentPolicy(tenantId: number) {
  return useQuery<BrainAgentPolicy>({
    queryKey: ["brain-agent-policy", tenantId],
    queryFn: () => apiGet<BrainAgentPolicy>(`${BASE}/agent/policy/${tenantId}`),
    enabled: tenantId > 0,
  });
}

export function useBrainUpdateAgentPolicy() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({
      tenantId,
      workflowTypes,
      approvalGateRequired,
      stepBudget,
    }: {
      tenantId: number;
      workflowTypes: string[];
      approvalGateRequired: boolean;
      stepBudget: number;
    }) =>
      apiPost<BrainAgentPolicy>(
        `${BASE}/agent/policy/${tenantId}?approval_gate_required=${approvalGateRequired}&step_budget=${stepBudget}&${workflowTypes.map((wt) => `workflow_types=${wt}`).join("&")}`,
        {},
      ),
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({
        queryKey: ["brain-agent-policy", variables.tenantId],
      });
    },
  });
}

export function useBrainClaimNextAgentStep() {
  return useMutation({
    mutationFn: ({
      tenantId,
      workerId,
    }: {
      tenantId: number;
      workerId: string;
    }) =>
      apiPost<BrainAgentClaimResult>(
        `${BASE}/agent/tasks/claim?tenant_id=${tenantId}&worker_id=${workerId}`,
        {},
      ),
  });
}

export function useBrainCompleteAgentStep() {
  return useMutation({
    mutationFn: ({
      taskId,
      stepId,
      workerId,
      success,
      errorCode,
    }: {
      taskId: string;
      stepId: string;
      workerId: string;
      success: boolean;
      errorCode?: string;
    }) =>
      apiPost<BrainAgentCompleteResult>(
        `${BASE}/agent/tasks/${taskId}/steps/${stepId}/complete?worker_id=${workerId}&success=${success}${errorCode ? `&error_code=${errorCode}` : ""}`,
        {},
      ),
  });
}

export function useBrainAgentSlaReport(tenantId: number, slaSeconds = 300) {
  return useQuery<BrainAgentSlaReport>({
    queryKey: ["brain-agent-sla", tenantId, slaSeconds],
    queryFn: () => apiGet<BrainAgentSlaReport>(`${BASE}/agent/sla/${tenantId}?sla_seconds=${slaSeconds}`),
    enabled: tenantId > 0,
  });
}

export function useBrainAgentQueueMetrics(tenantId: number) {
  return useQuery<BrainAgentQueueMetrics>({
    queryKey: ["brain-agent-queue", tenantId],
    queryFn: () => apiGet<BrainAgentQueueMetrics>(`${BASE}/agent/queue/${tenantId}`),
    enabled: tenantId > 0,
  });
}

// Phase XXIII — Agent Observability & Telemetry
export function useBrainLogAgentStepEvent() {
  return useMutation<
    BrainAgentStepEventLogResult,
    Error,
    { taskId: string; stepId: string; eventType: string; payload?: Record<string, unknown> }
  >({
    mutationFn: ({ taskId, stepId, eventType, payload = {} }) =>
      apiPost<BrainAgentStepEventLogResult>(
        `${BASE}/agent/tasks/${taskId}/steps/${stepId}/log`,
        { event_type: eventType, payload },
      ),
  });
}

export function useBrainAgentStepLog(taskId: string, stepId: string) {
  return useQuery<BrainAgentStepLog>({
    queryKey: ["brain-agent-step-log", taskId, stepId],
    queryFn: () => apiGet<BrainAgentStepLog>(`${BASE}/agent/tasks/${taskId}/steps/${stepId}/log`),
    enabled: Boolean(taskId) && Boolean(stepId),
  });
}

export function useBrainAgentTaskAudit(taskId: string) {
  return useQuery<BrainAgentTaskAudit>({
    queryKey: ["brain-agent-task-audit", taskId],
    queryFn: () => apiGet<BrainAgentTaskAudit>(`${BASE}/agent/tasks/${taskId}/audit`),
    enabled: Boolean(taskId),
  });
}

export function useBrainAgentPerformanceReport(tenantId: number, windowHours = 24) {
  return useQuery<BrainAgentPerformanceReport>({
    queryKey: ["brain-agent-performance", tenantId, windowHours],
    queryFn: () =>
      apiGet<BrainAgentPerformanceReport>(`${BASE}/agent/performance/${tenantId}?window_hours=${windowHours}`),
    enabled: tenantId > 0,
  });
}

// ---------------------------------------------------------------------------
// Phase XXIV — Agent Dependency & Resource Control
// ---------------------------------------------------------------------------

export function useBrainSetStepDependencies() {
  return useMutation<BrainAgentStepDependencies, unknown, { taskId: string; stepId: string; depends_on: string[] }>({
    mutationFn: ({ taskId, stepId, depends_on }) =>
      apiPost<BrainAgentStepDependencies>(
        `${BASE}/agent/tasks/${taskId}/steps/${stepId}/dependencies`,
        { depends_on },
      ),
  });
}

export function useBrainAgentReadyQueue(taskId: string) {
  return useQuery<BrainAgentReadyQueue>({
    queryKey: ["brain-agent-ready-queue", taskId],
    queryFn: () => apiGet<BrainAgentReadyQueue>(`${BASE}/agent/tasks/${taskId}/ready-queue`),
    enabled: Boolean(taskId),
  });
}

export function useBrainSetTaskResourceBudget() {
  return useMutation<BrainAgentResourceBudget, unknown, { taskId: string; token_limit: number; cost_limit_usd: number }>({
    mutationFn: ({ taskId, token_limit, cost_limit_usd }) =>
      apiPost<BrainAgentResourceBudget>(
        `${BASE}/agent/tasks/${taskId}/resources`,
        { token_limit, cost_limit_usd },
      ),
  });
}

export function useBrainTaskResourceUsage(taskId: string) {
  return useQuery<BrainAgentResourceUsage>({
    queryKey: ["brain-task-resource-usage", taskId],
    queryFn: () => apiGet<BrainAgentResourceUsage>(`${BASE}/agent/tasks/${taskId}/resources`),
    enabled: Boolean(taskId),
  });
}

export function useBrainRecordOutcomeFeedback() {
  return useMutation<BrainAgentOutcomeFeedbackResult, unknown, { taskId: string; quality_score: number; notes?: string }>({
    mutationFn: ({ taskId, quality_score, notes = "" }) =>
      apiPost<BrainAgentOutcomeFeedbackResult>(
        `${BASE}/agent/tasks/${taskId}/feedback`,
        { quality_score, notes },
      ),
  });
}

export function useBrainAgentOutcomeSummary(tenantId: number) {
  return useQuery<BrainAgentOutcomeSummary>({
    queryKey: ["brain-agent-outcome-summary", tenantId],
    queryFn: () => apiGet<BrainAgentOutcomeSummary>(`${BASE}/agent/outcomes/${tenantId}`),
    enabled: tenantId > 0,
  });
}

// Phase XXV — Agent Multi-Agent Collaboration & Handoff

export function useBrainInitiateHandoff() {
  return useMutation<
    BrainAgentHandoffResult,
    unknown,
    { fromTaskId: string; to_agent_id: string; context_snapshot?: Record<string, unknown> }
  >({
    mutationFn: ({ fromTaskId, to_agent_id, context_snapshot = {} }) =>
      apiPost<BrainAgentHandoffResult>(`${BASE}/agent/handoff/${fromTaskId}`, {
        to_agent_id,
        context_snapshot,
      }),
  });
}

export function useBrainHandoffStatus(handoffId: string) {
  return useQuery<BrainAgentHandoffStatus>({
    queryKey: ["brain-agent-handoff-status", handoffId],
    queryFn: () => apiGet<BrainAgentHandoffStatus>(`${BASE}/agent/handoff/${handoffId}`),
    enabled: Boolean(handoffId),
  });
}

export function useBrainAcceptHandoff() {
  return useMutation<{ handoff_id: string; status: string }, unknown, { handoffId: string }>({
    mutationFn: ({ handoffId }) =>
      apiPost<{ handoff_id: string; status: string }>(
        `${BASE}/agent/handoff/${handoffId}/accept`,
        {},
      ),
  });
}

export function useBrainSplitTask() {
  return useMutation<
    BrainAgentSplitResult,
    unknown,
    { taskId: string; split_strategy: string; subtask_configs: Record<string, unknown>[] }
  >({
    mutationFn: ({ taskId, split_strategy, subtask_configs }) =>
      apiPost<BrainAgentSplitResult>(`${BASE}/agent/tasks/${taskId}/split`, {
        split_strategy,
        subtask_configs,
      }),
  });
}

export function useBrainMergeResults() {
  return useMutation<BrainAgentMergeResult, unknown, { taskId: string; subtask_ids: string[] }>({
    mutationFn: ({ taskId, subtask_ids }) =>
      apiPost<BrainAgentMergeResult>(`${BASE}/agent/tasks/${taskId}/merge`, {
        subtask_ids,
      }),
  });
}

export function useBrainMergeStatus(taskId: string) {
  return useQuery<BrainAgentMergeResult>({
    queryKey: ["brain-agent-merge-status", taskId],
    queryFn: () => apiGet<BrainAgentMergeResult>(`${BASE}/agent/tasks/${taskId}/merge-status`),
    enabled: Boolean(taskId),
  });
}

// Phase XXVI — Agent Adaptive Learning & Self-Optimization

export function useBrainRecordLearningSignal() {
  const queryClient = useQueryClient();
  return useMutation<BrainAgentLearningSignalResult, Error, { taskId: string; agentId: string; signalType: string; value: number; context?: Record<string, unknown> }>({
    mutationFn: ({ taskId, agentId, signalType, value, context }) =>
      apiPost<BrainAgentLearningSignalResult>(`${BASE}/agent/tasks/${taskId}/learning`, {
        agent_id: agentId,
        signal_type: signalType,
        value,
        context,
      }),
    onSuccess: (_, { agentId }) => {
      queryClient.invalidateQueries({ queryKey: ["brain-agent-learning-summary", agentId] });
    },
  });
}

export function useBrainAgentLearningSummary(agentId: string) {
  return useQuery<BrainAgentLearningSummary>({
    queryKey: ["brain-agent-learning-summary", agentId],
    queryFn: () => apiGet<BrainAgentLearningSummary>(`${BASE}/agent/learning/${agentId}`),
    enabled: Boolean(agentId),
  });
}

export function useBrainOptimizeWorkflow() {
  const queryClient = useQueryClient();
  return useMutation<BrainAgentOptimizationResult, Error, { taskId: string; optimizationTarget: string; strategy?: string }>({
    mutationFn: ({ taskId, optimizationTarget, strategy }) =>
      apiPost<BrainAgentOptimizationResult>(`${BASE}/agent/tasks/${taskId}/optimize`, {
        optimization_target: optimizationTarget,
        strategy,
      }),
    onSuccess: (_, { taskId }) => {
      queryClient.invalidateQueries({ queryKey: ["brain-agent-optimize-history", taskId] });
    },
  });
}

export function useBrainOptimizationHistory(taskId: string) {
  return useQuery<BrainAgentOptimizationHistory>({
    queryKey: ["brain-agent-optimize-history", taskId],
    queryFn: () => apiGet<BrainAgentOptimizationHistory>(`${BASE}/agent/tasks/${taskId}/optimize-history`),
    enabled: Boolean(taskId),
  });
}

export function useBrainBenchmarkAgent() {
  const queryClient = useQueryClient();
  return useMutation<BrainAgentBenchmarkRecord, Error, { agentId: string; metric: string; observedValue: number; baselineValue: number }>({
    mutationFn: ({ agentId, metric, observedValue, baselineValue }) =>
      apiPost<BrainAgentBenchmarkRecord>(`${BASE}/agent/benchmark`, {
        agent_id: agentId,
        metric,
        observed_value: observedValue,
        baseline_value: baselineValue,
      }),
    onSuccess: (_, { agentId }) => {
      queryClient.invalidateQueries({ queryKey: ["brain-agent-benchmark", agentId] });
    },
  });
}

export function useBrainAgentBenchmark(agentId: string) {
  return useQuery<BrainAgentBenchmarkSummary>({
    queryKey: ["brain-agent-benchmark", agentId],
    queryFn: () => apiGet<BrainAgentBenchmarkSummary>(`${BASE}/agent/benchmark/${agentId}`),
    enabled: Boolean(agentId),
  });
}

// Phase XXVII — Agent Knowledge Graph & Cross-Agent Memory

export function useBrainStoreKnowledge() {
  const queryClient = useQueryClient();
  return useMutation<BrainAgentKnowledgeRecord, Error, { agentId: string; key: string; value: unknown; confidence: number }>({
    mutationFn: ({ agentId, key, value, confidence }) =>
      apiPost<BrainAgentKnowledgeRecord>(`${BASE}/agent/knowledge`, {
        agent_id: agentId,
        key,
        value,
        confidence,
      }),
    onSuccess: (_, { agentId, key }) => {
      queryClient.invalidateQueries({ queryKey: ["brain-agent-knowledge", agentId, key] });
      queryClient.invalidateQueries({ queryKey: ["brain-agent-knowledge-health", agentId] });
    },
  });
}

export function useBrainRetrieveKnowledge(agentId: string, key: string) {
  return useQuery<BrainAgentKnowledgeRecord>({
    queryKey: ["brain-agent-knowledge", agentId, key],
    queryFn: () => apiGet<BrainAgentKnowledgeRecord>(`${BASE}/agent/knowledge/${agentId}/${key}`),
    enabled: Boolean(agentId) && Boolean(key),
  });
}

export function useBrainShareKnowledge() {
  const queryClient = useQueryClient();
  return useMutation<BrainAgentKnowledgeShareResult, Error, { fromAgentId: string; toAgentId: string; key: string }>({
    mutationFn: ({ fromAgentId, toAgentId, key }) =>
      apiPost<BrainAgentKnowledgeShareResult>(`${BASE}/agent/knowledge/share`, {
        from_agent_id: fromAgentId,
        to_agent_id: toAgentId,
        key,
      }),
    onSuccess: (_, { toAgentId }) => {
      queryClient.invalidateQueries({ queryKey: ["brain-agent-shared-knowledge", toAgentId] });
    },
  });
}

export function useBrainSharedKnowledge(agentId: string) {
  return useQuery<BrainAgentSharedKnowledgeSummary>({
    queryKey: ["brain-agent-shared-knowledge", agentId],
    queryFn: () => apiGet<BrainAgentSharedKnowledgeSummary>(`${BASE}/agent/knowledge/${agentId}/shared`),
    enabled: Boolean(agentId),
  });
}

export function useBrainExpireKnowledge() {
  const queryClient = useQueryClient();
  return useMutation<BrainAgentKnowledgeExpireResult, Error, { agentId: string; maxAgeHours: number }>({
    mutationFn: ({ agentId, maxAgeHours }) =>
      apiPost<BrainAgentKnowledgeExpireResult>(`${BASE}/agent/knowledge/${agentId}/expire`, {
        max_age_hours: maxAgeHours,
      }),
    onSuccess: (_, { agentId }) => {
      queryClient.invalidateQueries({ queryKey: ["brain-agent-knowledge-health", agentId] });
    },
  });
}

export function useBrainKnowledgeHealth(agentId: string) {
  return useQuery<BrainAgentKnowledgeHealth>({
    queryKey: ["brain-agent-knowledge-health", agentId],
    queryFn: () => apiGet<BrainAgentKnowledgeHealth>(`${BASE}/agent/knowledge/${agentId}/health`),
    enabled: Boolean(agentId),
  });
}

// Phase XXVIII — Decision Replay & Recovery

/** Replay (or dry-run) a signal by signal_id. */
export function useBrainReplaySignal() {
  const qc = useQueryClient();
  return useMutation<BrainReplayResult, Error, { signalId: string; payload: BrainReplayRequest }>({
    mutationFn: ({ signalId, payload }) =>
      apiPost<BrainReplayResult>(`${BASE}/reprocess/${signalId}`, payload),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["brain-replay-audit"] });
    },
  });
}

/** Fetch replay audit trail, optionally filtered by signal_id and/or event_type. */
export function useBrainReplayAudit(params?: { signalId?: string; eventType?: string; limit?: number }) {
  const searchParams = new URLSearchParams();
  if (params?.signalId) searchParams.set("signal_id", params.signalId);
  if (params?.eventType) searchParams.set("event_type", params.eventType);
  if (params?.limit != null) searchParams.set("limit", String(params.limit));
  const qs = searchParams.toString();
  return useQuery<BrainReplayAuditResponse>({
    queryKey: ["brain-replay-audit", params],
    queryFn: () => apiGet<BrainReplayAuditResponse>(`${BASE}/replay-audit${qs ? `?${qs}` : ""}`),
  });
}

// Phase XXIX — Replay Governance & Operator Control

/** Approve a pending signal replay by signal_id. */
export function useBrainApproveReplay() {
  const qc = useQueryClient();
  return useMutation<BrainReplayApproveResult, Error, { signalId: string; payload: BrainReplayApproveRequest }>({
    mutationFn: ({ signalId, payload }) =>
      apiPost<BrainReplayApproveResult>(`${BASE}/reprocess/${signalId}/approve`, payload),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["brain-replay-audit"] });
    },
  });
}

/** Reject a pending signal replay by signal_id. */
export function useBrainRejectReplay() {
  const qc = useQueryClient();
  return useMutation<BrainReplayRejectResult, Error, { signalId: string; payload: BrainReplayRejectRequest }>({
    mutationFn: ({ signalId, payload }) =>
      apiPost<BrainReplayRejectResult>(`${BASE}/reprocess/${signalId}/reject`, payload),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["brain-replay-audit"] });
    },
  });
}

/** Cancel an in-flight signal replay by signal_id. */
export function useBrainCancelReplay() {
  const qc = useQueryClient();
  return useMutation<BrainReplayCancelResult, Error, { signalId: string; payload: BrainReplayCancelRequest }>({
    mutationFn: ({ signalId, payload }) =>
      apiPost<BrainReplayCancelResult>(`${BASE}/reprocess/${signalId}/cancel`, payload),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["brain-replay-audit"] });
    },
  });
}

// ── XXX — Replay Analytics & Operator Insights ─────────────────────────

/** Fetch replay analytics for a tenant. */
export function useBrainReplayAnalytics(tenantId: number, windowDays = 30) {
  return useQuery<BrainReplayAnalytics>({
    queryKey: ["brain-replay-analytics", tenantId, windowDays],
    queryFn: () =>
      apiGet<BrainReplayAnalytics>(
        `${BASE}/reprocess/analytics/${tenantId}?window_days=${windowDays}`
      ),
    enabled: tenantId > 0,
  });
}

/** Fetch active replay trend alerts for a tenant. */
export function useBrainReplayTrendAlerts(
  tenantId: number,
  rejectRateThreshold = 0.5
) {
  return useQuery<BrainReplayTrendAlert[]>({
    queryKey: ["brain-replay-trend-alerts", tenantId, rejectRateThreshold],
    queryFn: () =>
      apiGet<BrainReplayTrendAlert[]>(
        `${BASE}/reprocess/alerts/${tenantId}?reject_rate_threshold=${rejectRateThreshold}`
      ),
    enabled: tenantId > 0,
  });
}

/** Fetch operator action summary by actor name. */
export function useBrainReplayOperatorSummary(actor: string, windowDays = 30) {
  return useQuery<BrainReplayOperatorSummary>({
    queryKey: ["brain-replay-operator-summary", actor, windowDays],
    queryFn: () =>
      apiGet<BrainReplayOperatorSummary>(
        `${BASE}/reprocess/operator-summary/${encodeURIComponent(actor)}?window_days=${windowDays}`
      ),
    enabled: actor.length > 0,
  });
}

// ── XXXI — Replay Policy Configuration & Tenant-Scoped Governance Settings ─

/** Fetch tenant-scoped replay governance policy. */
export function useBrainReplayPolicy(tenantId: number) {
  return useQuery<BrainReplayPolicy>({
    queryKey: ["brain-replay-policy", tenantId],
    queryFn: () => apiGet<BrainReplayPolicy>(`${BASE}/reprocess/policy/${tenantId}`),
    enabled: tenantId > 0,
  });
}

/** Update tenant-scoped replay governance policy. */
export function useBrainReplayPolicyMutation(tenantId: number) {
  const qc = useQueryClient();
  return useMutation<BrainReplayPolicy, Error, Omit<BrainReplayPolicy, "tenant_id"> & { actor: string }>({
    mutationFn: (payload) =>
      apiPut<BrainReplayPolicy>(`${BASE}/reprocess/policy/${tenantId}`, payload),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["brain-replay-policy", tenantId] });
      qc.invalidateQueries({ queryKey: ["brain-replay-policy-history", tenantId] });
    },
  });
}

/** Fetch policy change history for a tenant. */
export function useBrainReplayPolicyHistory(tenantId: number) {
  return useQuery<BrainReplayPolicyHistoryEntry[]>({
    queryKey: ["brain-replay-policy-history", tenantId],
    queryFn: () =>
      apiGet<BrainReplayPolicyHistoryEntry[]>(`${BASE}/reprocess/policy/${tenantId}/history`),
    enabled: tenantId > 0,
  });
}

/** Check whether a replay action is allowed under current policy. */
export function useBrainReplayPolicyCheck(tenantId: number, actor: string, signalId: string) {
  return useQuery<BrainReplayPolicyCheckResult>({
    queryKey: ["brain-replay-policy-check", tenantId, actor, signalId],
    queryFn: () =>
      apiGet<BrainReplayPolicyCheckResult>(
        `${BASE}/reprocess/policy/${tenantId}/check?actor=${encodeURIComponent(actor)}&signal_id=${encodeURIComponent(signalId)}`
      ),
    enabled: tenantId > 0 && actor.length > 0 && signalId.length > 0,
  });
}

// ── XIX1 — Policy Reasoning Engine ────────────────────────────────────────

/** XIX1 — Analyze and reason about tenant's policy effectiveness. */
export function useBrainPolicyReasoning(tenantId: number) {
  return useQuery<BrainPolicyReasoningResult_XIX>({
    queryKey: ["brain-policy-reasoning", tenantId],
    queryFn: () =>
      apiGet<BrainPolicyReasoningResult_XIX>(`${BASE}/reasoning/policy/${tenantId}`),
    enabled: tenantId > 0,
  });
}

// ── XIX3 — Cross-Tenant Learning ──────────────────────────────────────────

/** XIX3 — Get recommendations from peer tenants, excluding current tenant. */
export function useBrainCrossTenantRecommendations(tenantId: number) {
  return useQuery<BrainCrossTenantRecommendationsResult_XIX>({
    queryKey: ["brain-cross-tenant-recommendations", tenantId],
    queryFn: () =>
      apiGet<BrainCrossTenantRecommendationsResult_XIX>(
        `${BASE}/cross-tenant-recommendations/${tenantId}`
      ),
    enabled: tenantId > 0,
  });
}

// ── XIX4 — Predictive Policy Optimization ────────────────────────────────

/** XIX4 — Predict outcomes of policy optimization. */
export function useBrainPredictiveOptimization(tenantId: number, horizonDays?: number) {
  return useQuery<BrainPredictivePolicyOptimizationResult_XIX>({
    queryKey: ["brain-predictive-optimization", tenantId, horizonDays],
    queryFn: () => {
      const params = new URLSearchParams();
      if (horizonDays !== undefined) {
        params.append("horizon_days", String(horizonDays));
      }
      const url = `${BASE}/policy-optimization/${tenantId}${params.toString() ? `?${params}` : ""}`;
      return apiGet<BrainPredictivePolicyOptimizationResult_XIX>(url);
    },
    enabled: tenantId > 0,
  });
}

// ── XX1 — Policy Rollout Plan ─────────────────────────────────────────────

/** XX1 — Generate staged policy rollout plan. */
export function useBrainPolicyRolloutPlan(tenantId: number, horizonDays?: number) {
  return useQuery<BrainPolicyRolloutPlanResult_XX>({
    queryKey: ["brain-policy-rollout-plan", tenantId, horizonDays],
    queryFn: () => {
      const params = new URLSearchParams();
      if (horizonDays !== undefined) {
        params.append("horizon_days", String(horizonDays));
      }
      const url = `${BASE}/policy-rollout-plan/${tenantId}${params.toString() ? `?${params}` : ""}`;
      return apiGet<BrainPolicyRolloutPlanResult_XX>(url);
    },
    enabled: tenantId > 0,
  });
}

// ── Legacy aliases (backward compat for existing pages) ───────────────────
export const useBrainPredictivePolicyOptimization = useBrainPredictiveOptimization;
