export interface PromptTemplate {
  template_id: string;
  name: string;
  description: string | null;
  template_text: string;
  variables: string[];
  category: string;
  version: number;
  is_active: boolean;
  created_by: string;
  created_at: string;
}

export interface CreateTemplatePayload {
  name: string;
  description?: string;
  template_text: string;
  variables?: string[];
  category?: "academic" | "faculty" | "finance" | "operations" | "general";
  is_active?: boolean;
}

export interface ABTestRoutePayload {
  template_id_a: string;
  template_id_b: string;
  traffic_split_pct?: number;
  context_key: string;
}

export interface ABTestResult {
  selected_template_id: string;
  variant: "A" | "B";
  traffic_split_pct: number;
  context_key: string;
}
