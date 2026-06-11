export interface QualityAccreditationBoundaryFlags {
  human_review_required: boolean;
  fake_metrics: boolean;
  fake_evidence: boolean;
  official_accreditation_approval_enabled: boolean;
  official_ministry_submission_enabled: boolean;
  official_ranking_claim_enabled: boolean;
  automatic_accreditation_decision_enabled: boolean;
  provider_integration_enabled: boolean;
  external_database_sync_enabled: boolean;
  hidden_score_present: boolean;
  autonomous_decision: boolean;
  incomplete_data: boolean;
  limitations: string[];
  source_capability_id?: string | null;
  source_family_id?: string | null;
}

export interface QualityAccreditationListResponse<T> {
  items: T[];
}

export interface QualityAccreditationRequestBase {
  status?: string | null;
  title?: string | null;
  description?: string | null;
  notes?: string | null;
  framework_ref?: string | null;
  policy_ref?: string | null;
  standard_ref?: string | null;
  criterion_ref?: string | null;
  requirement_ref?: string | null;
  evidence_ref?: string | null;
  limitation_ref?: string | null;
  readiness_ref?: string | null;
  report_ref?: string | null;
  section_ref?: string | null;
  plan_ref?: string | null;
  action_ref?: string | null;
  audit_ref?: string | null;
  finding_ref?: string | null;
  cycle_ref?: string | null;
  assessment_ref?: string | null;
  feedback_ref?: string | null;
  survey_ref?: string | null;
  review_ref?: string | null;
  response_plan_ref?: string | null;
  workflow_ref?: string | null;
  gap_ref?: string | null;
  calendar_ref?: string | null;
  risk_ref?: string | null;
  bridge_ref?: string | null;
  signal_ref?: string | null;
  source_entity_type?: string | null;
  source_entity_id?: number | null;
  source_entity_ref?: string | null;
  source_vertical_ref?: string | null;
  target_reference?: string | null;
  owner_ref?: string | null;
  reviewer_ref?: string | null;
  committee_ref?: string | null;
  program_ref?: string | null;
  department_ref?: string | null;
  faculty_ref?: string | null;
  student_group_ref?: string | null;
  event_type?: string | null;
  signal_type?: string | null;
  limitation_code?: string | null;
  limitation_text?: string | null;
  risk_band?: string | null;
  completion_percent?: number | null;
  reference_uri?: string | null;
  source_capability_id?: string | null;
  source_family_id?: string | null;
  read_only_first?: boolean | null;
  mutation_allowed?: boolean | null;
  limitations?: string[];
  metadata?: Record<string, unknown>;
}

export interface QualityAccreditationMetadataEntity extends QualityAccreditationBoundaryFlags {
  id: number;
  tenant_id: number;
  status: string;
  metadata: Record<string, unknown>;
  created_at: string | null;
  updated_at: string | null;
  archived_at: string | null;
  created_by_user_id?: string | null;
  updated_by_user_id?: string | null;
  title?: string | null;
  description?: string | null;
  notes?: string | null;
  framework_ref?: string | null;
  policy_ref?: string | null;
  standard_ref?: string | null;
  criterion_ref?: string | null;
  requirement_ref?: string | null;
  evidence_ref?: string | null;
  limitation_ref?: string | null;
  readiness_ref?: string | null;
  report_ref?: string | null;
  section_ref?: string | null;
  plan_ref?: string | null;
  action_ref?: string | null;
  audit_ref?: string | null;
  finding_ref?: string | null;
  cycle_ref?: string | null;
  assessment_ref?: string | null;
  feedback_ref?: string | null;
  survey_ref?: string | null;
  review_ref?: string | null;
  response_plan_ref?: string | null;
  workflow_ref?: string | null;
  gap_ref?: string | null;
  calendar_ref?: string | null;
  risk_ref?: string | null;
  bridge_ref?: string | null;
  signal_ref?: string | null;
  source_entity_type?: string | null;
  source_entity_id?: number | null;
  source_entity_ref?: string | null;
  source_vertical_ref?: string | null;
  target_reference?: string | null;
  owner_ref?: string | null;
  reviewer_ref?: string | null;
  committee_ref?: string | null;
  program_ref?: string | null;
  department_ref?: string | null;
  faculty_ref?: string | null;
  student_group_ref?: string | null;
  event_type?: string | null;
  signal_type?: string | null;
  limitation_code?: string | null;
  limitation_text?: string | null;
  risk_band?: string | null;
  completion_percent?: number | null;
  reference_uri?: string | null;
  fake_evidence: boolean;
  read_only_first: boolean;
  mutation_allowed: boolean;
}

