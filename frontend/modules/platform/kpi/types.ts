export interface RectorTrendPoint {
  snapshot_date: string;
  value: number;
}

export interface RectorKpiCard {
  metric_key: string;
  title: string;
  value: number;
  trend_7d: RectorTrendPoint[];
  metadata_json: Record<string, unknown>;
}

export interface RectorDashboard {
  tenant_id: number;
  snapshot_date: string;
  cards: RectorKpiCard[];
  generated_at: string | null;
  source: string;
}

export interface TenantMetricSnapshot {
  id: number;
  tenant_id: number;
  metric_key: string;
  metric_value: number;
  snapshot_date: string;
  metadata_json: Record<string, unknown>;
  created_at: string;
  updated_at: string;
  version: number;
}

export interface RectorKpiEvidenceSource {
  metric_key: string;
  label: string;
  value_label: string;
  source_domain: string;
  interpretation: string;
  available: boolean;
  lineage: Record<string, unknown> | null;
}

export interface RectorKpiEvidenceDrilldown {
  drilldown_id: string;
  title: string;
  domain_id: string;
  domain_title: string;
  source_metrics: string[];
  source_domains: string[];
  evidence_summary: string;
  explanation: string;
  risk_level: "critical" | "high" | "medium" | "low" | "unavailable";
  review_required: boolean;
  data_quality_note: string;
  readonly: boolean;
  tenant_scoped: boolean;
  optional: boolean;
  evidence_sources: RectorKpiEvidenceSource[];
}

export interface RectorKpiDrilldownSummary {
  tenant_id: number;
  snapshot_date: string;
  generated_at: string;
  domains: RectorKpiEvidenceDrilldown[];
  total_domains: number;
  review_required_count: number;
  unavailable_domains_count: number;
  critical_domains_count: number;
  high_domains_count: number;
  source: string;
  readonly: boolean;
  tenant_scoped: boolean;
  no_policy_enforcement: boolean;
  no_autonomous_decision: boolean;
  no_remediation_action: boolean;
}
