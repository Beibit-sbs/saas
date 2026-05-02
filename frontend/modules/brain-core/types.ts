export interface BrainPolicyProfile {
  tenant_id: number;
  autonomy_level: number;
  require_approval_for_critical: boolean;
  default_approval_role: string;
  enable_ai_reasoning: boolean;
}

export interface BrainPolicyTuningMetrics {
  total_outcomes: number;
  positive: number;
  negative: number;
  neutral: number;
  positive_rate: number;
  negative_rate: number;
}

export interface BrainPolicyTuningSuggestion {
  reason: string;
  changed: boolean;
  current_profile: BrainPolicyProfile;
  suggested_profile: BrainPolicyProfile;
  metrics: BrainPolicyTuningMetrics;
}

export interface BrainPolicyTuningApplyResult {
  status: string;
  changed: boolean;
  reason: string;
  actor: string;
  profile: BrainPolicyProfile;
  metrics: BrainPolicyTuningMetrics;
}

export interface BrainDecision {
  decision_id: string;
  tenant_id: number;
  correlation_id?: string;
  decision_type: string;
  situation_type?: string;
  priority: string;
  status: string;
  confidence_score?: number;
  severity_score?: number;
  urgency_score?: number;
  created_at?: string;
  updated_at?: string;
  policy_snapshot?: Record<string, unknown>;
}

export interface BrainOutcome {
  outcome_id: string;
  decision_id: string;
  tenant_id: number;
  outcome_type: string;
  effectiveness: string;
  outcome_payload?: Record<string, unknown>;
  created_at?: string;
}

export interface BrainExplanation {
  decision_id: string;
  summary: string;
  factors: string[];
  policy_notes: string[];
  expected_outcome: string;
}

export interface BrainPolicyUpdatePayload {
  autonomy_level: number;
  require_approval_for_critical: boolean;
  default_approval_role: string;
  enable_ai_reasoning: boolean;
  actor: string;
}

export interface BrainPolicyUpdateResult {
  status: string;
  updated_by: string;
  tenant_id: number;
  profile: BrainPolicyProfile;
}

export interface BrainCollectionResponse<T> {
  total: number;
  items: T[];
}

// XVII1 — Executive Brain KPI Dashboard
export interface BrainKPISignalVolume {
  total: number;
  by_type: Record<string, number>;
  high_severity: number;
}

export interface BrainKPIDecisionQuality {
  total_decisions: number;
  dispatched: number;
  approval_pending: number;
  dispatch_rate: number;
  avg_confidence: number;
  recommendation_trigger_eligible: boolean;
}

export interface BrainKPIOutcomeEffectiveness {
  total_outcomes: number;
  positive: number;
  negative: number;
  neutral: number;
  effectiveness_score: number;
}

export interface BrainKPITopRiskSignal {
  event_type: string;
  count: number;
}

export interface BrainKPIBrainHealth {
  policy_autonomy_level: number;
  ai_reasoning_enabled: boolean;
  requires_approval_for_critical: boolean;
  health_status: string;
}

export interface BrainKPIDashboard {
  tenant_id: number;
  signal_volume: BrainKPISignalVolume;
  decision_quality: BrainKPIDecisionQuality;
  outcome_effectiveness: BrainKPIOutcomeEffectiveness;
  top_risk_signals: BrainKPITopRiskSignal[];
  brain_health: BrainKPIBrainHealth;
}

// XVII1 — Proactive Recommendations
export interface BrainRecommendation {
  recommendation_id: string;
  tenant_id: number;
  category: string;
  severity: string;
  title: string;
  description: string;
  suggested_action: string;
  confidence: number;
  triggered_by: string[];
}

export interface BrainRecommendationsResponse {
  tenant_id: number;
  recommendations: BrainRecommendation[];
  generated_at: string;
}

// XVII2 — Predictive Risk
export interface BrainPredictionRequest {
  event_type: string;
  tenant_id: number;
  entity_id: string;
  history: number[];
  horizon_days: number;
}

export interface BrainPredictionResult {
  event_type: string;
  tenant_id: number;
  entity_id: string;
  predicted_score: number;
  risk_level: string;
  trajectory: string;
  confidence: number;
  factors: string[];
  horizon_days: number;
}

// XVII2 — Anomaly Detection
export interface BrainAnomalyRequest {
  tenant_id: number;
  metric_name: string;
  values: number[];
  entity_ids?: string[];
  z_threshold?: number;
}

