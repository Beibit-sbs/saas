export interface ReportingOverviewSummary {
  reporting_center_name: string;
  owner_module: string;
  active_reporting_cycles: number;
  active_submissions: number;
  active_deadlines: number;
  source_modules: string[];
  read_only: boolean;
}

export interface ProviderReadinessSummary {
  owner_module: string;
  provider_status_counts: Record<string, number>;
  provider_readiness: string;
  blocker_count: number;
  warning_count: number;
  live_integrations_enabled: boolean;
  sync_enabled: boolean;
  submission_execution_enabled: boolean;
  source_modules: string[];
  read_only: boolean;
}

export interface ComplianceSummary {
  owner_module: string;
  compliance_score: number;
  risk_band: string;
  source_modules: string[];
  read_only: boolean;
}

export interface DeadlineSummary {
  owner_module: string;
  active_deadlines: number;
  overdue_deadlines: number;
  upcoming_deadlines: number;
  deadline_signals: string[];
  source_modules: string[];
  read_only: boolean;
}

export interface ReportingStatusSummary {
  open_items: number;
  in_review_items: number;
  blocked_items: number;
  read_only: boolean;
}

export interface ReportingRuntimeShellResponse {
  tenant_id: number;
  reporting_center_name: string;
  active_reporting_cycles: number;
  active_submissions: number;
  active_deadlines: number;
  provider_readiness: ProviderReadinessSummary;
  compliance_score: number;
  generated_at: string;
  read_only: boolean;
  auditability_preserved: boolean;
  overview: ReportingOverviewSummary;
  compliance: ComplianceSummary;
  deadlines: DeadlineSummary;
  reporting_status: ReportingStatusSummary;
  widgets: string[];
  rbac_roles: string[];
}

export interface ReportingRegistryEntry {
  id: string;
  report_code: string;
  report_name: string;
  report_type: string;
  owner_module: string;
  reporting_period: string;
  submission_deadline: string;
  submission_status: string;
  compliance_status: string;
  provider_status: string;
  generated_at: string;
  read_only: boolean;
}

export interface ReportingTemplateSummary extends ReportingRegistryEntry {
  template_version: string;
  section_count: number;
}

export interface ReportingCycleSummary extends ReportingRegistryEntry {
  cycle_stage: string;
  active_days_remaining: number;
}

export interface ReportingSubmissionSummary extends ReportingRegistryEntry {
  submission_id: string;
  reviewer_required: boolean;
}

export interface ReportingRequirementSummary extends ReportingRegistryEntry {
  requirement_code: string;
  requirement_status: string;
}

export interface ReportingEvidenceSummary extends ReportingRegistryEntry {
  evidence_count: number;
  evidence_completeness: number;
}

export interface ReportingProviderSummary extends ReportingRegistryEntry {
  provider_key: string;
  live_integrations_enabled: boolean;
  submission_execution_enabled: boolean;
}

export interface ReportingStatusSummary extends ReportingRegistryEntry {
  risk_signal: string;
}

export interface ReportingRegistryResponse {
  tenant_id: number;
  generated_at: string;
  read_only: boolean;
  entries: ReportingRegistryEntry[];
  requirements: ReportingRequirementSummary[];
  statuses: ReportingStatusSummary[];
}

export interface ReportingTemplateResponse {
  tenant_id: number;
  generated_at: string;
  read_only: boolean;
  templates: ReportingTemplateSummary[];
}

export interface ReportingCycleResponse {
  tenant_id: number;
  generated_at: string;
  read_only: boolean;
  cycles: ReportingCycleSummary[];
}

export interface ReportingSubmissionResponse {
  tenant_id: number;
  generated_at: string;
  read_only: boolean;
  submissions: ReportingSubmissionSummary[];
}

export interface ReportingEvidenceResponse {
  tenant_id: number;
  generated_at: string;
  read_only: boolean;
  evidence: ReportingEvidenceSummary[];
}

export interface ReportingProviderResponse {
  tenant_id: number;
  generated_at: string;
  read_only: boolean;
  providers: ReportingProviderSummary[];
}

export interface MinistryReportingSummary {
  id: string;
  report_code: string;
  report_name: string;
  reporting_period: string;
  deadline: string;
  completion_percentage: number;
  readiness_status: string;
  submission_status: string;
  risk_level: string;
  days_remaining: number;
  owner_module: string;
  generated_at: string;
  read_only: boolean;
}

export interface MinistryReportingCycle extends MinistryReportingSummary {
  cycle_status: string;
}

export interface MinistryReportingDeadline extends MinistryReportingSummary {
  deadline_status: string;
  overdue: boolean;
}

export interface MinistryReportingReadiness extends MinistryReportingSummary {
  readiness_score: number;
}

export interface MinistryReportingCompleteness extends MinistryReportingSummary {
  required_data_points: number;
  completed_data_points: number;
}

export interface MinistryReportingRisk extends MinistryReportingSummary {
  signal_name: string;
  signal_owner_module: string;
}

export interface MinistryReportingSummaryResponse {
  tenant_id: number;
  generated_at: string;
  read_only: boolean;
  reports: MinistryReportingSummary[];
  signal_inventory: string[];
}

