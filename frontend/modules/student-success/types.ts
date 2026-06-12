export interface StudentSuccessRuntimeShellSection {
  owner_module: string;
  records: number;
  read_only: boolean;
  aggregator_only: boolean;
  source_modules: string[];
}

export interface StudentSuccessRuntimeShellSafety {
  read_only: boolean;
  aggregator_only: boolean;
  tenant_aware: boolean;
  summary_read_required: boolean;
  workflow_execution_enabled: boolean;
  provider_mutation_enabled: boolean;
  limitations: string[];
}

export interface StudentSuccessRuntimeShellResponse {
  tenant_id: number;
  owner_module: string;
  runtime_shell: string;
  runtime_mode: string;
  generated_at: string;
  read_only: boolean;
  aggregator_only: boolean;
  student_success_overview: StudentSuccessRuntimeShellSection;
  lifecycle_summary: StudentSuccessRuntimeShellSection;
  retention_summary: StudentSuccessRuntimeShellSection;
  risk_summary: StudentSuccessRuntimeShellSection;
  intervention_summary: StudentSuccessRuntimeShellSection;
  advisor_summary: StudentSuccessRuntimeShellSection;
  signal_summary: StudentSuccessRuntimeShellSection;
  dashboard_summary: StudentSuccessRuntimeShellSection;
  safety: StudentSuccessRuntimeShellSafety;
}

export interface StudentRegistryRuntimeSection {
  owner_module: string;
  records: number;
  read_only: boolean;
  aggregator_only: boolean;
  source_modules: string[];
}

export interface StudentRegistryRuntimeSafety {
  read_only: boolean;
  aggregator_only: boolean;
  tenant_aware: boolean;
  summary_read_required: boolean;
  write_operations_enabled: boolean;
  workflow_execution_enabled: boolean;
  approval_execution_enabled: boolean;
  background_jobs_enabled: boolean;
  provider_mutation_enabled: boolean;
  outbound_calls_enabled: boolean;
  limitations: string[];
}

export interface StudentRegistryRuntimeResponse {
  tenant_id: number;
  owner_module: string;
  runtime_surface: string;
  runtime_mode: string;
  generated_at: string;
  read_only: boolean;
  aggregator_only: boolean;
  student_registry_summary: StudentRegistryRuntimeSection;
  enrollment_summary: StudentRegistryRuntimeSection;
  academic_standing_summary: StudentRegistryRuntimeSection;
  retention_link_summary: StudentRegistryRuntimeSection;
  advisor_link_summary: StudentRegistryRuntimeSection;
  risk_link_summary: StudentRegistryRuntimeSection;
  lifecycle_status_summary: StudentRegistryRuntimeSection;
  safety: StudentRegistryRuntimeSafety;
}

export interface RetentionSummary {
  owner_module: string;
  records: number;
  read_only: boolean;
  aggregator_only: boolean;
  source_modules: string[];
}

export interface RetentionRiskSummary {
  owner_module: string;
  records: number;
  read_only: boolean;
  aggregator_only: boolean;
  source_modules: string[];
}

export interface RetentionTrendSummary {
  owner_module: string;
  records: number;
  read_only: boolean;
  aggregator_only: boolean;
  source_modules: string[];
}

export interface CohortRetentionSummary {
  owner_module: string;
  records: number;
  read_only: boolean;
  aggregator_only: boolean;
  source_modules: string[];
}

export interface StudentRetentionRuntimeSafety {
  read_only: boolean;
  aggregator_only: boolean;
  tenant_aware: boolean;
  summary_read_required: boolean;
  write_operations_enabled: boolean;
  workflow_execution_enabled: boolean;
  approval_execution_enabled: boolean;
  background_jobs_enabled: boolean;
  outbound_providers_enabled: boolean;
  external_integrations_enabled: boolean;
  limitations: string[];
}

export interface StudentRetentionRuntime {
  tenant_id: number;
  owner_module: string;
  runtime_surface: string;
  runtime_mode: string;
  generated_at: string;
  read_only: boolean;
  aggregator_only: boolean;
  retention_summary: RetentionSummary;
  retention_score_distribution: RetentionSummary;
  retention_risk_distribution: RetentionRiskSummary;
  dropout_risk_summary: RetentionRiskSummary;
  persistence_summary: RetentionSummary;
  retention_trend_summary: RetentionTrendSummary;
  cohort_retention_summary: CohortRetentionSummary;
  retention_signal_summary: RetentionSummary;
  safety: StudentRetentionRuntimeSafety;
}

export interface StudentAcademicRiskRuntimeSection {
  owner_module: string;
  records: number;
  read_only: boolean;
  aggregator_only: boolean;
  source_modules: string[];
}