export interface BrainAnomalyItem {
  index: number;
  entity_id: string;
  value: number;
  z_score: number;
  is_anomaly: boolean;
}

export interface BrainAnomalyResult {
  metric_name: string;
  tenant_id: number;
  method: string;
  anomalies: BrainAnomalyItem[];
  anomaly_count: number;
  mean: number;
  std: number;
}

// XVII4 — Brain Optimization
export interface BrainOptimizeRequest {
  tenant_id: number;
  domain_signals: Array<{
    domain: string;
    metric: string;
    value: number;
    threshold?: number;
  }>;
}

export interface BrainOptimizationRecommendation {
  domain: string;
  metric: string;
  current_value: number;
  recommended_action: string;
  priority: string;
  expected_improvement: number;
  rationale: string;
}

export interface BrainOptimizationResult {
  tenant_id: number;
  recommendations: BrainOptimizationRecommendation[];
  optimization_score: number;
  generated_at: string;
}

// XVII3 — Learning Evaluation
export interface BrainLearningEvaluationResult {
  tenant_id: number;
  total_decisions: number;
  total_outcomes: number;
  positive_outcomes: number;
  negative_outcomes: number;
  neutral_outcomes: number;
  effectiveness_score: number;
  policy_drift_detected: boolean;
  learning_ready: boolean;
  evaluated_at: string;
}

// XVIII1 — Learning Apply (Governance)
export interface BrainLearningApplyRequest {
  tenant_id: number;
  actor?: string;
  dry_run?: boolean;
  idempotency_key?: string;
}

export interface BrainLearningApplyResult {
  status: "preview" | "applied" | "skipped";
  dry_run: boolean;
  learning_ready: boolean;
  changed: boolean;
  reason: string;
  preview_profile?: BrainPolicyProfile;
  before_profile?: BrainPolicyProfile;
  suggested_profile?: BrainPolicyProfile;
  after_profile?: BrainPolicyProfile;
  applied_by?: string;
  applied_at?: string;
  profile?: BrainPolicyProfile;
  tenant_id: number;
}

export interface BrainPolicyReasoningRecommendation {
  recommendation: string;
  rationale: string;
  risk_level: "low" | "medium" | "high";
  expected_impact: "positive" | "neutral" | "negative";
}

export interface BrainAlternativePolicy {
  name: string;
  profile: BrainPolicyProfile;
  reasoning: string;
  adoption_risk: "low" | "medium" | "high";
  rationale: string;
}

export interface BrainPolicyReasoningResult {
  tenant_id: number;
  reasoning: string;
  current_profile: BrainPolicyProfile;
  recommendations: BrainPolicyReasoningRecommendation[];
  alternative_policies: BrainAlternativePolicy[];
  effectiveness_metrics: {
    tenant_id: number;
    total_outcomes: number;
    positive: number;
    neutral: number;
    negative: number;
    positive_rate: number;
    negative_rate: number;
  };
  timestamp: string;
}

export interface BrainCrossTenantRecommendationsResult {
  tenant_id: number;
  sample_size: number;
  recommended_profile: BrainPolicyProfile;
  peer_benchmarks: {
    avg_positive_rate: number;
    avg_negative_rate: number;
    ai_reasoning_adoption_rate: number;
    median_autonomy_level?: number;
  };
  rationale: string[];
  generated_at: string;
}

export interface BrainPredictivePolicyOptimizationResult {
  tenant_id: number;
  horizon_days: number;
  risk_score: number;
  forecast_band: "low" | "moderate" | "high";
  drivers: string[];
  current_profile: BrainPolicyProfile;
  predicted_profile: BrainPolicyProfile;
  recommended_actions: string[];
  generated_at: string;
}

export interface BrainPolicyRolloutPhase {
  phase: string;
  window_days: number;
  objective: string;
  actions: string[];
  gates: string[];
}

export interface BrainPolicyRolloutPlanResult {
  plan_id: string;
  tenant_id: number;
  horizon_days: number;
  risk_score: number;
  forecast_band: "low" | "moderate" | "high";
  current_profile: BrainPolicyProfile;
  target_profile: BrainPolicyProfile;
  has_material_change: boolean;
  can_auto_apply: boolean;
  peer_sample_size: number;
  top_recommendations: string[];
  phases: BrainPolicyRolloutPhase[];
  rollback_triggers: string[];
  generated_at: string;
}


export interface BrainPhaseMetrics {
  phase: string;
  plan_id: string;
  tenant_id: number;
  decisions_made: number;
  overrides_triggered: number;
  policy_changes_applied: number;
  avg_decision_latency_ms: number;
  negative_rate_change_pp: number;
  phase_status: "in_progress" | "baseline_collected" | "pilot_active" | "rollout_active" | "unknown_phase";
  started_at: string;
}