export interface QualityAccreditationOverviewResponse {
  tenant_id: number;
  module: string;
  product_vertical: string;
  contract_version: string;
  runtime_mode: string;
  table_count: number;
  route_count: number;
  readiness_items: number;
  evidence_items: number;
  bridge_items: number;
  limitations: string[];
  boundary_summary: Record<string, boolean>;
}

export interface QualityAccreditationHealthResponse {
  tenant_id: number;
  module: string;
  target_level: string;
  foundation_status: string;
  runtime_mode: string;
  contract_version: string;
  provider_integration_enabled: boolean;
  external_database_sync_enabled: boolean;
  official_accreditation_approval_enabled: boolean;
  official_ministry_submission_enabled: boolean;
  official_ranking_claim_enabled: boolean;
  hidden_score_present: boolean;
  fake_metrics: boolean;
  incomplete_data: boolean;
  limitations: string[];
  route_count: number;
  table_count: number;
}

export interface QualityAccreditationRuntimeShellSection {
  owner_module: string;
  records: number;
  read_only: boolean;
  aggregator_only: boolean;
  source_modules: string[];
}

export interface QualityAccreditationRuntimeShellSafety {
  read_only: boolean;
  aggregator_only: boolean;
  human_review_required: boolean;
  provider_integration_enabled: boolean;
  official_accreditation_approval_enabled: boolean;
  official_ministry_submission_enabled: boolean;
  official_ranking_claim_enabled: boolean;
  hidden_score_present: boolean;
  limitations: string[];
}

export interface QualityAccreditationRuntimeShellResponse {
  tenant_id: number;
  owner_module: string;
  runtime_shell: string;
  runtime_mode: string;
  generated_at: string;
  read_only: boolean;
  aggregator_only: boolean;
  overview: QualityAccreditationRuntimeShellSection;
  readiness: QualityAccreditationRuntimeShellSection;
  evidence: QualityAccreditationRuntimeShellSection;
  risk: QualityAccreditationRuntimeShellSection;
  dashboard: QualityAccreditationRuntimeShellSection;
  safety: QualityAccreditationRuntimeShellSafety;
}

export interface AccreditationRegistryItem {
  accreditation_id: string;
  accreditation_name: string;
  accreditation_type: string;
  accreditation_scope: string;
  provider: string;
  status: string;
  issued_date: string;
  expiry_date: string;
  readiness_score: number;
  risk_level: string;
  read_only: boolean;
  aggregator_only: boolean;
}

export interface AccreditationProviderSummary {
  provider: string;
  accreditation_count: number;
  active_count: number;
  expiring_count: number;
  read_only: boolean;
  aggregator_only: boolean;
}

export interface AccreditationStatusSummary {
  status: string;
  accreditation_count: number;
  read_only: boolean;
  aggregator_only: boolean;
}

export interface AccreditationReadinessSummary {
  readiness_band: string;
  accreditation_count: number;
  average_readiness_score: number;
  read_only: boolean;
  aggregator_only: boolean;
}

export interface AccreditationRiskSummary {
  risk_level: string;
  accreditation_count: number;
  read_only: boolean;
  aggregator_only: boolean;
}

export interface AccreditationRegistryRuntimeResponse {
  tenant_id: number;
  owner_module: string;
  runtime_registry: string;
  runtime_mode: string;
  generated_at: string;
  read_only: boolean;
  aggregator_only: boolean;
  active_accreditations: AccreditationRegistryItem[];
  expiring_accreditations: AccreditationRegistryItem[];
  accreditation_provider: AccreditationProviderSummary[];
  accreditation_status: AccreditationStatusSummary[];
  accreditation_readiness: AccreditationReadinessSummary[];
  accreditation_risk: AccreditationRiskSummary[];
}

export type EvidenceCategory = string;
export type EvidenceStatus = string;

