export interface Job {
  id: string;
  job_type: string;
  status: "queued" | "running" | "completed" | "failed" | "cancelled";
  tenant_id: string | null;
  progress: number | null;
  error_message: string | null;
  created_at: string;
  started_at: string | null;
  completed_at: string | null;
  metadata: Record<string, unknown>;
}

export interface TriggerJobPayload {
  job_type: string;
  tenant_id?: string;
  metadata?: Record<string, unknown>;
}
