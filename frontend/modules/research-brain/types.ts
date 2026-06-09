export interface ResearchBrainShellResponse {
  tenant_id: number;
  owner_module: string;
  runtime_boundary: string;
  navigation_entry: string;
  bridge_modules: string[];
  read_only_aggregation: boolean;
  provider_execution_enabled: boolean;
  external_calls_enabled: boolean;
}

export interface ResearchBrainOrchestrationItem {
  source_module: string;
  read_only: boolean;
  total: number;
  notes: string;
}

export interface ResearchBrainOrchestrationResponse {
  tenant_id: number;
  projects: ResearchBrainOrchestrationItem;
  grants: ResearchBrainOrchestrationItem;
  publications: ResearchBrainOrchestrationItem;
  ethics: ResearchBrainOrchestrationItem;
  kpi: ResearchBrainOrchestrationItem;
  signals: ResearchBrainOrchestrationItem;
  researchers: ResearchBrainOrchestrationItem;
  researcher_summary: ResearchBrainOrchestrationItem;
  researcher_health: ResearchBrainOrchestrationItem;
  researcher_workload: ResearchBrainOrchestrationItem;
  researcher_risk: ResearchBrainOrchestrationItem;
}

export interface ResearchBrainContextSource {
  source: string;
  contract_status: string;
  read_only: boolean;
  summary: Record<string, unknown>;
}

export interface ResearchBrainContextResponse {
  tenant_id: number;
  context: Record<string, ResearchBrainContextSource>;
}

export interface ResearchBrainKpiSurfaceResponse {
  tenant_id: number;
  owner_module: string;
  publication_count: number;
  grant_count: number;
  project_count: number;
  ethics_count: number;
  read_only: boolean;
  provider_execution_enabled: boolean;
}

export interface ResearchBrainSignalItem {
  family: string;
  owner: string;
  source: string;
  consumer: string;
  review_queue: string;
  read_only: boolean;
  scoring_engine_enabled: boolean;
  observed_count: number;
}

export interface ResearchBrainSignalSurfaceResponse {
  tenant_id: number;
  signals: ResearchBrainSignalItem[];
}

export interface ResearchBrainRoleValidation {
  role: string;
  required_permissions: string[];
  status: string;
}

export interface ResearchBrainRbacValidationResponse {
  tenant_id: number;
  tenant: string;
  rbac: string;
  audit: string;
  roles: ResearchBrainRoleValidation[];
}

export interface Researcher {
  researcher_id: string;
  employee_id: string;
  full_name: string;
  position: string;
  faculty: string | null;
  department: string | null;
  laboratory: string | null;
  research_areas: string[];
  specializations: string[];
  active_projects: number;
  active_grants: number;
  publication_count: number;
  citation_count: number;
  h_index: number;
  risk_level: string;
  status: string;
}

export interface ResearcherListResponse {
  items: Researcher[];
}

export interface ResearcherDashboardSummaryResponse {
  tenant_id: number;
  total_researchers: number;
  active_researchers: number;
  high_risk_researchers: number;
  publication_total: number;
  active_projects_total: number;
  active_grants_total: number;
}

export interface ResearcherProfile {
  researcher_id: string;
  employee_id: string;
  full_name: string;
  position: string;
  faculty: string | null;
  department: string | null;
  laboratory: string | null;
  research_areas: string[];
  specializations: string[];
  status: string;
}

export interface ResearcherActivityProfileResponse {
  tenant_id: number;
  researcher: ResearcherProfile;
  project_summary: { active_projects: number };
  grant_summary: { active_grants: number };
  publication_summary: { publication_count: number; citation_count: number };
  scientometric_summary: { h_index: number; citation_count: number };
}

export interface ResearcherRiskProfileResponse {
  tenant_id: number;
  researcher_id: string;
  risk_level: string;
  workload: Record<string, number>;
  signals: string[];
  notes: string[];
}