export interface AccreditationEvidenceItem {
  evidence_id: string;
  evidence_name: string;
  evidence_category: EvidenceCategory;
  accreditation_standard: string;
  accreditation_section: string;
  owner_unit: string;
  evidence_status: EvidenceStatus;
  completeness_score: number;
  last_updated: string;
  risk_level: string;
  read_only: boolean;
  aggregator_only: boolean;
}

export interface EvidenceCategorySummary {
  evidence_category: EvidenceCategory;
  evidence_count: number;
  average_completeness_score: number;
  read_only: boolean;
  aggregator_only: boolean;
}

export interface EvidenceReadinessSummary {
  readiness_band: string;
  evidence_count: number;
  read_only: boolean;
  aggregator_only: boolean;
}

export interface EvidenceCoverageSummary {
  coverage_scope: string;
  evidence_count: number;
  covered_count: number;
  coverage_percent: number;
  read_only: boolean;
  aggregator_only: boolean;
}

export interface EvidenceRiskSummary {
  risk_level: string;
  evidence_count: number;
  read_only: boolean;
  aggregator_only: boolean;
}

export interface AccreditationEvidenceRuntimeResponse {
  tenant_id: number;
  owner_module: string;
  runtime_registry: string;
  runtime_mode: string;
  generated_at: string;
  read_only: boolean;
  aggregator_only: boolean;
  evidence_inventory: AccreditationEvidenceItem[];
  evidence_categories: EvidenceCategorySummary[];
  evidence_readiness: EvidenceReadinessSummary[];
  evidence_coverage: EvidenceCoverageSummary[];
  evidence_risk: EvidenceRiskSummary[];
}

export type SelfAssessmentRiskLevel = 'LOW' | 'MEDIUM' | 'HIGH' | 'UNKNOWN';

export interface SelfAssessmentStandard {
  standard_id: string;
  standard_name: string;
  accreditation_framework: string;
  readiness_score: number;
  completion_percentage: number;
  evidence_coverage: number;
  gap_count: number;
  risk_level: SelfAssessmentRiskLevel;
  owner_unit: string;
  last_updated: string;
  read_only: boolean;
  aggregator_only: boolean;
}

export interface SelfAssessmentScorecard {
  standards_total: number;
  ready_standards: number;
  average_readiness_score: number;
  average_completion_percentage: number;
  average_evidence_coverage: number;
  high_risk_standards: number;
  gap_total: number;
  read_only: boolean;
  aggregator_only: boolean;
}

export interface SelfAssessmentReadinessSummary {
  readiness_band: string;
  standard_count: number;
  average_readiness_score: number;
  read_only: boolean;
  aggregator_only: boolean;
}

export interface SelfAssessmentCoverageSummary {
  coverage_scope: string;
  standard_count: number;
  average_evidence_coverage: number;
  read_only: boolean;
  aggregator_only: boolean;
}

export interface SelfAssessmentRiskSummary {
  risk_level: SelfAssessmentRiskLevel;
  standard_count: number;
  read_only: boolean;
  aggregator_only: boolean;
}

export interface SelfAssessmentRuntimeResponse {
  tenant_id: number;
  owner_module: string;
  runtime_registry: string;
  runtime_mode: string;
  generated_at: string;
  read_only: boolean;
  aggregator_only: boolean;
  standards: SelfAssessmentStandard[];
  scorecard: SelfAssessmentScorecard;
  readiness_summary: SelfAssessmentReadinessSummary[];
  coverage_summary: SelfAssessmentCoverageSummary[];
  risk_summary: SelfAssessmentRiskSummary[];
}

export type CorrectiveActionStatus = string;
export type CorrectiveActionRiskLevel = 'LOW' | 'MEDIUM' | 'HIGH' | 'UNKNOWN';

export interface CorrectiveActionItem {
  action_id: string;
  action_title: string;
  accreditation_standard: string;
  finding_reference: string;
  owner_unit: string;
  due_date: string;
  completion_percentage: number;
  status: CorrectiveActionStatus;
  readiness_score: number;
  risk_level: CorrectiveActionRiskLevel;
  overdue_flag: boolean;
  last_updated: string;
  read_only: boolean;
  aggregator_only: boolean;
}

