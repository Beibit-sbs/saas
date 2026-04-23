export interface AIRoutingRule {
  task_type: string;
  target_model: string;
  priority: number;
}

export interface AIRoutingPolicy {
  id: number;
  tenant_id: number;
  name: string;
  strategy: "priority";
  enabled: boolean;
  rules: AIRoutingRule[];
  fallback_chain: string[];
  created_at: string;
  updated_at: string;
}

export interface AIRoutingPolicyCreatePayload {
  name: string;
  strategy?: "priority";
  enabled?: boolean;
  rules?: AIRoutingRule[];
  fallback_chain?: string[];
}

export interface AIRoutingSelectionLogEntry {
  timestamp: string;
  tenant_id: number;
  model_key: string;
  mode: string;
  selection: string;
  policy_id?: number | null;
  task_type?: string | null;
}
