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

export interface ExecutiveAssignmentEntry {
  assignment_id: string;
  assignment_title: string;
  assignment_source: string;
  assignment_type: string;
  assigned_unit: string;
  assigned_person: string;
  created_at: string;
  due_date: string;
  completion_percent: number;
  execution_status: 'NOT_STARTED' | 'IN_PROGRESS' | 'AT_RISK' | 'ESCALATED' | 'OVERDUE' | 'COMPLETED' | 'CLOSED';
  risk_level: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  overdue_flag: boolean;
  escalation_flag: boolean;
}

export interface ExecutiveAssignmentSummary {
  tenant_id: number;
  entries: ExecutiveAssignmentEntry[];
  total_assignments: number;
  active_assignments: number;
  completed_assignments: number;
  overdue_assignments: number;
  escalated_assignments: number;
  execution_performance: number;
  execution_trend: string;
  read_only: boolean;
  aggregator_only: boolean;
  owner_modules: string[];
  generated_at: string;
}

export interface ExecutiveExecutionMetrics {
  tenant_id: number;
  total_assignments: number;
  execution_status_counts: Record<string, number>;
  overdue_assignments: number;
  escalated_assignments: number;
  execution_performance: number;
  execution_trend: string;
  escalation_inventory: Record<string, number>;
  escalation_summary: Record<string, number>;
  escalation_trends: string[];
  high_risk_assignments: ExecutiveAssignmentEntry[];
  signal_families: string[];
  read_only: boolean;
  aggregator_only: boolean;
  generated_at: string;
}

export interface ExecutiveControlTowerSummary {
  tenant_id: number;
  dashboard_owner_module: string;
  dashboard_view: string;
  total_decisions: number;
  total_protocols: number;
  total_assignments: number;
  active_assignments: number;
  completed_assignments: number;
  overdue_assignments: number;
  escalated_assignments: number;
  execution_rate: number;
  risk_score: number;
  kpi_score: number;
  executive_workload: number;
  strategic_initiatives: Record<string, number>;
  read_only: boolean;
  aggregator_only: boolean;
  auditability_preserved: boolean;
  generated_at: string;
}

export interface ExecutivePerformanceMetrics {
  tenant_id: number;
  total_decisions: number;
  total_protocols: number;
  total_assignments: number;
  active_assignments: number;
  completed_assignments: number;
  overdue_assignments: number;
  escalated_assignments: number;
  execution_rate: number;
  completion_rate: number;
  escalation_rate: number;
  workload_distribution: Record<string, number>;
  unit_performance: Record<string, number>;
  strategic_initiative_status: Record<string, number>;
  read_only: boolean;
  aggregator_only: boolean;
  generated_at: string;
}

export interface ExecutiveRiskOverview {
  tenant_id: number;
  risk_score: number;
  risk_distribution: Record<string, number>;
  high_risk_assignments: ExecutiveAssignmentEntry[];
  high_risk_units: Record<string, number>;
  high_risk_initiatives: Record<string, number>;
  escalation_hotspots: Record<string, number>;
  overdue_hotspots: Record<string, number>;
  signal_families: string[];
  read_only: boolean;
  aggregator_only: boolean;
  generated_at: string;
}

export interface ExecutiveKpiOverview {
  tenant_id: number;
  kpi_score: number;
  kpi_distribution: Record<string, number>;
  execution_rate: number;
  completion_rate: number;
  escalation_rate: number;
  unit_performance: Record<string, number>;
  strategic_initiative_status: Record<string, number>;
  signal_families: string[];
  read_only: boolean;
  aggregator_only: boolean;
  generated_at: string;
}

export interface RectorDashboardRuntimeSummary {
  tenant_id: number;
  rector_overview: ExecutiveControlTowerSummary;
  university_execution_status: ExecutivePerformanceMetrics;
  strategic_initiatives: Record<string, number>;
  executive_risks: ExecutiveRiskOverview;
  kpi_performance: ExecutiveKpiOverview;
  escalation_summary: Record<string, number>;
  read_only: boolean;
  aggregator_only: boolean;
  generated_at: string;
}

export interface StrategicInitiativeEntry {
  initiative_id: string;
  initiative_code: string;
  initiative_title: string;
  initiative_owner: string;
  initiative_status: string;
  start_date: string;
  target_date: string;
  completion_percent: number;
  linked_kpi_count: number;
  linked_assignment_count: number;
  risk_level: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  escalation_flag: boolean;
}

export interface StrategicInitiativeSummary {
  tenant_id: number;
  initiatives: StrategicInitiativeEntry[];
  total_initiatives: number;
  active_initiatives: number;
  completed_initiatives: number;
  at_risk_initiatives: number;
  delayed_initiatives: number;
  initiative_kpi_coverage: number;
  kpi_completion_alignment: number;
  kpi_deviation_visibility: Record<string, number>;
  kpi_ownership_visibility: Record<string, number>;
  roadmap_visibility: Record<string, number>;
  strategic_signal_families: string[];
  rbac_roles: string[];
  read_only: boolean;
  aggregator_only: boolean;
  generated_at: string;
}

export interface StrategicInitiativeMetrics {
  tenant_id: number;
  delayed_initiatives: StrategicInitiativeEntry[];
  high_risk_initiatives: StrategicInitiativeEntry[];
  kpi_deviation_hotspots: Record<string, number>;
  strategic_bottlenecks: Record<string, number>;
  execution_blockers: Record<string, number>;
  risk_distribution: Record<string, number>;
  strategic_signal_families: string[];
  read_only: boolean;
  aggregator_only: boolean;
  generated_at: string;
}

export interface DevelopmentProgramSummary {
  tenant_id: number;
  program_name: string;
  program_year: number;
  initiative_count: number;
  active_initiatives: number;
  completed_initiatives: number;
  at_risk_initiatives: number;
  delayed_initiatives: number;
  overall_progress: number;
  strategic_signal_families: string[];
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