export interface CorrectiveActionSummary {
  total_actions: number;
  completed_actions: number;
  in_progress_actions: number;
  overdue_actions: number;
  average_completion_percentage: number;
  read_only: boolean;
  aggregator_only: boolean;
}

export interface CorrectiveActionReadinessSummary {
  readiness_band: string;
  action_count: number;
  average_readiness_score: number;
  read_only: boolean;
  aggregator_only: boolean;
}

export interface CorrectiveActionRiskSummary {
  risk_level: CorrectiveActionRiskLevel;
  action_count: number;
  read_only: boolean;
  aggregator_only: boolean;
}

export interface CorrectiveActionOverdueSummary {
  overdue_state: string;
  action_count: number;
  read_only: boolean;
  aggregator_only: boolean;
}

export interface CorrectiveActionRuntimeResponse {
  tenant_id: number;
  owner_module: string;
  runtime_registry: string;
  runtime_mode: string;
  generated_at: string;
  read_only: boolean;
  aggregator_only: boolean;
  corrective_actions: CorrectiveActionItem[];
  action_summary: CorrectiveActionSummary;
  readiness_summary: CorrectiveActionReadinessSummary[];
  risk_summary: CorrectiveActionRiskSummary[];
  overdue_summary: CorrectiveActionOverdueSummary[];
}

export interface ImprovementMilestone {
  milestone_id: string;
  milestone_title: string;
  due_date: string;
  completion_percentage: number;
  status: string;
  read_only: boolean;
  aggregator_only: boolean;
}

export interface ImprovementKpiTarget {
  kpi_target_id: string;
  kpi_name: string;
  baseline_value: number;
  target_value: number;
  current_value: number;
  unit: string;
  read_only: boolean;
  aggregator_only: boolean;
}

export interface ImprovementInitiative {
  initiative_id: string;
  initiative_title: string;
  strategic_theme: string;
  owner_unit: string;
  status: string;
  completion_percentage: number;
  milestones: ImprovementMilestone[];
  kpi_targets: ImprovementKpiTarget[];
  read_only: boolean;
  aggregator_only: boolean;
}

export interface ImprovementRoadmap {
  roadmap_id: string;
  roadmap_title: string;
  accreditation_cycle: string;
  phase: string;
  initiatives_total: number;
  initiatives_completed: number;
  completion_percentage: number;
  read_only: boolean;
  aggregator_only: boolean;
}

export interface ImprovementForecast {
  forecast_id: string;
  forecast_type: string;
  confidence_level: string;
  projected_completion_date: string;
  readiness_forecast_score: number;
  risk_level: string;
  read_only: boolean;
  aggregator_only: boolean;
}

export interface ImprovementPlanRuntime {
  plan_id: string;
  plan_title: string;
  accreditation_standard: string;
  owner_unit: string;
  progress_tracking_status: string;
  completion_percentage: number;
  initiatives: ImprovementInitiative[];
  roadmaps: ImprovementRoadmap[];
  forecasts: ImprovementForecast[];
  last_updated: string;
  read_only: boolean;
  aggregator_only: boolean;
}

export interface ImprovementPlanRuntimeResponse {
  tenant_id: number;
  owner_module: string;
  runtime_registry: string;
  runtime_mode: string;
  generated_at: string;
  read_only: boolean;
  aggregator_only: boolean;
  improvement_plans: ImprovementPlanRuntime[];
}

export interface AuditFinding {
  finding_id: string;
  finding_source: string;
  finding_type: string;
  finding_title: string;
  severity: string;
  impacted_standard: string;
  remediation_status: string;
  closure_tracking_status: string;
  opened_at: string;
  due_date: string;
  read_only: boolean;
  aggregator_only: boolean;
}

export interface NonConformity {
  non_conformity_id: string;
  category: string;
  severity: string;
  affected_area: string;
  status: string;
  read_only: boolean;
  aggregator_only: boolean;
}

export interface AuditObservation {
  observation_id: string;
  observation_type: string;
  summary: string;
  impact_level: string;
  read_only: boolean;
  aggregator_only: boolean;
}