export interface BrainPhaseAuditEntry {
  tenant_id: number;
  plan_id: string;
  phase: string;
  action: "phase_started" | "phase_completed";
  metrics?: BrainPhaseMetrics;
  timestamp: string;
}

export interface BrainPolicyRolloutPhaseExecutionResult {
  plan_id: string;
  tenant_id: number;
  phase: string;
  execution_id: string;
  metrics: BrainPhaseMetrics;
  status: "success" | "already_executed";
  audit_trail: BrainPhaseAuditEntry[];
  completed_at: string;
}

export interface BrainRollbackAuditEntry {
  tenant_id: number;
  plan_id: string;
  action: "rollback_executed";
  trigger: string;
  rollback_id: string;
  current_profile: Record<string, unknown>;
  prior_profile: Record<string, unknown>;
  restore_status: "restored" | "restore_skipped";
  timestamp: string;
}

export interface BrainPolicyRollbackResult {
  rollback_id: string;
  plan_id: string;
  tenant_id: number;
  trigger: string;
  status: "rolled_back" | "invalid_trigger";
  prior_profile: Record<string, unknown> | null;
  restore_status?: "restored" | "restore_skipped";
  audit_trail: BrainRollbackAuditEntry[];
  rolled_back_at: string;
}

export interface BrainCrossTenantRolloutTenantResult {
  tenant_id: number;
  status: "success" | "already_executed" | "error";
  metrics?: BrainPhaseMetrics;
  error?: string;
}

export interface BrainCrossTenantRolloutResult {
  coordination_id: string;
  plan_id: string;
  phase: string;
  tenant_count: number;
  overall_status: "all_succeeded" | "partial_failure" | "all_failed";
  succeeded_tenants: number[];
  failed_tenants: number[];
  results: BrainCrossTenantRolloutTenantResult[];
  audit_trail: Record<string, unknown>[];
  coordinated_at: string;
}

// XXI — Autonomous Agent Workflows
export interface BrainAgentStep {
  step_id: string;
  index: number;
  name: string;
  status: "pending" | "running" | "done" | "blocked" | "corrected_pending";
  depends_on: string[];
  started_at?: string;
  completed_at?: string;
  correction_note?: string;
}

export interface BrainAgentTask {
  task_id: string | null;
  tenant_id: number;
  workflow_type: string;
  context: Record<string, unknown>;
  status: "pending" | "running" | "done" | "self_correcting" | "invalid_workflow_type";
  steps: BrainAgentStep[];
  created_at?: string;
}

export interface BrainAgentStepResult {
  task_id: string;
  step_id: string;
  step_name?: string;
  status: "done" | "blocked" | "task_not_found" | "step_not_found";
  task_status?: "pending" | "running" | "done" | "self_correcting";
  blocked_by?: string;
  executed_at?: string;
}

export interface BrainAgentTaskStatus {
  task_id: string;
  tenant_id?: number;
  workflow_type?: string;
  status: "pending" | "running" | "done" | "self_correcting" | "task_not_found";
  steps: BrainAgentStep[];
  correction_applied: boolean;
  retrieved_at: string;
}

export interface BrainAgentPolicy {
  tenant_id: number;
  allowed_workflow_types: string[];
  approval_gate_required: boolean;
  step_budget: number;
  policy_version: string;
  updated_at?: string;
  status?: "updated" | "invalid_workflow_type";
}

// XXII — Agent Execution Governance
export interface BrainAgentClaimResult {
  status: "claimed" | "none_available";
  tenant_id: number;
  task_id?: string;
  step_id?: string;
  step_name?: string;
  worker_id: string;
  claimed_at: string;
}

export interface BrainAgentCompleteResult {
  status: "completed" | "failed" | "task_not_found" | "step_not_found" | "not_running";
  task_id: string;
  step_id: string;
  step_status?: string;
  task_status?: string;
  retry_count?: number;
  completed_at?: string;
}

export interface BrainAgentSlaBreach {
  task_id: string;
  step_id: string;
  step_name?: string;
  elapsed_seconds: number;
  claimed_by?: string;
}

export interface BrainAgentSlaReport {
  tenant_id: number;
  sla_seconds: number;
  running_steps: number;
  breach_count: number;
  breaches: BrainAgentSlaBreach[];
  generated_at: string;
}

