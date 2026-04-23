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