export interface AuditRecommendation {
  recommendation_id: string;
  recommendation_title: string;
  priority: string;
  owner_unit: string;
  target_date: string;
  status: string;
  read_only: boolean;
  aggregator_only: boolean;
}

export interface AuditRiskAnalysis {
  risk_band: string;
  findings_count: number;
  non_conformities_count: number;
  recommendations_open: number;
  read_only: boolean;
  aggregator_only: boolean;
}

export interface AuditRemediationStatus {
  remediation_state: string;
  findings_count: number;
  average_completion_percentage: number;
  read_only: boolean;
  aggregator_only: boolean;
}

export interface AuditReadiness {
  indicator_name: string;
  indicator_value: number;
  threshold: number;
  status: string;
  read_only: boolean;
  aggregator_only: boolean;
}

export interface AuditFindingRuntime {
  tenant_id: number;
  owner_module: string;
  runtime_registry: string;
  runtime_mode: string;
  generated_at: string;
  read_only: boolean;
  aggregator_only: boolean;
  findings: AuditFinding[];
  non_conformities: NonConformity[];
  observations: AuditObservation[];
  recommendations: AuditRecommendation[];
  risk_severity_analysis: AuditRiskAnalysis[];
  remediation_status: AuditRemediationStatus[];
  audit_readiness_indicators: AuditReadiness[];
}

export interface ReadinessMonitoringSummary {
  monitored_domains_total: number;
  domains_on_track: number;
  domains_at_risk: number;
  average_readiness_score: number;
  read_only: boolean;
  aggregator_only: boolean;
}

export interface ReadinessMonitoringDomain {
  domain_id: string;
  domain_name: string;
  readiness_score: number;
  threshold: number;
  status: string;
  trend: string;
  read_only: boolean;
  aggregator_only: boolean;
}

export interface ReadinessMonitoringRisk {
  risk_id: string;
  risk_title: string;
  risk_level: string;
  impacted_domain: string;
  mitigation_status: string;
  read_only: boolean;
  aggregator_only: boolean;
}

export interface ReadinessMonitoringRemediation {
  remediation_id: string;
  remediation_title: string;
  owner_unit: string;
  completion_percentage: number;
  status: string;
  due_date: string;
  read_only: boolean;
  aggregator_only: boolean;
}

export interface ReadinessMonitoringIndicator {
  indicator_name: string;
  indicator_value: number;
  threshold: number;
  status: string;
  read_only: boolean;
  aggregator_only: boolean;
}

export interface ReadinessMonitoringRuntime {
  tenant_id: number;
  owner_module: string;
  runtime_registry: string;
  runtime_mode: string;
  generated_at: string;
  read_only: boolean;
  aggregator_only: boolean;
  readiness_summary: ReadinessMonitoringSummary;
  readiness_domains: ReadinessMonitoringDomain[];
  readiness_risks: ReadinessMonitoringRisk[];
  remediation_tracking: ReadinessMonitoringRemediation[];
  readiness_indicators: ReadinessMonitoringIndicator[];
}

export interface QualityAccreditationDashboardResponse extends QualityAccreditationBoundaryFlags {
  tenant_id: number;
  generated_at: string | null;
  contract_version: string;
  source_spec_commit: string;
  source_product_map_commit: string;
  source_vertical_selection_commit: string;
  master_matrix_commit: string;
  master_matrix_rows: number;
  detailed_capability_count: number;
  capability_family_count: number;
  data_source: string;
  frameworks_summary: Record<string, number>;
  standards_summary: Record<string, number>;
  evidence_summary: Record<string, number>;
  readiness_summary: Record<string, number>;
  self_assessment_summary: Record<string, number>;
  improvement_summary: Record<string, number>;
  audit_summary: Record<string, number>;
  program_review_summary: Record<string, number>;
  bridge_summary: Record<string, number>;
  brain_signal_summary: Record<string, number>;
  boundary_summary: Record<string, boolean>;
}

export interface QualityAccreditationMatrixSummaryResponse {
  contract_version: string;
  source_spec_commit: string;
  source_product_map_commit: string;
  source_vertical_selection_commit: string;
  master_matrix_commit: string;
  master_matrix_rows: number;
  detailed_capability_count: number;
  capability_family_count: number;
  runtime_mode: string;
  route_count_expected: string;
  table_count_expected: number;
  permission_count_expected: number;
}