export interface BrainAgentQueueMetrics {
  tenant_id: number;
  tasks_total: number;
  steps_pending: number;
  steps_running: number;
  steps_done: number;
  steps_blocked: number;
  steps_corrected_pending: number;
  generated_at: string;
}

// Phase XXIII — Agent Observability & Telemetry
export interface BrainAgentStepEventLogResult {
  logged: boolean;
  seq: number;
  logged_at: string;
}

export interface BrainAgentStepEvent {
  task_id: string;
  step_id: string;
  event_type: string;
  payload: Record<string, unknown>;
  logged_at: string;
  seq: number;
}

export interface BrainAgentStepLog {
  task_id: string;
  step_id: string;
  event_count: number;
  events: BrainAgentStepEvent[];
}

export interface BrainAgentAuditEntry {
  action: string;
  step_id?: string;
  worker_id?: string;
  status?: string;
  ts?: string;
  detail: Record<string, unknown>;
}

export interface BrainAgentTaskAudit {
  task_id: string;
  found: boolean;
  workflow_type?: string;
  tenant_id?: number;
  task_status?: string;
  audit_event_count: number;
  audit_trail: BrainAgentAuditEntry[];
}

export interface BrainAgentPerformanceReport {
  tenant_id: number;
  window_hours: number;
  steps_total: number;
  steps_done: number;
  steps_failed: number;
  steps_retried: number;
  avg_step_duration_seconds: number | null;
  failure_rate: number;
  retry_rate: number;
  generated_at: string;
}

// ---------------------------------------------------------------------------
// Phase XXIV — Agent Dependency & Resource Control
// ---------------------------------------------------------------------------

export interface BrainAgentStepReadyItem {
  step_id: string;
  step_type: string | null;
  status: string;
}

export interface BrainAgentReadyQueue {
  task_id: string;
  ready_steps: BrainAgentStepReadyItem[];
  ready_count: number;
}

export interface BrainAgentStepDependencies {
  task_id: string;
  step_id: string;
  depends_on: string[];
}

export interface BrainAgentResourceBudget {
  task_id: string;
  token_limit: number;
  cost_limit_usd: number;
}

export interface BrainAgentResourceUsage {
  task_id: string;
  tokens_used: number;
  cost_usd: number;
  token_limit: number | null;
  cost_limit_usd: number | null;
  token_pct: number | null;
  cost_pct: number | null;
  budget_set: boolean;
}

export interface BrainAgentOutcomeFeedbackResult {
  task_id: string;
  quality_score: number;
  notes: string;
  recorded_at: string;
}

export interface BrainAgentOutcomeSummary {
  tenant_id: number;
  tasks_with_feedback: number;
  avg_quality_score: number | null;
  total_tenant_tasks: number;
  generated_at: string;
}

// Phase XXV — Agent Multi-Agent Collaboration & Handoff

export interface BrainAgentHandoffResult {
  handoff_id: string;
  status: 'pending' | 'accepted';
  to_agent_id: string;
}

export interface BrainAgentHandoffStatus {
  handoff_id: string;
  from_task_id: string;
  to_agent_id: string;
  tenant_id: number | null;
  context_snapshot: Record<string, unknown>;
  status: 'pending' | 'accepted';
  created_at: string;
  accepted_at: string | null;
}

export interface BrainAgentSubtask {
  subtask_id: string;
  parent_task_id: string;
  agent_id: string;
  workflow_type: string;
  context: Record<string, unknown>;
  status: string;
  created_at: string;
}

export interface BrainAgentSplitResult {
  task_id: string;
  split_strategy: string;
  subtask_count: number;
  subtasks: BrainAgentSubtask[];
  created_at: string;
}

export interface BrainAgentSubtaskResult {
  subtask_id: string;
  found: boolean;
  status: string;
  workflow_type: string | null;
}

export interface BrainAgentMergeConflict {
  workflow_type: string;
  subtask_ids: string[];
  statuses: string[];
}

export interface BrainAgentMergeResult {
  task_id: string;
  subtask_ids: string[];
  subtask_results: BrainAgentSubtaskResult[];
  conflicts_detected: number;
  conflicts: BrainAgentMergeConflict[];
  resolution: string;
  merged_at: string;
}

// Phase XXVI — Agent Adaptive Learning & Self-Optimization

export interface BrainAgentLearningSignalResult {
  task_id: string;
  agent_id: string;
  signal_type: string;
  value: number;
  total_signals_for_agent: number;
}

