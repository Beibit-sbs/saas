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
