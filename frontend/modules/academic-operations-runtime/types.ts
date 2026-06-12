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
