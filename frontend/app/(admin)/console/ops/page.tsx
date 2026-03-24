"use client";

import { Activity, RefreshCw, ServerCog } from "lucide-react";
import { PERMISSIONS } from "@/shared/config/permissions";
import { Button } from "@/shared/ui/button";
import { EmptyState } from "@/shared/ui/empty-state";
import { ErrorState } from "@/shared/ui/error-state";
import { PageHeader } from "@/shared/ui/page-header";
import { RequirePermission } from "@/shared/ui/permission-gate";
import { Skeleton } from "@/shared/ui/skeleton";
import { MetricTile } from "@/modules/platform/ops/metric-tile";
import { OpsSectionCard } from "@/modules/platform/ops/ops-section-card";
import { OpsStatusBadge } from "@/modules/platform/ops/status-badge";
import { useOpsHealth } from "@/modules/platform/ops/use-ops-health";
import { useOpsMetrics } from "@/modules/platform/ops/use-ops-metrics";

function formatDateTime(value: string | null): string {
  if (!value) return "Unknown";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "Unknown";
  return date.toLocaleString();
}

function hasAnyNumber(values: Array<number | null>): boolean {
  return values.some((value) => typeof value === "number");
}

export default function OpsConsolePage() {
  const healthQuery = useOpsHealth();
  const metricsQuery = useOpsMetrics();

  const health = healthQuery.data;
  const metrics = metricsQuery.data;

  const isInitialLoading = !health && !metrics && (healthQuery.isLoading || metricsQuery.isLoading);
  const noHealthData = !health;
  const noMetricsData = !metrics;

  const queueValues = metrics
    ? [
      metrics.queue.outboxBacklog,
      metrics.queue.eventQueueSize,
      metrics.queue.failedWebhooks,
      metrics.queue.failedAutomationExecutions,
      metrics.queue.failedJobs,
    ]
    : [];

  const trafficValues = metrics
    ? [
      metrics.traffic.requestsPerMinute,
      metrics.traffic.p50LatencyMs,
      metrics.traffic.p95LatencyMs,
      metrics.traffic.p99LatencyMs,
      metrics.traffic.http4xxCount,
      metrics.traffic.http5xxCount,
      metrics.traffic.developerApiErrorCount,
    ]
    : [];

  const hasQueueData = hasAnyNumber(queueValues);
  const hasTrafficData = hasAnyNumber(trafficValues);

  const errorMessages = [...(health?.errors ?? []), ...(metrics?.errors ?? [])];

  const refreshAll = () => {
    void healthQuery.refetch();
    void metricsQuery.refetch();
  };

  if (isInitialLoading) {
    return (
      <div className="space-y-6" data-testid="ops-console-page">
        <PageHeader title="Platform Ops Console" description="Operational visibility for platform reliability" icon={ServerCog} />
        <Skeleton className="h-36 w-full" />
        <Skeleton className="h-48 w-full" />
        <Skeleton className="h-48 w-full" />
      </div>
    );
  }

  if (noHealthData && noMetricsData) {
    return (
      <div className="space-y-6" data-testid="ops-console-page">
        <PageHeader
          title="Platform Ops Console"
          description="Operational visibility for platform reliability"
          icon={ServerCog}
        />
        <ErrorState
          title="Unable to load ops signals"
          message={errorMessages[0] ?? "Ops endpoints are currently unavailable."}
          onRetry={refreshAll}
        />
      </div>
    );
  }

  return (
    <RequirePermission permission={PERMISSIONS.OPS_READ}>
      <div className="space-y-6" data-testid="ops-console-page">
        <PageHeader
          title="Platform Ops Console"
          description="Operational visibility for platform health, queues and API behavior"
          icon={ServerCog}
          actions={(
            <Button variant="outline" size="sm" onClick={refreshAll}>
              <RefreshCw className="mr-2 h-4 w-4" />
              Refresh
            </Button>
          )}
        />

        <OpsSectionCard
          title="Health Overview"
          description="Current status for core platform dependencies"
        >
          {health ? (
            <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4" data-testid="ops-health-section">
              <div className="rounded-md border p-3">
                <p className="text-xs text-muted-foreground">Overall Health</p>
                <div className="mt-2"><OpsStatusBadge status={health.overall} /></div>
              </div>
              <div className="rounded-md border p-3">
                <p className="text-xs text-muted-foreground">API</p>
                <div className="mt-2"><OpsStatusBadge status={health.api} /></div>
              </div>
              <div className="rounded-md border p-3">
                <p className="text-xs text-muted-foreground">Database</p>
                <div className="mt-2"><OpsStatusBadge status={health.db} /></div>
              </div>
              <div className="rounded-md border p-3">
                <p className="text-xs text-muted-foreground">Worker</p>
                <div className="mt-2"><OpsStatusBadge status={health.worker} /></div>
              </div>
              <div className="rounded-md border p-3 sm:col-span-2 lg:col-span-4">
                <p className="text-xs text-muted-foreground">Scheduler Last Run</p>
                <p className="mt-1 text-sm font-medium">{formatDateTime(metrics?.queue.schedulerLastRun ?? null)}</p>
              </div>
            </div>
          ) : (
            <ErrorState title="Health endpoints unavailable" message="Could not read /health endpoints." onRetry={() => void healthQuery.refetch()} />
          )}
        </OpsSectionCard>

        <OpsSectionCard
          title="Queue / Retry Health"
          description="Backlogs, failed deliveries and dead-state visibility"
          actions={<OpsStatusBadge status={hasQueueData ? "healthy" : "unknown"} />}
        >
          {metrics ? (
            hasQueueData ? (
              <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4" data-testid="ops-queue-section">
                <MetricTile label="Outbox Backlog" value={metrics.queue.outboxBacklog} testId="metric-outbox-backlog" />
                <MetricTile label="Event Queue Size" value={metrics.queue.eventQueueSize} testId="metric-event-queue" />
                <MetricTile label="Failed Webhooks" value={metrics.queue.failedWebhooks} testId="metric-failed-webhooks" />
                <MetricTile label="Dead Webhooks" value={metrics.queue.deadWebhooks} testId="metric-dead-webhooks" />
                <MetricTile label="Failed Automation" value={metrics.queue.failedAutomationExecutions} testId="metric-failed-automation" />
                <MetricTile label="Dead Automation" value={metrics.queue.deadAutomationExecutions} testId="metric-dead-automation" />
                <MetricTile label="Failed Jobs" value={metrics.queue.failedJobs} testId="metric-failed-jobs" />
                <MetricTile label="Dead Jobs" value={metrics.queue.deadJobs} testId="metric-dead-jobs" />
              </div>
            ) : (
              <EmptyState
                title="Queue metrics unavailable"
                description="No queue/retry metrics were returned by /metrics/ops."
                action={<Button variant="outline" size="sm" onClick={() => void metricsQuery.refetch()}>Retry</Button>}
              />
            )
          ) : (
            <ErrorState title="Metrics endpoint unavailable" message="Could not read /metrics/ops." onRetry={() => void metricsQuery.refetch()} />
          )}
        </OpsSectionCard>

        <OpsSectionCard
          title="API / Traffic"
          description="Latency and error-rate summary for recent requests"
          actions={<Activity className="h-4 w-4 text-muted-foreground" />}
        >
          {metrics ? (
            hasTrafficData ? (
              <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4" data-testid="ops-traffic-section">
                <MetricTile label="Requests / Min" value={metrics.traffic.requestsPerMinute} testId="metric-rpm" />
                <MetricTile label="P50 Latency" value={metrics.traffic.p50LatencyMs === null ? null : `${metrics.traffic.p50LatencyMs} ms`} testId="metric-p50" />
                <MetricTile label="P95 Latency" value={metrics.traffic.p95LatencyMs === null ? null : `${metrics.traffic.p95LatencyMs} ms`} testId="metric-p95" />
                <MetricTile label="P99 Latency" value={metrics.traffic.p99LatencyMs === null ? null : `${metrics.traffic.p99LatencyMs} ms`} testId="metric-p99" />
                <MetricTile label="4xx Count" value={metrics.traffic.http4xxCount} testId="metric-4xx" />
                <MetricTile label="5xx Count" value={metrics.traffic.http5xxCount} testId="metric-5xx" />
                <MetricTile label="Developer API Errors" value={metrics.traffic.developerApiErrorCount} testId="metric-dev-errors" />
              </div>
            ) : (
              <EmptyState
                title="Traffic metrics unavailable"
                description="No latency/traffic metrics were returned by /metrics/latency."
                action={<Button variant="outline" size="sm" onClick={() => void metricsQuery.refetch()}>Retry</Button>}
              />
            )
          ) : (
            <ErrorState title="Latency endpoint unavailable" message="Could not read /metrics/latency." onRetry={() => void metricsQuery.refetch()} />
          )}
        </OpsSectionCard>

        <OpsSectionCard title="Last Updated" description="Refresh status and endpoint warnings">
          <div className="space-y-2" data-testid="ops-last-updated">
            <p className="text-sm">Health: <span className="font-medium">{formatDateTime(health?.updatedAt ?? null)}</span></p>
            <p className="text-sm">Metrics: <span className="font-medium">{formatDateTime(metrics?.updatedAt ?? null)}</span></p>
            {errorMessages.length > 0 && (
              <div className="rounded-md border border-yellow-300 bg-yellow-50 p-2 text-xs text-yellow-900">
                Partial data mode: {errorMessages.join(" | ")}
              </div>
            )}
          </div>
        </OpsSectionCard>
      </div>
    </RequirePermission>
  );
}