export interface BrainAgentSignalTypeSummary {
  count: number;
  average: number;
  min: number;
  max: number;
}

export interface BrainAgentLearningSummary {
  agent_id: string;
  total_signals: number;
  signal_types: Record<string, BrainAgentSignalTypeSummary>;
  average_value: number | null;
}

export interface BrainAgentOptimizationResult {
  task_id: string;
  optimization_target: string;
  strategy: string;
  applied_at: string;
  signals_considered: number;
  status: string;
}

export interface BrainAgentOptimizationHistory {
  task_id: string;
  total_optimizations: number;
  history: BrainAgentOptimizationResult[];
}

export interface BrainAgentBenchmarkRecord {
  agent_id: string;
  metric: string;
  observed_value: number;
  baseline_value: number;
  delta: number;
  pct_change: number;
  status: "improved" | "regressed" | "unchanged";
  benchmarked_at: string;
}

export interface BrainAgentBenchmarkSummary {
  agent_id: string;
  metrics: Record<string, BrainAgentBenchmarkRecord>;
  total_metrics: number;
}

// Phase XXVII — Agent Knowledge Graph & Cross-Agent Memory

export interface BrainAgentKnowledgeRecord {
  agent_id: string;
  key: string;
  value: unknown;
  confidence: number;
  prior_value: unknown | null;
  stored_at: string;
  expired: boolean;
}

export interface BrainAgentKnowledgeShareResult {
  from_agent_id: string;
  to_agent_id: string;
  key: string;
  value: unknown;
  confidence: number;
  conflict_detected: boolean;
  conflict_detail: Record<string, unknown> | null;
  shared_at: string;
}

export interface BrainAgentSharedKnowledgeSummary {
  agent_id: string;
  shared_entries: BrainAgentKnowledgeShareResult[];
  total: number;
  conflicts: number;
}

export interface BrainAgentKnowledgeExpireResult {
  agent_id: string;
  expired_count: number;
  expired_keys: string[];
  max_age_hours: number;
}

export interface BrainAgentKnowledgeHealth {
  agent_id: string;
  total_entries: number;
  active_entries: number;
  expired_entries: number;
  low_confidence_entries: number;
  health: "healthy" | "degraded";
}

// Phase XXVIII — Decision Replay & Recovery

export interface BrainReplayRequest {
  dry_run?: boolean;
  idempotency_key?: string | null;
  replay_reason?: string | null;
  expected_tenant_id?: number | null;
}

export interface BrainReplayDryRunResult {
  status: "dry_run";
  signal_id: string;
  tenant_id: number;
  event_type: string;
  replay_reason: string | null;
  idempotent_replay: boolean;
  would_process: boolean;
}

export interface BrainReplayExecuteResult {
  status: string;
  reprocessed_by: string;
  original_signal_id: string;
  replay_reason: string | null;
  idempotency_key: string | null;
  idempotent_replay: boolean;
}

export type BrainReplayResult = BrainReplayDryRunResult | BrainReplayExecuteResult;

export interface BrainReplayAuditRecord {
  event: "replay_requested" | "replay_executed" | "replay_rejected";
  signal_id: string;
  actor: string;
  reason?: string;
  tenant_id: number;
  recorded_at: string;
  dry_run?: boolean;
  idempotency_key?: string | null;
  replay_reason?: string | null;
  expected_tenant_id?: number;
  actual_tenant_id?: number;
}

export interface BrainReplayAuditResponse {
  total: number;
  records: BrainReplayAuditRecord[];
}

// Phase XXIX — Replay Governance & Operator Control

export interface BrainReplayApproveRequest {
  actor?: string | null;
  replay_reason?: string | null;
  expected_tenant_id?: number | null;
}

export interface BrainReplayApproveResult {
  status: "replay_approved";
  signal_id: string;
  actor: string;
  replay_reason: string | null;
  tenant_id: number;
  recorded_at: string;
}

export interface BrainReplayRejectRequest {
  actor?: string | null;
  reason?: string | null;
  expected_tenant_id?: number | null;
}

export interface BrainReplayRejectResult {
  status: "replay_rejected";
  signal_id: string;
  actor: string;
  reason: string | null;
  tenant_id: number;
  recorded_at: string;
}

export interface BrainReplayCancelRequest {
  actor?: string | null;
  reason?: string | null;
  expected_tenant_id?: number | null;
}

export interface BrainReplayCancelResult {
  status: "replay_cancelled";
  signal_id: string;
  actor: string;
  reason: string | null;
  tenant_id: number;
  recorded_at: string;
}