export interface MinistryReportingCycleResponse {
  tenant_id: number;
  generated_at: string;
  read_only: boolean;
  cycles: MinistryReportingCycle[];
}

export interface MinistryReportingDeadlineResponse {
  tenant_id: number;
  generated_at: string;
  read_only: boolean;
  deadlines: MinistryReportingDeadline[];
}

export interface MinistryReportingReadinessResponse {
  tenant_id: number;
  generated_at: string;
  read_only: boolean;
  readiness: MinistryReportingReadiness[];
}

export interface MinistryReportingCompletenessResponse {
  tenant_id: number;
  generated_at: string;
  read_only: boolean;
  completeness: MinistryReportingCompleteness[];
}

export interface MinistryReportingRiskResponse {
  tenant_id: number;
  generated_at: string;
  read_only: boolean;
  risks: MinistryReportingRisk[];
}

export interface AccreditationReportingSummary {
  id: string;
  accreditation_code: string;
  accreditation_name: string;
  accreditation_type: string;
  agency_name: string;
  deadline: string;
  completion_percentage: number;
  evidence_readiness: string;
  compliance_status: string;
  risk_level: string;
  days_remaining: number;
  owner_module: string;
  generated_at: string;
  read_only: boolean;
}

export interface AccreditationCycle extends AccreditationReportingSummary {
  cycle_status: string;
}

export interface AccreditationEvidenceReadiness extends AccreditationReportingSummary {
  readiness_score: number;
}

export interface AccreditationComplianceSummary extends AccreditationReportingSummary {
  compliance_score: number;
}

export interface AccreditationDeadlineSummary extends AccreditationReportingSummary {
  deadline_status: string;
  overdue: boolean;
}

export interface AccreditationRiskSummary extends AccreditationReportingSummary {
  signal_name: string;
  signal_owner_module: string;
}

export interface AccreditationReportingResponse {
  tenant_id: number;
  generated_at: string;
  read_only: boolean;
  reports: AccreditationReportingSummary[];
  signal_inventory: string[];
}

export interface AccreditationCycleResponse {
  tenant_id: number;
  generated_at: string;
  read_only: boolean;
  cycles: AccreditationCycle[];
}

export interface AccreditationEvidenceReadinessResponse {
  tenant_id: number;
  generated_at: string;
  read_only: boolean;
  readiness: AccreditationEvidenceReadiness[];
}

export interface AccreditationComplianceResponse {
  tenant_id: number;
  generated_at: string;
  read_only: boolean;
  compliance: AccreditationComplianceSummary[];
}

export interface AccreditationDeadlineResponse {
  tenant_id: number;
  generated_at: string;
  read_only: boolean;
  deadlines: AccreditationDeadlineSummary[];
}

export interface AccreditationRiskResponse {
  tenant_id: number;
  generated_at: string;
  read_only: boolean;
  risks: AccreditationRiskSummary[];
}

export interface RegulatoryReportingSummary {
  id: string;
  requirement_code: string;
  requirement_name: string;
  regulator_name: string;
  compliance_status: string;
  deadline: string;
  days_remaining: number;
  risk_level: string;
  document_status: string;
  owner_module: string;
  generated_at: string;
  read_only: boolean;
}

export interface RegulatoryRequirementSummary extends RegulatoryReportingSummary {
  requirement_status: string;
}

export interface RegulatoryComplianceSummary extends RegulatoryReportingSummary {
  compliance_score: number;
}

export interface RegulatoryDeadlineSummary extends RegulatoryReportingSummary {
  deadline_status: string;
  overdue: boolean;
}

export interface RegulatoryDocumentStatus extends RegulatoryReportingSummary {
  document_name: string;
  document_completeness: number;
}

export interface RegulatoryRiskSummary extends RegulatoryReportingSummary {
  signal_name: string;
  signal_owner_module: string;
}

export interface RegulatoryReportingResponse {
  tenant_id: number;
  generated_at: string;
  read_only: boolean;
  reports: RegulatoryReportingSummary[];
  signal_inventory: string[];
}

export interface RegulatoryRequirementResponse {
  tenant_id: number;
  generated_at: string;
  read_only: boolean;
  requirements: RegulatoryRequirementSummary[];
}

export interface RegulatoryComplianceResponse {
  tenant_id: number;
  generated_at: string;
  read_only: boolean;
  compliance: RegulatoryComplianceSummary[];
}

export interface RegulatoryDeadlineResponse {
  tenant_id: number;
  generated_at: string;
  read_only: boolean;
  deadlines: RegulatoryDeadlineSummary[];
}

export interface RegulatoryDocumentResponse {
  tenant_id: number;
  generated_at: string;
  read_only: boolean;
  documents: RegulatoryDocumentStatus[];
}

export interface RegulatoryRiskResponse {
  tenant_id: number;
  generated_at: string;
  read_only: boolean;
  risks: RegulatoryRiskSummary[];
}