export interface StudentAcademicRiskRuntimeSafety {
  read_only: boolean;
  aggregator_only: boolean;
  tenant_aware: boolean;
  summary_read_required: boolean;
  write_operations_enabled: boolean;
  workflow_execution_enabled: boolean;
  approval_execution_enabled: boolean;
  background_jobs_enabled: boolean;
  provider_mutation_enabled: boolean;
  outbound_integrations_enabled: boolean;
  limitations: string[];
}

export interface StudentAcademicRiskRuntime {
  tenant_id: number;
  owner_module: string;
  runtime_surface: string;
  runtime_mode: string;
  generated_at: string;
  read_only: boolean;
  aggregator_only: boolean;
  academic_risk_summary: StudentAcademicRiskRuntimeSection;
  gpa_risk_distribution: StudentAcademicRiskRuntimeSection;
  failed_course_risk_summary: StudentAcademicRiskRuntimeSection;
  low_performance_summary: StudentAcademicRiskRuntimeSection;
  probation_summary: StudentAcademicRiskRuntimeSection;
  progression_risk_summary: StudentAcademicRiskRuntimeSection;
  academic_alert_summary: StudentAcademicRiskRuntimeSection;
  academic_signal_summary: StudentAcademicRiskRuntimeSection;
  safety: StudentAcademicRiskRuntimeSafety;
}

export interface StudentAttendanceRiskRuntimeSection {
  owner_module: string;
  records: number;
  read_only: boolean;
  aggregator_only: boolean;
  source_modules: string[];
}

export interface StudentAttendanceRiskRuntimeSafety {
  read_only: boolean;
  aggregator_only: boolean;
  tenant_aware: boolean;
  summary_read_required: boolean;
  write_operations_enabled: boolean;
  workflow_execution_enabled: boolean;
  approval_execution_enabled: boolean;
  background_jobs_enabled: boolean;
  provider_mutation_enabled: boolean;
  outbound_integrations_enabled: boolean;
  limitations: string[];
}

export interface StudentAttendanceRiskRuntime {
  tenant_id: number;
  owner_module: string;
  runtime_surface: string;
  runtime_mode: string;
  generated_at: string;
  read_only: boolean;
  aggregator_only: boolean;
  attendance_risk_summary: StudentAttendanceRiskRuntimeSection;
  absence_distribution: StudentAttendanceRiskRuntimeSection;
  chronic_absence_summary: StudentAttendanceRiskRuntimeSection;
  missed_class_summary: StudentAttendanceRiskRuntimeSection;
  attendance_trend_summary: StudentAttendanceRiskRuntimeSection;
  punctuality_summary: StudentAttendanceRiskRuntimeSection;
  engagement_attendance_summary: StudentAttendanceRiskRuntimeSection;
  attendance_signal_summary: StudentAttendanceRiskRuntimeSection;
  safety: StudentAttendanceRiskRuntimeSafety;
}

export interface StudentInterventionRuntimeSection {
  owner_module: string;
  records: number;
  read_only: boolean;
  aggregator_only: boolean;
  source_modules: string[];
}

export interface StudentInterventionRuntimeSafety {
  read_only: boolean;
  aggregator_only: boolean;
  tenant_aware: boolean;
  summary_read_required: boolean;
  write_operations_enabled: boolean;
  workflow_execution_enabled: boolean;
  approval_execution_enabled: boolean;
  background_jobs_enabled: boolean;
  notification_execution_enabled: boolean;
  provider_mutation_enabled: boolean;
  outbound_integrations_enabled: boolean;
  intervention_execution_enabled: boolean;
  limitations: string[];
}

export interface StudentInterventionRuntime {
  tenant_id: number;
  owner_module: string;
  runtime_surface: string;
  runtime_mode: string;
  generated_at: string;
  read_only: boolean;
  aggregator_only: boolean;
  intervention_summary: StudentInterventionRuntimeSection;
  intervention_priority_groups: StudentInterventionRuntimeSection;
  intervention_recommendations: StudentInterventionRuntimeSection;
  advisor_interventions: StudentInterventionRuntimeSection;
  dean_interventions: StudentInterventionRuntimeSection;
  support_programs: StudentInterventionRuntimeSection;
  intervention_effectiveness_signals: StudentInterventionRuntimeSection;
  intervention_signal_summary: StudentInterventionRuntimeSection;
  safety: StudentInterventionRuntimeSafety;
}

export interface StudentAdvisorRuntimeSection {
  owner_module: string;
  records: number;
  read_only: boolean;
  aggregator_only: boolean;
  source_modules: string[];
}

