export enum MetricGroupId {
  EXECUTIVE_OVERVIEW = 'EXECUTIVE_OVERVIEW',
  ASSIGNMENT_EXECUTION = 'ASSIGNMENT_EXECUTION',
  DOCUMENT_WORKFLOW = 'DOCUMENT_WORKFLOW',
  DECREE_WORKFLOW = 'DECREE_WORKFLOW',
  CORRESPONDENCE_WORKFLOW = 'CORRESPONDENCE_WORKFLOW',
  SLA_RISK_BOTTLENECK = 'SLA_RISK_BOTTLENECK',
  STRATEGY_KPI = 'STRATEGY_KPI',
  AUDIT_COMPLIANCE = 'AUDIT_COMPLIANCE',
  DEPARTMENT_PERFORMANCE = 'DEPARTMENT_PERFORMANCE',
}

export enum MetricRuntimeStatus {
  FOUNDATION_CONTRACT_ONLY = 'FOUNDATION_CONTRACT_ONLY',
  DEFERRED_UNTIL_STRATEGY_MODULE = 'DEFERRED_UNTIL_STRATEGY_MODULE',
  COMPUTED = 'COMPUTED',
  UNAVAILABLE = 'UNAVAILABLE',
}

export enum MetricReadiness {
  CONTRACT_DEFINED = 'CONTRACT_DEFINED',
  FUTURE_CONTRACT = 'FUTURE_CONTRACT',
  COMPUTED_READY = 'COMPUTED_READY',
  INCOMPLETE_SOURCE = 'INCOMPLETE_SOURCE',
}

export enum MetricFailureMode {
  INCOMPLETE_DATA = 'INCOMPLETE_DATA',
  PERMISSION_DENIED = 'PERMISSION_DENIED',
  STALE_DATA = 'STALE_DATA',
  SOURCE_UNAVAILABLE = 'SOURCE_UNAVAILABLE',
  DATA_SOURCE_MISMATCH = 'DATA_SOURCE_MISMATCH',
  FAKE_METRICS_BLOCKED = 'FAKE_METRICS_BLOCKED',
}

export interface EvidenceLink {
  label: string;
  source_module: string;
  source_entity?: string | null;
  source_table?: string | null;
  reference_field?: string | null;
  reference_value?: string | number | null;
  url?: string | null;
  available: boolean;
  limitations: string[];
}

export interface ExecutiveControlTowerMetric {
  metric_id: string;
  metric_group: MetricGroupId | string;
  label: string;
  description: string;
  value: number | string | null;
  unit?: string | null;
  source_module: string;
  source_entities: string[];
  source_tables: string[];
  source_fields: string[];
  calculation_method: string;
  formula: string;
  tenant_scope: string;
  permission_required: string;
  freshness_timestamp?: string | null;
  staleness_threshold_minutes?: number | null;
  evidence_links: EvidenceLink[];
  data_source: string;
  fake_metrics: boolean;
  incomplete_data: boolean;
  limitations: string[];
  failure_mode: MetricFailureMode | string;
  runtime_status: MetricRuntimeStatus | string;
  readiness: MetricReadiness | string;
}

export interface ExecutiveControlTowerMetricGroup {
  group_id: MetricGroupId | string;
  label: string;
  description: string;
  metrics: ExecutiveControlTowerMetric[];
  fake_metrics: boolean;
  data_source: string;
  incomplete_data: boolean;
  limitations: string[];
}

export interface ExecutiveControlTowerResponseBase {
  fake_metrics: boolean;
  data_source: string;
  incomplete_data: boolean;
  generated_at: string;
  limitations: string[];
}

export interface MetricRegistryResponse extends ExecutiveControlTowerResponseBase {
  groups: ExecutiveControlTowerMetricGroup[];
  total_metrics: number;
}

export interface MetricDetailResponse extends ExecutiveControlTowerResponseBase {
  metric: ExecutiveControlTowerMetric;
}

export interface ExecutiveControlTowerSummaryResponse extends ExecutiveControlTowerResponseBase {
  groups: ExecutiveControlTowerMetricGroup[];
}

export interface AssignmentExecutionSummaryResponse extends ExecutiveControlTowerResponseBase {
  metric_group: MetricGroupId | string;
  group_label: string;
  metrics: ExecutiveControlTowerMetric[];
}

export interface DocumentWorkflowSummaryResponse extends ExecutiveControlTowerResponseBase {
  metric_group: MetricGroupId | string;
  group_label: string;
  metrics: ExecutiveControlTowerMetric[];
}

export interface DecreeWorkflowSummaryResponse extends ExecutiveControlTowerResponseBase {
  metric_group: MetricGroupId | string;
  group_label: string;
  metrics: ExecutiveControlTowerMetric[];
}

export interface CorrespondenceWorkflowSummaryResponse extends ExecutiveControlTowerResponseBase {
  metric_group: MetricGroupId | string;
  group_label: string;
  metrics: ExecutiveControlTowerMetric[];
}

export interface SlaRiskBottleneckSummaryResponse extends ExecutiveControlTowerResponseBase {
  metric_group: MetricGroupId | string;
  group_label: string;
  metrics: ExecutiveControlTowerMetric[];
}

export interface StrategyKpiSummaryResponse extends ExecutiveControlTowerResponseBase {
  metric_group: MetricGroupId | string;
  group_label: string;
  metrics: ExecutiveControlTowerMetric[];
}

export interface AuditComplianceSummaryResponse extends ExecutiveControlTowerResponseBase {
  metric_group: MetricGroupId | string;
  group_label: string;
  metrics: ExecutiveControlTowerMetric[];
}

export interface DepartmentPerformanceSummaryResponse extends ExecutiveControlTowerResponseBase {
  metric_group: MetricGroupId | string;
  group_label: string;
  metrics: ExecutiveControlTowerMetric[];
}

export interface ExecutiveControlTowerHealthResponse extends ExecutiveControlTowerResponseBase {
  total_groups: number;
  total_metrics: number;
  registry_valid: boolean;
  validation_errors: string[];
  read_only_foundation: boolean;
  runtime_status: MetricRuntimeStatus | string;
}

export type SectionSummaryResponse =
  | AssignmentExecutionSummaryResponse
  | DocumentWorkflowSummaryResponse
  | DecreeWorkflowSummaryResponse
  | CorrespondenceWorkflowSummaryResponse
  | SlaRiskBottleneckSummaryResponse
  | StrategyKpiSummaryResponse
  | AuditComplianceSummaryResponse
  | DepartmentPerformanceSummaryResponse;

export interface MetricDisplayState {
  blocked: boolean;
  unavailable: boolean;
  stale: boolean;
  futureContract: boolean;
  foundationOnly: boolean;
  incomplete: boolean;
  label: string;
}