export interface QualityAccreditationLimitationsResponse {
  items: string[];
}

export interface QualityFramework extends QualityAccreditationMetadataEntity {
  framework_ref?: string | null;
}

export interface QualityPolicyRegistryItem extends QualityAccreditationMetadataEntity {
  policy_ref?: string | null;
}

export interface AccreditationStandard extends QualityAccreditationMetadataEntity {
  standard_ref?: string | null;
}

export interface StandardCriterion extends QualityAccreditationMetadataEntity {
  criterion_ref?: string | null;
}

export interface StandardsEvidenceRequirement extends QualityAccreditationMetadataEntity {
  requirement_ref?: string | null;
}

export interface QualityEvidence extends QualityAccreditationMetadataEntity {
  evidence_ref?: string | null;
}

export interface QualityEvidenceReview extends QualityAccreditationMetadataEntity {
  review_ref?: string | null;
}

export interface EvidenceLimitation extends QualityAccreditationMetadataEntity {
  limitation_ref?: string | null;
}

export interface ProgramReadiness extends QualityAccreditationMetadataEntity {
  readiness_ref?: string | null;
}

export interface InstitutionalReadiness extends QualityAccreditationMetadataEntity {
  readiness_ref?: string | null;
}

export interface SelfAssessmentReport extends QualityAccreditationMetadataEntity {
  report_ref?: string | null;
}

export interface SelfAssessmentSection extends QualityAccreditationMetadataEntity {
  section_ref?: string | null;
}

export interface QualityImprovementPlan extends QualityAccreditationMetadataEntity {
  plan_ref?: string | null;
}

export interface QualityImprovementAction extends QualityAccreditationMetadataEntity {
  action_ref?: string | null;
}

export interface InternalQualityAudit extends QualityAccreditationMetadataEntity {
  audit_ref?: string | null;
}

export interface QualityAuditFinding extends QualityAccreditationMetadataEntity {
  finding_ref?: string | null;
}

export interface ProgramReviewCycle extends QualityAccreditationMetadataEntity {
  cycle_ref?: string | null;
}

export interface LearningOutcomesAssessment extends QualityAccreditationMetadataEntity {
  assessment_ref?: string | null;
}

export interface StakeholderFeedbackMetadata extends QualityAccreditationMetadataEntity {
  feedback_ref?: string | null;
}

export interface SurveyQualityMetadata extends QualityAccreditationMetadataEntity {
  survey_ref?: string | null;
}

export interface ExternalExpertReview extends QualityAccreditationMetadataEntity {
  review_ref?: string | null;
}

export interface ExpertRecommendationResponsePlan extends QualityAccreditationMetadataEntity {
  response_plan_ref?: string | null;
}

export interface AccreditationCommitteeWorkflow extends QualityAccreditationMetadataEntity {
  workflow_ref?: string | null;
}

export interface ComplianceGapAnalysis extends QualityAccreditationMetadataEntity {
  gap_ref?: string | null;
}

export interface AccreditationCalendarItem extends QualityAccreditationMetadataEntity {
  calendar_ref?: string | null;
}

export interface QualityRisk extends QualityAccreditationMetadataEntity {
  risk_ref?: string | null;
}

export interface QualityBridge extends QualityAccreditationMetadataEntity {
  bridge_ref?: string | null;
}

export interface QualityBrainSignal extends QualityAccreditationMetadataEntity {
  signal_ref?: string | null;
}

export interface QualityAuditEvent {
  id: number;
  tenant_id: number;
  event_type: string;
  source_entity_type: string;
  source_entity_id?: number | null;
  actor_user_id?: string | null;
  previous_status?: string | null;
  new_status?: string | null;
  payload: Record<string, unknown>;
  created_at: string | null;
  human_review_required: boolean;
  provider_integration_enabled: boolean;
  hidden_score_present: boolean;
}

export interface QualityStatusHistory {
  id: number;
  tenant_id: number;
  source_entity_type: string;
  source_entity_id?: number | null;
  previous_status?: string | null;
  new_status: string;
  changed_by_user_id?: string | null;
  created_at: string | null;
  metadata: Record<string, unknown>;
}

