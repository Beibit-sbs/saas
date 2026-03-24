import { useQuery } from "@tanstack/react-query";
import { apiGet } from "@/shared/api/client";
import type { LatencyMetricsResponse, OpsMetricsResponse, OpsMetricsSnapshot } from "./types";

function errorText(err: unknown): string {
  if (err instanceof Error && err.message) return err.message;
  return "Request failed";
}

export function useOpsMetrics() {
  return useQuery<OpsMetricsSnapshot>({
    queryKey: ["ops", "metrics"],
    refetchInterval: 30_000,
    queryFn: async () => {
      const [opsResult, latencyResult] = await Promise.allSettled([
        apiGet<OpsMetricsResponse>("/metrics/ops"),
        apiGet<LatencyMetricsResponse>("/metrics/latency"),
      ]);

      const errors: string[] = [];
      const ops = opsResult.status === "fulfilled"
        ? opsResult.value
        : (errors.push(`ops: ${errorText(opsResult.reason)}`), undefined);
      const latency = latencyResult.status === "fulfilled"
        ? latencyResult.value
        : (errors.push(`latency: ${errorText(latencyResult.reason)}`), undefined);

      return {
        queue: {
          outboxBacklog: ops?.outbox_backlog ?? ops?.event_queue_size ?? null,
          eventQueueSize: ops?.event_queue_size ?? null,
          failedWebhooks: ops?.failed_webhooks ?? null,
          deadWebhooks: ops?.dead_webhooks ?? null,
          failedAutomationExecutions: ops?.failed_automation_executions ?? null,
          deadAutomationExecutions: ops?.dead_automation_executions ?? null,
          failedJobs: ops?.failed_jobs ?? null,
          deadJobs: ops?.dead_jobs ?? null,
          schedulerLastRun: ops?.scheduler_last_run ?? null,
        },
        traffic: {
          requestsPerMinute: latency?.requests_per_minute ?? null,
          p50LatencyMs: latency?.p50_latency_ms ?? null,
          p95LatencyMs: latency?.p95_latency_ms ?? null,
          p99LatencyMs: latency?.p99_latency_ms ?? null,
          http4xxCount: latency?.http_4xx_count ?? null,
          http5xxCount: latency?.http_5xx_count ?? null,
          developerApiErrorCount: latency?.developer_api_error_count ?? null,
        },
        updatedAt: new Date().toISOString(),
        errors,
      };
    },
  });
}