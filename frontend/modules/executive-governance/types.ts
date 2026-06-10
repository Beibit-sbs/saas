export interface ExecutiveGovernanceRuntimeOverview {
  tenant_id: number;
  owner_module: string;
  runtime_boundary: string;
  navigation_entry: string;
  canonical_modules: string[];
  read_only_runtime: boolean;
  provider_integrations_enabled: boolean;
  external_calls_enabled: boolean;
  executive_assignments: number;
  executive_decisions: number;
  executive_protocols: number;
  executive_meetings: number;
  overdue_items: number;
  escalated_items: number;
  strategic_items: number;
  executive_signals: number;
  generated_at: string;
}

export interface ExecutiveGovernanceRuntimeSummary {
  tenant_id: number;
  read_only: boolean;
  owner_modules: string[];
  executive_assignments: number;
  executive_decisions: number;
  executive_protocols: number;
  executive_meetings: number;
  overdue_items: number;
  escalated_items: number;
  strategic_items: number;
  executive_signals: number;
  generated_at: string;
}

export interface ExecutiveGovernanceSignalSummary {
  signal_family: string;
  owner_module: string;
  source_module: string;
  read_only: boolean;
  observed_items: number;
  notes: string;
}

export interface ExecutiveGovernanceDashboardSummary {
  tenant_id: number;
  dashboard_owner_module: string;
  dashboard_view: string;
  widgets: string[];
  executive_assignments: number;
  executive_decisions: number;
  executive_protocols: number;
  executive_meetings: number;
  overdue_items: number;
  escalated_items: number;
  strategic_items: number;
  executive_signals: number;
  signal_summaries: ExecutiveGovernanceSignalSummary[];
  rbac_roles: string[];
  read_only: boolean;
  auditability_preserved: boolean;
  generated_at: string;
}
