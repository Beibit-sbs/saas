export interface AIUsageCostModelSummary {
  model_key: string;
  provider: string;
  requests_total: number;
  success_count: number;
  degraded_count: number;
  failed_count: number;
  total_tokens: number;
  avg_latency_ms: number;
  estimated_cost_usd: number;
}

export interface AIUsageCostSummary {
  tenant_id: number;
  requests_total: number;
  success_count: number;
  degraded_count: number;
  failed_count: number;
  total_tokens: number;
  avg_latency_ms: number;
  estimated_cost_usd: number;
  budget_limit_usd: number;
  budget_utilization_pct: number;
  budget_alert: boolean;
  budget_hard_cap: boolean;
  anomaly_detected: boolean;
  anomaly_score_z: number;
  anomaly_reason: string | null;
  models: AIUsageCostModelSummary[];
}

export interface AIUsageCostByUser {
  tenant_id: number;
  actor: string;
  requests_total: number;
  success_count: number;
  degraded_count: number;
  failed_count: number;
  total_tokens: number;
  avg_latency_ms: number;
  estimated_cost_usd: number;
}

export interface AIUsageCostByDepartment {
  tenant_id: number;
  department: string;
  requests_total: number;
  success_count: number;
  degraded_count: number;
  failed_count: number;
  total_tokens: number;
  avg_latency_ms: number;
  estimated_cost_usd: number;
}

export interface AIUsageCostTrendPoint {
  tenant_id: number;
  date: string;
  requests_total: number;
  total_tokens: number;
  estimated_cost_usd: number;
}

export interface AIUsageCostProjection {
  tenant_id: number;
  period: "daily";
  elapsed_requests: number;
  current_cost_usd: number;
  projected_cost_usd: number;
  projection_basis: string;
}

export interface AIUsageCostAnomaly {
  tenant_id: number;
  timestamp: string;
  model_key: string;
  provider: string;
  total_tokens: number;
  estimated_cost_usd: number;
  anomaly_score_z: number;
  anomaly_reason: string;
}

export interface AIUsageBudget {
  tenant_id: number;
  budget_limit_usd: number;
  alert_threshold_pct: number;
  hard_cap: boolean;
  updated_at: string;
}

export interface AIUsageBudgetPayload {
  budget_limit_usd: number;
  alert_threshold_pct?: number;
  hard_cap?: boolean;
}

export interface AIUsageBudgetStatus {
  tenant_id: number;
  scope: "tenant" | "department" | "user";
  scope_id: string | null;
  budget_limit_usd: number;
  current_cost_usd: number;
  utilization_pct: number;
  alert_threshold_pct: number;
  budget_alert: boolean;
  hard_cap: boolean;
  hard_cap_exceeded: boolean;
  updated_at: string;
}

export interface AISLOPolicy {
  tenant_id: number;
  model_key: string;
  p95_latency_ms: number;
  max_error_rate_pct: number;
  updated_at: string;
}

export interface AISLOCompliance {
  tenant_id: number;
  model_key: string;
  requests_total: number;
  p95_latency_ms_observed: number;
  error_rate_pct_observed: number;
  p95_latency_ms_target: number;
  max_error_rate_pct_target: number;
  latency_compliant: boolean;
  error_rate_compliant: boolean;
  compliant: boolean;
}

export interface AISLOViolation extends AISLOCompliance {
  violation_types: ("latency" | "error_rate")[];
}