export interface QualityFrameworkCreatePayload extends QualityAccreditationRequestBase {}
export interface QualityFrameworkUpdatePayload extends QualityAccreditationRequestBase {}
export interface AccreditationStandardCreatePayload extends QualityAccreditationRequestBase {}
export interface AccreditationStandardUpdatePayload extends QualityAccreditationRequestBase {}
export interface StandardCriterionCreatePayload extends QualityAccreditationRequestBase {}
export interface StandardCriterionUpdatePayload extends QualityAccreditationRequestBase {}
export interface StandardsEvidenceRequirementCreatePayload extends QualityAccreditationRequestBase {}
export interface QualityEvidenceCreatePayload extends QualityAccreditationRequestBase {}
export interface QualityEvidenceReviewPayload extends QualityAccreditationRequestBase {}
export interface EvidenceLimitationCreatePayload extends QualityAccreditationRequestBase {}
export interface ProgramReadinessCreatePayload extends QualityAccreditationRequestBase {}
export interface ProgramReadinessUpdatePayload extends QualityAccreditationRequestBase {}
export interface InstitutionalReadinessCreatePayload extends QualityAccreditationRequestBase {}
export interface InstitutionalReadinessUpdatePayload extends QualityAccreditationRequestBase {}
export interface SelfAssessmentReportCreatePayload extends QualityAccreditationRequestBase {}
export interface SelfAssessmentReportUpdatePayload extends QualityAccreditationRequestBase {}
export interface SelfAssessmentSectionCreatePayload extends QualityAccreditationRequestBase {}
export interface SelfAssessmentSectionUpdatePayload extends QualityAccreditationRequestBase {}
export interface QualityImprovementPlanCreatePayload extends QualityAccreditationRequestBase {}
export interface QualityImprovementPlanUpdatePayload extends QualityAccreditationRequestBase {}
export interface QualityImprovementActionCreatePayload extends QualityAccreditationRequestBase {}
export interface QualityImprovementActionUpdatePayload extends QualityAccreditationRequestBase {}
export interface InternalQualityAuditCreatePayload extends QualityAccreditationRequestBase {}
export interface InternalQualityAuditUpdatePayload extends QualityAccreditationRequestBase {}
export interface QualityAuditFindingCreatePayload extends QualityAccreditationRequestBase {}
export interface QualityAuditFindingUpdatePayload extends QualityAccreditationRequestBase {}
export interface ProgramReviewCycleCreatePayload extends QualityAccreditationRequestBase {}
export interface ProgramReviewCycleUpdatePayload extends QualityAccreditationRequestBase {}
export interface LearningOutcomesAssessmentCreatePayload extends QualityAccreditationRequestBase {}
export interface LearningOutcomesAssessmentUpdatePayload extends QualityAccreditationRequestBase {}
export interface StakeholderFeedbackMetadataCreatePayload extends QualityAccreditationRequestBase {}
export interface SurveyQualityMetadataCreatePayload extends QualityAccreditationRequestBase {}
export interface AccreditationCommitteeWorkflowCreatePayload extends QualityAccreditationRequestBase {}
export interface AccreditationCommitteeWorkflowUpdatePayload extends QualityAccreditationRequestBase {}
export interface ExternalExpertReviewCreatePayload extends QualityAccreditationRequestBase {}
export interface ExternalExpertReviewUpdatePayload extends QualityAccreditationRequestBase {}
export interface ExpertRecommendationResponsePlanCreatePayload extends QualityAccreditationRequestBase {}
export interface ComplianceGapAnalysisCreatePayload extends QualityAccreditationRequestBase {}
export interface ComplianceGapAnalysisUpdatePayload extends QualityAccreditationRequestBase {}
export interface AccreditationCalendarCreatePayload extends QualityAccreditationRequestBase {}
export interface AccreditationCalendarUpdatePayload extends QualityAccreditationRequestBase {}
export interface QualityRiskCreatePayload extends QualityAccreditationRequestBase {}
export interface QualityRiskUpdatePayload extends QualityAccreditationRequestBase {}
export interface QualityBridgeCreatePayload extends QualityAccreditationRequestBase {}
export interface QualityBrainSignalCreatePayload extends QualityAccreditationRequestBase {}