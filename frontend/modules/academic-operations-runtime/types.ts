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
