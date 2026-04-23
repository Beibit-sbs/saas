export interface EvalRun {
  run_id: string;
  model_name: string;
  eval_set_name: string;
  status: "pending" | "running" | "completed" | "failed";
  metrics: EvalMetric[];
  notes: string | null;
  created_by: string;
  created_at: string;
  completed_at: string | null;
}

export interface CreateEvalRunPayload {
  model_name: string;
  eval_set_name: string;
  metric_names?: string[];
  notes?: string;
}

export interface EvalMetric {
  metric_name: string;
  value: number;
  unit?: string;
}

export interface SubmitResultsPayload {
  run_id: string;
  metrics: EvalMetric[];
}

export interface LeaderboardEntry {
  rank: number;
  model_name: string;
  eval_set_name: string;
  primary_metric: string;
  primary_score: number;
  run_id: string;
  completed_at: string | null;
}