export interface StudentAdvisorRuntimeSafety {
  read_only: boolean;
  aggregator_only: boolean;
  tenant_aware: boolean;
  summary_read_required: boolean;
  write_operations_enabled: boolean;
  intervention_execution_enabled: boolean;
  workflow_execution_enabled: boolean;
  approval_execution_enabled: boolean;
  background_jobs_enabled: boolean;
  notification_execution_enabled: boolean;
  provider_mutation_enabled: boolean;
  outbound_integrations_enabled: boolean;
  scheduling_engine_enabled: boolean;
  limitations: string[];
}

export interface StudentAdvisorRuntime {
  tenant_id: number;
  owner_module: string;
  runtime_surface: string;
  runtime_mode: string;
  generated_at: string;
  read_only: boolean;
  aggregator_only: boolean;
  advisor_summary: StudentAdvisorRuntimeSection;
  advisor_workload_distribution: StudentAdvisorRuntimeSection;
  advisor_student_assignments: StudentAdvisorRuntimeSection;
  advisor_intervention_queue: StudentAdvisorRuntimeSection;
  advisor_follow_up_summary: StudentAdvisorRuntimeSection;
  advisor_risk_coverage: StudentAdvisorRuntimeSection;
  advisor_effectiveness_summary: StudentAdvisorRuntimeSection;
  advisor_signal_summary: StudentAdvisorRuntimeSection;
  safety: StudentAdvisorRuntimeSafety;
}

export interface StudentSuccessSignalsRuntimeSection {
  owner_module: string;
  records: number;
  read_only: boolean;
  aggregator_only: boolean;
  source_modules: string[];
}

export interface StudentSuccessSignalsRuntimeSafety {
  read_only: boolean;
  aggregator_only: boolean;
  tenant_aware: boolean;
  summary_read_required: boolean;
  write_operations_enabled: boolean;
  workflow_execution_enabled: boolean;
  approval_execution_enabled: boolean;
  background_jobs_enabled: boolean;
  notification_execution_enabled: boolean;
  provider_mutation_enabled: boolean;
  outbound_integrations_enabled: boolean;
  scheduling_engine_enabled: boolean;
  signal_execution_engine_enabled: boolean;
  persistence_enabled: boolean;
  limitations: string[];
}

export interface StudentSuccessSignalsRuntime {
  tenant_id: number;
  owner_module: string;
  runtime_surface: string;
  runtime_mode: string;
  generated_at: string;
  read_only: boolean;
  aggregator_only: boolean;
  success_signal_summary: StudentSuccessSignalsRuntimeSection;
  retention_signals: StudentSuccessSignalsRuntimeSection;
  academic_signals: StudentSuccessSignalsRuntimeSection;
  attendance_signals: StudentSuccessSignalsRuntimeSection;
  intervention_signals: StudentSuccessSignalsRuntimeSection;
  advisor_signals: StudentSuccessSignalsRuntimeSection;
  early_warning_signals: StudentSuccessSignalsRuntimeSection;
  success_indicator_signals: StudentSuccessSignalsRuntimeSection;
  signal_trend_summary: StudentSuccessSignalsRuntimeSection;
  signal_scorecard: StudentSuccessSignalsRuntimeSection;
  safety: StudentSuccessSignalsRuntimeSafety;
}

export interface StudentSuccessDashboardRuntimeSection {
  owner_module: string;
  records: number;
  read_only: boolean;
  aggregator_only: boolean;
  source_modules: string[];
}

export interface StudentSuccessDashboardRuntimeSafety {
  read_only: boolean;
  aggregator_only: boolean;
  tenant_aware: boolean;
  summary_read_required: boolean;
  write_operations_enabled: boolean;
  workflow_execution_enabled: boolean;
  approval_execution_enabled: boolean;
  background_jobs_enabled: boolean;
  notification_execution_enabled: boolean;
  provider_mutation_enabled: boolean;
  outbound_integrations_enabled: boolean;
  scheduling_engine_enabled: boolean;
  persistence_enabled: boolean;
  limitations: string[];
}

export interface StudentSuccessDashboardRuntime {
  tenant_id: number;
  owner_module: string;
  runtime_surface: string;
  runtime_mode: string;
  generated_at: string;
  read_only: boolean;
  aggregator_only: boolean;
  executive_summary: StudentSuccessDashboardRuntimeSection;
  student_population: StudentSuccessDashboardRuntimeSection;
  retention_overview: StudentSuccessDashboardRuntimeSection;
  academic_risk_overview: StudentSuccessDashboardRuntimeSection;
  attendance_risk_overview: StudentSuccessDashboardRuntimeSection;
  intervention_overview: StudentSuccessDashboardRuntimeSection;
  advisor_overview: StudentSuccessDashboardRuntimeSection;
  success_signals: StudentSuccessDashboardRuntimeSection;
  priority_actions: StudentSuccessDashboardRuntimeSection;
  dashboard_kpis: StudentSuccessDashboardRuntimeSection;
  safety: StudentSuccessDashboardRuntimeSafety;
}