export interface RankingReportingSummary {
  id: string;
  ranking_system: string;
  indicator_name: string;
  indicator_score: number;
  benchmark_score: number;
  trend_direction: string;
  readiness_level: string;
  risk_level: string;
  owner_module: string;
  generated_at: string;
  read_only: boolean;
}

export interface RankingIndicatorSummary extends RankingReportingSummary {
  indicator_weight: number;
}

export interface RankingReadinessSummary extends RankingReportingSummary {
  readiness_score: number;
}

export interface RankingBenchmarkSummary extends RankingReportingSummary {
  benchmark_gap: number;
}

export interface RankingTrendSummary extends RankingReportingSummary {
  trend_delta: number;
}

export interface RankingRiskSummary extends RankingReportingSummary {
  signal_name: string;
  signal_owner_module: string;
}

export interface RankingReportingResponse {
  tenant_id: number;
  generated_at: string;
  read_only: boolean;
  reports: RankingReportingSummary[];
  signal_inventory: string[];
}

export interface RankingIndicatorResponse {
  tenant_id: number;
  generated_at: string;
  read_only: boolean;
  indicators: RankingIndicatorSummary[];
}

export interface RankingReadinessResponse {
  tenant_id: number;
  generated_at: string;
  read_only: boolean;
  readiness: RankingReadinessSummary[];
}

export interface RankingBenchmarkResponse {
  tenant_id: number;
  generated_at: string;
  read_only: boolean;
  benchmarks: RankingBenchmarkSummary[];
}

export interface RankingTrendResponse {
  tenant_id: number;
  generated_at: string;
  read_only: boolean;
  trends: RankingTrendSummary[];
}

export interface RankingRiskResponse {
  tenant_id: number;
  generated_at: string;
  read_only: boolean;
  risks: RankingRiskSummary[];
}

export interface NobdReportingSummary {
  id: string;
  dataset_code: string;
  dataset_name: string;
  records_total: number;
  records_complete: number;
  completeness_percentage: number;
  quality_score: number;
  sync_status: string;
  risk_level: string;
  owner_module: string;
  generated_at: string;
  read_only: boolean;
}

export interface NobdDatasetSummary extends NobdReportingSummary {
  dataset_priority: string;
}

export interface NobdCompletenessSummary extends NobdReportingSummary {
  completeness_gap: number;
}

export interface NobdQualitySummary extends NobdReportingSummary {
  quality_band: string;
}

export interface NobdSyncStatusSummary extends NobdReportingSummary {
  sync_lag_hours: number;
}

export interface NobdRiskSummary extends NobdReportingSummary {
  signal_name: string;
  signal_owner_module: string;
}

export interface NobdReportingResponse {
  tenant_id: number;
  generated_at: string;
  read_only: boolean;
  reports: NobdReportingSummary[];
  signal_inventory: string[];
}

export interface NobdDatasetResponse {
  tenant_id: number;
  generated_at: string;
  read_only: boolean;
  datasets: NobdDatasetSummary[];
}

export interface NobdCompletenessResponse {
  tenant_id: number;
  generated_at: string;
  read_only: boolean;
  completeness: NobdCompletenessSummary[];
}

export interface NobdQualityResponse {
  tenant_id: number;
  generated_at: string;
  read_only: boolean;
  quality: NobdQualitySummary[];
}

export interface NobdSyncStatusResponse {
  tenant_id: number;
  generated_at: string;
  read_only: boolean;
  sync_status: NobdSyncStatusSummary[];
}

export interface NobdRiskResponse {
  tenant_id: number;
  generated_at: string;
  read_only: boolean;
  risks: NobdRiskSummary[];
}

export interface ComplianceMonitoringSummary {
  id: string;
  control_code: string;
  control_name: string;
  compliance_status: string;
  readiness_score: number;
  risk_level: string;
  gap_count: number;
  owner_module: string;
  generated_at: string;
  read_only: boolean;
}

export interface ComplianceControlSummary extends ComplianceMonitoringSummary {
  control_type: string;
}

export interface ComplianceReadinessSummary extends ComplianceMonitoringSummary {
  readiness_level: string;
}

export interface ComplianceGapSummary extends ComplianceMonitoringSummary {
  gap_severity: string;
}

export interface ComplianceRiskSummary extends ComplianceMonitoringSummary {
  signal_name: string;
  signal_owner_module: string;
}

export interface ComplianceMonitoringResponse {
  tenant_id: number;
  generated_at: string;
  read_only: boolean;
  reports: ComplianceMonitoringSummary[];
  signal_inventory: string[];
}

export interface ComplianceControlResponse {
  tenant_id: number;
  generated_at: string;
  read_only: boolean;
  controls: ComplianceControlSummary[];
}

export interface ComplianceReadinessResponse {
  tenant_id: number;
  generated_at: string;
  read_only: boolean;
  readiness: ComplianceReadinessSummary[];
}

export interface ComplianceGapResponse {
  tenant_id: number;
  generated_at: string;
  read_only: boolean;
  gaps: ComplianceGapSummary[];
}

export interface ComplianceRiskResponse {
  tenant_id: number;
  generated_at: string;
  read_only: boolean;
  risks: ComplianceRiskSummary[];
}
