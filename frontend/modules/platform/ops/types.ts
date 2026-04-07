export type OpsStatus = "healthy" | "degraded" | "critical" | "skipped" | "unknown";

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
    retryBacklog: number | null;
    deadCount: number | null;
  };
  traffic: {
    requestsPerMinute: number | null;
    p50LatencyMs: number | null;
    p95LatencyMs: number | null;
    p99LatencyMs: number | null;
    http4xxCount: number | null;
    http5xxCount: number | null;
    developerApiErrorCount: number | null;
    errorRate: number | null;
  };
  runtime: {
    workerHeartbeat: string | null;
    workerHeartbeatAgeSeconds: number | null;
    schedulerHeartbeatAgeSeconds: number | null;
  };
  backup: {
    lastStatus: string;
    lastStartedAt: string | null;
    lastFinishedAt: string | null;
    lastError: string | null;
  };
  updatedAt: string;
  errors: string[];
}

export interface OpsSummaryResponse {
  updated_at: string;
  tenant_id: number;
  latency: {
    p50_ms: number;
    p95_ms: number;
    p99_ms: number;
  };
  traffic: {
    requests_per_minute: number;
    http_4xx_count: number;
    http_5xx_count: number;
    error_rate: number;
  };
  runtime: {
    worker_heartbeat: string | null;
    worker_heartbeat_age_seconds: number | null;
    scheduler_heartbeat: string | null;
    scheduler_heartbeat_age_seconds: number | null;
  };
  queues: {
    event_queue_size: number | null;
    outbox_backlog: number | null;
    retry_backlog: number | null;
    failed_webhooks: number | null;
    dead_webhooks: number | null;
    failed_jobs: number | null;
    dead_jobs: number | null;
    failed_automation_executions: number | null;
    dead_automation_executions: number | null;
    dead_count: number;
  };
  backup: {
    last_status: string;
    last_started_at: string | null;
    last_finished_at: string | null;
    last_error: string | null;
  };
}