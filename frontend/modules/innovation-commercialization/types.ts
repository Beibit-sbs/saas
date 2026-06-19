export interface InnovationCommercializationShell {
  tenant_id: number;
  owner_module: string;
  extension_boundary: string;
  runtime_mode: string;
  canonical_base_vertical: string;
  integration_policy: string;
  bridge_modules: string[];
}

export interface InnovationOpportunity {
  opportunity_id: string;
  title: string;
  stage: string;
  readiness: string;
  source_module: string;
  notes: string;
}

export interface InnovationOpportunityList {
  tenant_id: number;
  items: InnovationOpportunity[];
}
