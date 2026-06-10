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
