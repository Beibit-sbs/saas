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

export interface ExecutiveDecisionRegistryEntry {
  decision_id: string;
  decision_type: string;
  decision_source: string;
  decision_title: string;
  decision_status: string;
  decision_date: string;
  execution_status: 'NOT_STARTED' | 'IN_PROGRESS' | 'AT_RISK' | 'ESCALATED' | 'OVERDUE' | 'COMPLETED' | 'CLOSED';
  execution_progress: number;
  assigned_units: string[];
  overdue_flag: boolean;
  escalation_flag: boolean;
}

export interface ExecutiveDecisionRegistrySummary {
  tenant_id: number;
  entries: ExecutiveDecisionRegistryEntry[];
  total_decisions: number;
  decision_sources: Record<string, number>;
  execution_status_counts: Record<string, number>;
  read_only: boolean;
  aggregator_only: boolean;
  owner_modules: string[];
  generated_at: string;
}

export interface ExecutiveDecisionExecutionSummary {
  tenant_id: number;
  total_decisions: number;
  execution_status_counts: Record<string, number>;
  overdue_items: number;
  escalated_items: number;
  signal_families: string[];
  read_only: boolean;
  aggregator_only: boolean;
  generated_at: string;
}

export interface ExecutiveMeetingEntry {
  meeting_id: string;
  meeting_type: string;
  meeting_title: string;
  meeting_date: string;
  meeting_status: string;
  chairperson: string;
  participants_count: number;
  protocol_count: number;
  decision_count: number;
  execution_status: 'NOT_STARTED' | 'IN_PROGRESS' | 'AT_RISK' | 'ESCALATED' | 'OVERDUE' | 'COMPLETED' | 'CLOSED';
}

export interface ExecutiveMeetingSummary {
  tenant_id: number;
  entries: ExecutiveMeetingEntry[];
  total_meetings: number;
  meeting_status_counts: Record<string, number>;
  total_protocols: number;
  total_decisions: number;
  read_only: boolean;
  generated_at: string;
}

export interface ExecutiveProtocolEntry {
  protocol_id: string;
  protocol_number: string;
  protocol_title: string;
  protocol_date: string;
  protocol_status: string;
  decision_count: number;
  assignment_count: number;
  execution_progress: number;
  overdue_items: number;
  escalated_items: number;
}

export interface ExecutiveProtocolSummary {
  tenant_id: number;
  entries: ExecutiveProtocolEntry[];
  total_protocols: number;
  protocol_status_counts: Record<string, number>;
  total_decisions: number;
  total_assignments: number;
  average_execution_progress: number;
  overdue_items: number;
  escalated_items: number;
  read_only: boolean;
  generated_at: string;
}

export interface ExecutiveProtocolExecutionSummary {
  tenant_id: number;
  total_protocols: number;
  average_execution_progress: number;
  overdue_items: number;
  escalated_items: number;
  completion_status: Record<string, number>;
  linkage_inventory: Record<string, number>;
  signal_families: string[];
  read_only: boolean;
  generated_at: string;
}