// ── XXX — Replay Analytics & Operator Insights ─────────────────────────

export interface BrainReplayTopActor {
  actor: string;
  actions: number;
}

export interface BrainReplayAnalytics {
  tenant_id: number;
  window_days: number;
  approved_count: number;
  rejected_count: number;
  cancelled_count: number;
  total_resolved: number;
  avg_resolution_seconds: number | null;
  top_actors: BrainReplayTopActor[];
}

export interface BrainReplayTrendAlert {
  alert_type: string;
  tenant_id: number;
  severity: "warning" | "critical";
  reject_rate: number;
  rejected_count: number;
  approved_count: number;
  trigger_reason: string;
  recorded_at: string;
}

export interface BrainReplayOperatorSummary {
  actor: string;
  window_days: number;
  approved_count: number;
  rejected_count: number;
  cancelled_count: number;
  total_actions: number;
  tenants_affected: number[];
}

// ── XXXI — Replay Policy Configuration & Tenant-Scoped Governance Settings ──

export interface BrainReplayPolicy {
  tenant_id: number;
  max_window_days: number;
  allowed_actors: string[] | null;
  auto_reject_threshold: number | null;
  require_dual_approval: boolean;
  max_replays_per_signal: number;
}

export interface BrainReplayPolicyHistoryEntry {
  event: string;
  tenant_id: number;
  actor: string;
  policy: Omit<BrainReplayPolicy, "tenant_id">;
  recorded_at: string;
}

export interface BrainReplayPolicyCheckResult {
  allowed: boolean;
  reason?: string;
}

// ── XIX1 — Policy Reasoning Engine ────────────────────────────────────────

export interface BrainPolicyReasoningRecommendation_XIX {
  recommendation: string;
  rationale: string;
  risk_level: "low" | "medium" | "high";
  expected_impact: "positive" | "neutral" | "negative";
}

export interface BrainAlternativePolicy_XIX {
  name: string;
  profile: {
    autonomy_level: number;
    risk_tolerance: string;
  };
  reasoning: string;
  adoption_risk: "low" | "medium" | "high";
  rationale: string;
}

export interface BrainPolicyReasoningResult_XIX {
  tenant_id: number;
  current_profile: {
    autonomy_level: number;
    risk_tolerance: string;
  };
  reasoning: string;
  recommendations: BrainPolicyReasoningRecommendation_XIX[];
  alternative_policies: BrainAlternativePolicy_XIX[];
  timestamp: string;
}

// ── XIX3 — Cross-Tenant Learning Aggregation ──────────────────────────────

export interface BrainCrossTenantRecommendationsResult_XIX {
  tenant_id: number;
  sample_size: number;
  recommended_profile: {
    tenant_id: number;
    autonomy_level: number;
    require_approval_for_critical: boolean;
    default_approval_role: string;
    enable_ai_reasoning: boolean;
  };
  peer_benchmarks: {
    avg_positive_rate: number;
    avg_negative_rate: number;
    ai_reasoning_adoption_rate: number;
    median_autonomy_level: number;
  };
  rationale: string[];
  generated_at: string;
}

// ── XIX4 — Predictive Policy Optimization ────────────────────────────────

export interface BrainPredictivePolicyOptimizationResult_XIX {
  tenant_id: number;
  horizon_days: number;
  risk_score: number;
  forecast_band: "low" | "moderate" | "high";
  current_profile: {
    autonomy_level: number;
    require_approval_for_critical: boolean;
  };
  predicted_profile: {
    autonomy_level: number;
    require_approval_for_critical: boolean;
  };
  drivers: string[];
  recommended_actions: string[];
  generated_at: string;
}

// ── XX1 — Policy Rollout Plan ─────────────────────────────────────────────

export interface BrainPolicyRolloutPhase_XX {
  phase: number;
  window_days: number;
  objective: string;
  actions: string[];
  gates: string[];
}

export interface BrainPolicyRolloutPlanResult_XX {
  plan_id: string;
  tenant_id: number;
  horizon_days: number;
  risk_score: number;
  forecast_band: "low" | "moderate" | "high";
  current_profile: {
    autonomy_level: number;
    require_approval_for_critical: boolean;
  };
  target_profile: {
    autonomy_level: number;
    require_approval_for_critical: boolean;
  };
  has_material_change: boolean;
  can_auto_apply: boolean;
  peer_sample_size: number;
  top_recommendations: string[];
  phases: BrainPolicyRolloutPhase_XX[];
  rollback_triggers: string[];
  generated_at: string;
}
