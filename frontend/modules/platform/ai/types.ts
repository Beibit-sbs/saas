export type CopilotSourceReference = {
  source_type: "kpi" | "analytics" | "context" | "automation" | string;
  reference: string;
};

export type CopilotInsightCard = {
  title: string;
  value: string;
  explanation: string;
};

export type CopilotRecommendationAction = {
  action_type: "navigate" | "review" | "alert" | string;
  label: string;
  target?: string | null;
};

export type CopilotRecommendation = {
  recommendation_type: string;
  title: string;
  priority: "high" | "medium" | "low";
  reason: string;
  suggested_actions: CopilotRecommendationAction[];
  created_intervention_case_id?: number | null;
};

export type CopilotPromptPack = {
  prompt_key: string;
  admin_role: string;
  tenant_id: number;
  query_type: string;
  scope: string;
};

export type CopilotTenantPolicyBinding = {
  binding_mode: string;
  bound_tenant_id: number;
  cross_tenant_allowed: boolean;
  admin_role: string;
};

export type CopilotAuditTaxonomy = {
  domain: string;
  action: string;
  query_type: string;
};

export type CopilotAnswer = {
  question: string;
  summary: string;
  insights: CopilotInsightCard[];
  sources: CopilotSourceReference[];
  warnings: string[];
  recommendations: CopilotRecommendation[];
  created_intervention_case_id?: number | null;
  query_type?: string | null;
  admin_prompt_pack?: CopilotPromptPack | null;
  tenant_policy_binding?: CopilotTenantPolicyBinding | null;
  audit_taxonomy?: CopilotAuditTaxonomy | null;
};

export type CopilotAskRequest = {
  tenant_id: number;
  question: string;
  context?: Record<string, unknown>;
};

export type CopilotQueryLog = {
  id: number;
  tenant_id: number;
  actor_id: string;
  question: string;
  query_type: string;
  retrieved_sources_json: Array<Record<string, unknown>>;
  answer_json: Record<string, unknown>;
  created_at: string;
};
