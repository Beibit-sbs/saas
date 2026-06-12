export type AcademicOperationsRuntimeShellSection = {
  owner_module: string;
  records: number;
  read_only: boolean;
  aggregator_only: boolean;
  source_modules: string[];
};

export type AcademicOperationsRuntimeShellSafety = {
  read_only: boolean;
  aggregator_only: boolean;
  tenant_aware: boolean;
  summary_read_required: boolean;
  workflow_execution_enabled: boolean;
  approval_execution_enabled: boolean;
  background_jobs_enabled: boolean;
  provider_mutation_enabled: boolean;
  limitations: string[];
};

export type AcademicOperationsRuntimeShellResponse = {
  tenant_id: number;
  owner_module: string;
  runtime_shell: string;
  runtime_mode: string;
  generated_at: string;
  read_only: boolean;
  aggregator_only: boolean;
  runtime_shell_summary: AcademicOperationsRuntimeShellSection;
  runtime_shell_domain: AcademicOperationsRuntimeShellSection;
  runtime_shell_runtime: AcademicOperationsRuntimeShellSection;
  runtime_shell_integration: AcademicOperationsRuntimeShellSection;
  runtime_shell_readiness: AcademicOperationsRuntimeShellSection;
  safety: AcademicOperationsRuntimeShellSafety;
};

export type AcademicRegistryRuntimeSection = {
  owner_module: string;
  records: number;
  read_only: boolean;
  aggregator_only: boolean;
  source_modules: string[];
};

export type AcademicRegistryRuntimeOverview = {
  owner_module: string;
  runtime_scope: string;
  generated_at: string;
  read_only: boolean;
  aggregator_only: boolean;
};

export type AcademicRegistryRuntimeStatistics = {
  academic_periods_total: number;
  academic_groups_total: number;
  curriculum_registry_total: number;
  course_catalog_linkage_total: number;
  student_registry_linkage_total: number;
  canonical_bridge_total: number;
};

export type AcademicRegistryRuntimeIntegrationStatus = {
  provider: string;
  status: string;
  integration_mode: string;
  ready: boolean;
  evidence_count: number;
  read_only: boolean;
};

export type AcademicRegistryRuntimeHealth = {
  healthy: boolean;
  consistency_score: number;
  issues: string[];
};

export type AcademicRegistryRuntimeReadiness = {
  ready_for_runtime: boolean;
  checklist: string[];
  readiness_score: number;
};

export type AcademicRegistryRuntimeResponse = {
  tenant_id: number;
  overview: AcademicRegistryRuntimeOverview;
  registry_statistics: AcademicRegistryRuntimeStatistics;
  academic_periods: AcademicRegistryRuntimeSection;
  academic_groups: AcademicRegistryRuntimeSection;
  curriculum_linkage: AcademicRegistryRuntimeSection;
  catalog_linkage: AcademicRegistryRuntimeSection;
  sis_status: AcademicRegistryRuntimeIntegrationStatus;
  lms_status: AcademicRegistryRuntimeIntegrationStatus;
  health: AcademicRegistryRuntimeHealth;
  readiness: AcademicRegistryRuntimeReadiness;
};

export type CurriculumRuntimeSection = {
  owner_module: string;
  records: number;
  read_only: boolean;
  aggregator_only: boolean;
  source_modules: string[];
};

export type CurriculumRuntimeOverview = {
  owner_module: string;
  runtime_scope: string;
  generated_at: string;
  read_only: boolean;
  aggregator_only: boolean;
};

export type CurriculumRuntimeStatistics = {
  program_structures_total: number;
  curriculum_versions_total: number;
  curriculum_health_score: number;
  course_catalog_linkage_total: number;
  prerequisite_chains_total: number;
  learning_outcomes_total: number;
  academic_plans_total: number;
  canonical_bridge_total: number;
};

export type CurriculumRuntimeHealth = {
  healthy: boolean;
  consistency_score: number;
  issues: string[];
};

export type CurriculumRuntimeRisks = {
  risk_score: number;
  open_risks: number;
  indicators: string[];
};

export type CurriculumRuntimeReadiness = {
  ready_for_runtime: boolean;
  checklist: string[];
  readiness_score: number;
};

export type CurriculumRuntimeResponse = {
  tenant_id: number;
  overview: CurriculumRuntimeOverview;
  curriculum_statistics: CurriculumRuntimeStatistics;
  program_structures: CurriculumRuntimeSection;
  curriculum_versions: CurriculumRuntimeSection;
  curriculum_health: CurriculumRuntimeHealth;
  course_catalog_linkage: CurriculumRuntimeSection;
  prerequisite_chains: CurriculumRuntimeSection;
  learning_outcomes_summary: CurriculumRuntimeSection;
  curriculum_risks: CurriculumRuntimeRisks;
  curriculum_readiness: CurriculumRuntimeReadiness;
};

export type TimetableRuntimeOverview = {
  owner_module: string;
  runtime_scope: string;
  generated_at: string;
  read_only: boolean;
  aggregator_only: boolean;
};

export type TimetableRuntimeStatistics = {
  course_sections_total: number;
  schedules_total: number;
  calendar_periods_total: number;
  rooms_total: number;
  instructors_total: number;
  students_total: number;
  conflicts_total: number;
  capacity_alerts_total: number;
  canonical_bridge_total: number;
};

export type TimetableRuntimeSection = {
  owner_module: string;
  records: number;
  read_only: boolean;
  aggregator_only: boolean;
  source_modules: string[];
};

export type TimetableRoomUtilization = {
  records: number;
  utilization_rate: number;
  underutilized_rooms: number;
  overloaded_rooms: number;
  read_only: boolean;
};

export type TimetableInstructorAllocation = {
  records: number;
  assigned_instructors: number;
  unassigned_sections: number;
  read_only: boolean;
};

export type TimetableScheduleConflicts = {
  records: number;
  conflict_rate: number;
  critical_conflicts: number;
  read_only: boolean;
};

export type TimetableCapacityIndicators = {
  records: number;
  over_capacity_sections: number;
  under_capacity_sections: number;
  read_only: boolean;
};

export type TimetableRuntimeHealth = {
  healthy: boolean;
  consistency_score: number;
  issues: string[];
};

export type TimetableRuntimeReadiness = {
  ready_for_runtime: boolean;
  checklist: string[];
  readiness_score: number;
};

export type TimetableRuntimeResponse = {
  tenant_id: number;
  overview: TimetableRuntimeOverview;
  timetable_statistics: TimetableRuntimeStatistics;
  academic_calendar_summary: TimetableRuntimeSection;
  room_utilization: TimetableRoomUtilization;
  instructor_allocation: TimetableInstructorAllocation;
  student_schedule_summary: TimetableRuntimeSection;
  schedule_conflicts: TimetableScheduleConflicts;
  capacity_indicators: TimetableCapacityIndicators;
  timetable_health: TimetableRuntimeHealth;
  timetable_readiness: TimetableRuntimeReadiness;
};
