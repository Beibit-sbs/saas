import { useQuery, type UseQueryResult } from "@tanstack/react-query";
import { apiGet } from "@/shared/api/client";
import type { OpsMetricsSnapshot, OpsSummaryResponse } from "./types";

function errorText(err: unknown): string {
  if (err instanceof Error && err.message) return err.message;
  return "Request failed";
}

export function useOpsMetrics(): UseQueryResult<OpsMetricsSnapshot, Error> {
  return useQuery<OpsMetricsSnapshot, Error>({
    queryKey: ["ops", "metrics"],
    refetchInterval: 30_000,
    queryFn: async () => {
      const summary = await apiGet<OpsSummaryResponse>("/api/v1/platform/ops/summary");

      return {
        queue: {
          outboxBacklog: summary.queues.outbox_backlog,
          eventQueueSize: summary.queues.event_queue_size,
          failedWebhooks: summary.queues.failed_webhooks,
          deadWebhooks: summary.queues.dead_webhooks,
          failedAutomationExecutions: summary.queues.failed_automation_executions,
          deadAutomationExecutions: summary.queues.dead_automation_executions,
          failedJobs: summary.queues.failed_jobs,
          deadJobs: summary.queues.dead_jobs,
          schedulerLastRun: summary.runtime.scheduler_heartbeat,
          retryBacklog: summary.queues.retry_backlog,
          deadCount: summary.queues.dead_count,
        },
        traffic: {
          requestsPerMinute: summary.traffic.requests_per_minute,
          p50LatencyMs: summary.latency.p50_ms,
          p95LatencyMs: summary.latency.p95_ms,
          p99LatencyMs: summary.latency.p99_ms,
          http4xxCount: summary.traffic.http_4xx_count,
          http5xxCount: summary.traffic.http_5xx_count,
          developerApiErrorCount: null,
          errorRate: summary.traffic.error_rate,
        },
        runtime: {
          workerHeartbeat: summary.runtime.worker_heartbeat,
          workerHeartbeatAgeSeconds: summary.runtime.worker_heartbeat_age_seconds,
          schedulerHeartbeatAgeSeconds: summary.runtime.scheduler_heartbeat_age_seconds,
        },
        backup: {
          lastStatus: summary.backup.last_status,
          lastStartedAt: summary.backup.last_started_at,
          lastFinishedAt: summary.backup.last_finished_at,
          lastError: summary.backup.last_error,
        },
        updatedAt: summary.updated_at,
        errors: [],
      };
    },
    retry: 1,
  });
}