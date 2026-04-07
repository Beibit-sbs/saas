"use client";

import { useEffect, useState } from "react";
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
import { useLanguage } from "@/app/components/LanguageProvider";

function formatDateTime(value: string | null, unknownLabel: string): string {
  if (!value) return unknownLabel;
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return unknownLabel;
  return date.toLocaleString();
}

function hasAnyNumber(values: Array<number | null>): boolean {
  return values.some((value) => typeof value === "number");
}

function formatPercent(value: number | null): string | null {
  if (value === null) return null;
  return `${(value * 100).toFixed(2)}%`;
}

function toChartPercent(value: number | null, max: number): number {
  if (value === null || max <= 0) return 0;
  return Math.max(0, Math.min(100, (value / max) * 100));
}

export default function OpsConsolePage() {
  const { t } = useLanguage();
  const healthQuery = useOpsHealth();
  const metricsQuery = useOpsMetrics();
  const [loadingTimedOut, setLoadingTimedOut] = useState(false);

  const health = healthQuery.data;
  const metrics = metricsQuery.data;
  const isRefreshing = healthQuery.isFetching || metricsQuery.isFetching;

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
      metrics.queue.retryBacklog,
      metrics.queue.deadCount,
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
      metrics.traffic.errorRate,
    ]
    : [];

  const hasQueueData = hasAnyNumber(queueValues);
  const hasTrafficData = hasAnyNumber(trafficValues);

  const errorMessages = [...(health?.errors ?? []), ...(metrics?.errors ?? [])];

  const refreshAll = () => {
    void healthQuery.refetch();
    void metricsQuery.refetch();
    setLoadingTimedOut(false);
  };

  useEffect(() => {
    if (!isInitialLoading) {
      setLoadingTimedOut(false);
      return;
    }
    const timer = setTimeout(() => setLoadingTimedOut(true), 12_000);
    return () => clearTimeout(timer);
  }, [isInitialLoading]);

  if (isInitialLoading && !loadingTimedOut) {
    return (
      <div className="space-y-6" data-testid="ops-console-page">
        <PageHeader title={t("nav.platformOps")} description={t("console.ops.description")} icon={ServerCog} />
        <Skeleton className="h-36 w-full" />
        <Skeleton className="h-48 w-full" />
        <Skeleton className="h-48 w-full" />
      </div>
    );
  }

  if (loadingTimedOut && noHealthData && noMetricsData) {
    return (
      <div className="space-y-6" data-testid="ops-console-page">
        <PageHeader
          title={t("nav.platformOps")}
          description={t("console.ops.description")}
          icon={ServerCog}
        />
        <ErrorState
          title={t("ops.loadingTimedOut")}
          message={t("ops.loadingTimedOutMessage")}
          onRetry={refreshAll}
          retryLabel={t("state.retry")}
          retrying={isRefreshing}
        />
      </div>
    );
  }

  if (noHealthData && noMetricsData) {
    return (
      <div className="space-y-6" data-testid="ops-console-page">
        <PageHeader
          title={t("nav.platformOps")}
          description={t("console.ops.description")}
          icon={ServerCog}
        />
        <ErrorState
          title={t("ops.unableToLoadSignals")}
          message={errorMessages[0] ?? t("ops.endpointsUnavailable")}
          onRetry={refreshAll}
          retryLabel={t("state.retry")}
          retrying={isRefreshing}
        />
      </div>
    );
  }

  return (
    <RequirePermission permission={PERMISSIONS.OPS_READ}>
      <div className="space-y-6" data-testid="ops-console-page">
        <PageHeader
          title={t("nav.platformOps")}
          description={t("console.ops.description")}
          icon={ServerCog}
          actions={(
            <Button variant="outline" size="sm" onClick={refreshAll} disabled={isRefreshing}>
              <RefreshCw className="mr-2 h-4 w-4" />
              {t("ops.refresh")}
            </Button>
          )}
        />

        <OpsSectionCard
          title={t("ops.healthOverview")}
          description={t("ops.healthOverviewDescription")}
        >
          {health ? (
            <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4" data-testid="ops-health-section">
              <div className="rounded-md border p-3">
                <p className="text-xs text-muted-foreground">{t("ops.health.overallHealth")}</p>
                <div className="mt-2"><OpsStatusBadge status={health.overall} /></div>
              </div>
              <div className="rounded-md border p-3">
                <p className="text-xs text-muted-foreground">{t("ops.health.api")}</p>
                <div className="mt-2"><OpsStatusBadge status={health.api} /></div>
              </div>
              <div className="rounded-md border p-3">
                <p className="text-xs text-muted-foreground">{t("ops.health.database")}</p>
                <div className="mt-2"><OpsStatusBadge status={health.db} /></div>
              </div>
              <div className="rounded-md border p-3">
                <p className="text-xs text-muted-foreground">{t("ops.health.worker")}</p>
                <div className="mt-2"><OpsStatusBadge status={health.worker} /></div>
                {health.worker === "skipped" ? (
                  <p className="mt-1 text-xs text-muted-foreground">{t("ops.health.workerNotRequired")}</p>
                ) : null}
              </div>
              <div className="rounded-md border p-3 sm:col-span-2 lg:col-span-4">
                <p className="text-xs text-muted-foreground">{t("ops.health.schedulerLastRun")}</p>
                <p className="mt-1 text-sm font-medium">{formatDateTime(metrics?.queue.schedulerLastRun ?? null, t("ops.unknown"))}</p>
              </div>
            </div>
          ) : (
            <ErrorState
              title={t("ops.healthEndpointsUnavailable")}
              message={t("ops.healthEndpointsUnavailableMessage")}
              onRetry={() => void healthQuery.refetch()}
              retryLabel={t("state.retry")}
              retrying={healthQuery.isFetching}
            />
          )}
        </OpsSectionCard>

        <OpsSectionCard
          title={t("ops.queueRetryHealth")}
          description={t("ops.queueRetryHealthDescription")}
          actions={<OpsStatusBadge status={hasQueueData ? "healthy" : "unknown"} />}
        >
          {metrics ? (
            hasQueueData ? (
              <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4" data-testid="ops-queue-section">
                <MetricTile label={t("ops.queue.outboxBacklog")} value={metrics.queue.outboxBacklog} testId="metric-outbox-backlog" />
                <MetricTile label={t("ops.queue.eventQueueSize")} value={metrics.queue.eventQueueSize} testId="metric-event-queue" />
                <MetricTile label={t("ops.queue.failedWebhooks")} value={metrics.queue.failedWebhooks} testId="metric-failed-webhooks" />
                <MetricTile label={t("ops.queue.deadWebhooks")} value={metrics.queue.deadWebhooks} testId="metric-dead-webhooks" />
                <MetricTile label={t("ops.queue.failedAutomation")} value={metrics.queue.failedAutomationExecutions} testId="metric-failed-automation" />
                <MetricTile label={t("ops.queue.deadAutomation")} value={metrics.queue.deadAutomationExecutions} testId="metric-dead-automation" />
                <MetricTile label={t("ops.queue.failedJobs")} value={metrics.queue.failedJobs} testId="metric-failed-jobs" />
                <MetricTile label={t("ops.queue.deadJobs")} value={metrics.queue.deadJobs} testId="metric-dead-jobs" />
              </div>
            ) : (
              <EmptyState
                title={t("ops.queueMetricsUnavailable")}
                description={t("ops.queueMetricsUnavailableMessage")}
                action={<Button variant="outline" size="sm" onClick={() => void metricsQuery.refetch()} disabled={metricsQuery.isFetching}>{t("state.retry")}</Button>}
              />
            )
          ) : (
            <ErrorState
              title={t("ops.metricsEndpointUnavailable")}
              message={t("ops.metricsEndpointUnavailableMessage")}
              onRetry={() => void metricsQuery.refetch()}
              retryLabel={t("state.retry")}
              retrying={metricsQuery.isFetching}
            />
          )}
        </OpsSectionCard>

        <OpsSectionCard
          title={t("ops.apiTraffic")}
          description={t("ops.apiTrafficDescription")}
          actions={<Activity className="h-4 w-4 text-muted-foreground" />}
        >
          {metrics ? (
            hasTrafficData ? (
              <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4" data-testid="ops-traffic-section">
                <MetricTile label={t("ops.traffic.requestsPerMin")} value={metrics.traffic.requestsPerMinute} testId="metric-rpm" />
                <MetricTile label={t("ops.traffic.p50Latency")} value={metrics.traffic.p50LatencyMs === null ? null : `${metrics.traffic.p50LatencyMs} ms`} testId="metric-p50" />
                <MetricTile label={t("ops.traffic.p95Latency")} value={metrics.traffic.p95LatencyMs === null ? null : `${metrics.traffic.p95LatencyMs} ms`} testId="metric-p95" />
                <MetricTile label={t("ops.traffic.p99Latency")} value={metrics.traffic.p99LatencyMs === null ? null : `${metrics.traffic.p99LatencyMs} ms`} testId="metric-p99" />
                <MetricTile label={t("ops.traffic.http4xxCount")} value={metrics.traffic.http4xxCount} testId="metric-4xx" />
                <MetricTile label={t("ops.traffic.http5xxCount")} value={metrics.traffic.http5xxCount} testId="metric-5xx" />
                <MetricTile label={t("ops.traffic.developerApiErrors")} value={metrics.traffic.developerApiErrorCount} testId="metric-dev-errors" />
                <MetricTile label={t("ops.traffic.errorRate")} value={formatPercent(metrics.traffic.errorRate)} testId="metric-error-rate" />
              </div>
            ) : (
              <EmptyState
                title={t("ops.trafficMetricsUnavailable")}
                description={t("ops.trafficMetricsUnavailableMessage")}
                action={<Button variant="outline" size="sm" onClick={() => void metricsQuery.refetch()} disabled={metricsQuery.isFetching}>{t("state.retry")}</Button>}
              />
            )
          ) : (
            <ErrorState
              title={t("ops.latencyEndpointUnavailable")}
              message={t("ops.latencyEndpointUnavailableMessage")}
              onRetry={() => void metricsQuery.refetch()}
              retryLabel={t("state.retry")}
              retrying={metricsQuery.isFetching}
            />
          )}
          {metrics && hasTrafficData ? (
            <div className="mt-4 grid gap-3 sm:grid-cols-2" data-testid="ops-traffic-chart">
              <div className="rounded-md border bg-card p-3">
                <p className="text-xs text-muted-foreground">{t("ops.latencyChart")}</p>
                <div className="mt-3 space-y-2">
                  {[
                    [t("ops.traffic.p50Latency"), metrics.traffic.p50LatencyMs],
                    [t("ops.traffic.p95Latency"), metrics.traffic.p95LatencyMs],
                    [t("ops.traffic.p99Latency"), metrics.traffic.p99LatencyMs],
                  ].map(([label, raw]) => (
                    <div key={String(label)}>
                      <div className="mb-1 flex items-center justify-between text-xs">
                        <span>{label}</span>
                        <span className="font-medium">{raw === null ? t("ops.unknown") : `${raw} ms`}</span>
                      </div>
                      <div className="h-2 rounded bg-muted">
                        <div className="h-2 rounded bg-sky-500" style={{ width: `${toChartPercent(raw as number | null, 1000)}%` }} />
                      </div>
                    </div>
                  ))}
                </div>
              </div>
              <div className="rounded-md border bg-card p-3">
                <p className="text-xs text-muted-foreground">{t("ops.errorChart")}</p>
                <div className="mt-3 space-y-2">
                  {[
                    [t("ops.traffic.http4xxCount"), metrics.traffic.http4xxCount],
                    [t("ops.traffic.http5xxCount"), metrics.traffic.http5xxCount],
                    [t("ops.traffic.errorRate"), metrics.traffic.errorRate === null ? null : metrics.traffic.errorRate * 100],
                  ].map(([label, raw]) => (
                    <div key={String(label)}>
                      <div className="mb-1 flex items-center justify-between text-xs">
                        <span>{label}</span>
                        <span className="font-medium">
                          {label === t("ops.traffic.errorRate")
                            ? (raw === null ? t("ops.unknown") : `${(raw as number).toFixed(2)}%`)
                            : (raw ?? t("ops.unknown"))}
                        </span>
                      </div>
                      <div className="h-2 rounded bg-muted">
                        <div className="h-2 rounded bg-rose-500" style={{ width: `${toChartPercent(raw as number | null, 100)}%` }} />
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          ) : null}
        </OpsSectionCard>

        <OpsSectionCard
          title={t("ops.runtimeAndBackup")}
          description={t("ops.runtimeAndBackupDescription")}
        >
          {metrics ? (
            <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4" data-testid="ops-runtime-backup-section">
              <MetricTile
                label={t("ops.runtime.workerHeartbeatAge")}
                value={metrics.runtime.workerHeartbeatAgeSeconds === null ? null : `${metrics.runtime.workerHeartbeatAgeSeconds}s`}
                testId="metric-worker-heartbeat-age"
              />
              <MetricTile
                label={t("ops.runtime.schedulerHeartbeatAge")}
                value={metrics.runtime.schedulerHeartbeatAgeSeconds === null ? null : `${metrics.runtime.schedulerHeartbeatAgeSeconds}s`}
                testId="metric-scheduler-heartbeat-age"
              />
              <MetricTile label={t("ops.queue.retryBacklog")} value={metrics.queue.retryBacklog} testId="metric-retry-backlog" />
              <MetricTile label={t("ops.queue.deadCount")} value={metrics.queue.deadCount} testId="metric-dead-count" />
              <div className="rounded-md border p-3 sm:col-span-2">
                <p className="text-xs text-muted-foreground">{t("ops.backup.lastStatus")}</p>
                <p className="mt-1 text-sm font-medium">{metrics.backup.lastStatus || t("ops.unknown")}</p>
              </div>
              <div className="rounded-md border p-3 sm:col-span-2">
                <p className="text-xs text-muted-foreground">{t("ops.backup.lastFinishedAt")}</p>
                <p className="mt-1 text-sm font-medium">{formatDateTime(metrics.backup.lastFinishedAt, t("ops.unknown"))}</p>
              </div>
              {metrics.backup.lastError ? (
                <div className="rounded-md border border-yellow-300 bg-yellow-50 p-3 text-xs text-yellow-900 sm:col-span-2 lg:col-span-4">
                  {t("ops.backup.lastError")}: {metrics.backup.lastError}
                </div>
              ) : null}
            </div>
          ) : (
            <ErrorState
              title={t("ops.metricsEndpointUnavailable")}
              message={t("ops.metricsEndpointUnavailableMessage")}
              onRetry={() => void metricsQuery.refetch()}
              retryLabel={t("state.retry")}
              retrying={metricsQuery.isFetching}
            />
          )}
        </OpsSectionCard>

        <OpsSectionCard title={t("ops.lastUpdated")} description={t("ops.lastUpdatedDescription")}>
          <div className="space-y-2" data-testid="ops-last-updated">
            <p className="text-sm">{t("ops.healthLabel")}: <span className="font-medium">{formatDateTime(health?.updatedAt ?? null, t("ops.unknown"))}</span></p>
            <p className="text-sm">{t("ops.metricsLabel")}: <span className="font-medium">{formatDateTime(metrics?.updatedAt ?? null, t("ops.unknown"))}</span></p>
            {errorMessages.length > 0 && (
              <div className="rounded-md border border-yellow-300 bg-yellow-50 p-2 text-xs text-yellow-900">
                {t("ops.partialDataMode")}: {errorMessages.join(" | ")}
              </div>
            )}
          </div>
        </OpsSectionCard>
      </div>
    </RequirePermission>
  );
}