export type OpsStatus = "healthy" | "degraded" | "critical" | "unknown";

export interface HealthApiResponse {
  status: string;
  service?: string;
}

export interface HealthDbResponse {
  status: string;
  database?: string;
}

export interface HealthWorkerResponse {
  status: string;
  worker?: string;
  heartbeat_at?: string;
}

export interface OpsMetricsResponse {
  event_queue_size?: number;
  outbox_backlog?: number;
  failed_webhooks?: number;
  dead_webhooks?: number;
  failed_automation_executions?: number;
  dead_automation_executions?: number;
  failed_jobs?: number;
  dead_jobs?: number;
  worker_last_heartbeat?: string;
  scheduler_last_run?: string;
  retry_backlog?: number;
}

export interface LatencyMetricsResponse {
  p50_latency_ms?: number;
  p95_latency_ms?: number;
  p99_latency_ms?: number;
  requests_per_minute?: number;
  http_4xx_count?: number;
  http_5xx_count?: number;
  developer_api_error_count?: number;
}

export interface OpsHealthSnapshot {
  overall: OpsStatus;
  api: OpsStatus;
  db: OpsStatus;
  worker: OpsStatus;
  workerHeartbeatAt: string | null;
  updatedAt: string;
  errors: string[];
}

export interface OpsMetricsSnapshot {
  queue: {
    outboxBacklog: number | null;
    eventQueueSize: number | null;
    failedWebhooks: number | null;
    deadWebhooks: number | null;
    failedAutomationExecutions: number | null;
    deadAutomationExecutions: number | null;
    failedJobs: number | null;
    deadJobs: number | null;
    schedulerLastRun: string | null;
  };
  traffic: {
    requestsPerMinute: number | null;
    p50LatencyMs: number | null;
    p95LatencyMs: number | null;
    p99LatencyMs: number | null;
    http4xxCount: number | null;
    http5xxCount: number | null;
    developerApiErrorCount: number | null;
  };
  updatedAt: string;
  errors: string[];
}