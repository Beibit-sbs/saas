import { useQuery } from "@tanstack/react-query";
import { apiGet } from "@/shared/api/client";
import type { HealthStatus, Metrics } from "./types";

type OpsSummaryResponse = {
  traffic: {
    requests_per_minute: number;
  };
  latency: {
    p50_ms: number;
  };
  queues: {
    failed_jobs: number | null;
    dead_jobs: number | null;
    retry_backlog: number | null;
  };
};

export function useHealthStatus() {
  return useQuery({
    queryKey: ["health"],
    queryFn: () => apiGet<HealthStatus>("/api/health"),
    refetchInterval: 60_000,
  });
}

export function useMetrics() {
  return useQuery({
    queryKey: ["metrics"],
    queryFn: async (): Promise<Metrics> => {
      const summary = await apiGet<OpsSummaryResponse>("/api/v1/platform/ops/summary");
      const requestsPerMinute = summary.traffic.requests_per_minute ?? 0;

      return {
        total_tenants: 0,
        active_tenants: 0,
        total_students: 0,
        active_jobs: summary.queues.retry_backlog ?? 0,
        queued_jobs: summary.queues.retry_backlog ?? 0,
        failed_jobs_24h: (summary.queues.failed_jobs ?? 0) + (summary.queues.dead_jobs ?? 0),
        api_requests_1h: requestsPerMinute * 60,
        avg_response_ms: summary.latency.p50_ms ?? 0,
      };
    },
    refetchInterval: 60_000,
  });
}
