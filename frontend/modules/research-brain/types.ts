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
