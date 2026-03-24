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
};

export type CopilotAnswer = {
  question: string;
  summary: string;
  insights: CopilotInsightCard[];
  sources: CopilotSourceReference[];
  warnings: string[];
  recommendations: CopilotRecommendation[];
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
