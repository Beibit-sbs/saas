"use client";

import { PageHeader } from "@/shared/ui/page-header";
import { MetricCard } from "@/shared/ui/metric-card";
import { StatusBadge } from "@/shared/ui/status-badge";
import { Skeleton } from "@/shared/ui/skeleton";
import { ErrorState } from "@/shared/ui/error-state";
import { useHealthStatus, useMetrics } from "@/modules/platform/health/hooks";
import { Activity, Zap, Clock, AlertCircle } from "lucide-react";

export default function HealthPage() {
  const { data: health, isLoading: healthLoading, error, refetch } = useHealthStatus();
  const { data: metrics, isLoading: metricsLoading } = useMetrics();

  if (error) return <ErrorState title="Failed to load health data" onRetry={refetch} />;

  return (
    <div className="space-y-6">
      <PageHeader title="Health & Metrics" description="Platform operational status" icon={Activity} />

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <MetricCard
          label="API Requests (1h)"
          value={metrics?.api_requests_1h}
          icon={Zap}
          loading={metricsLoading}
        />
        <MetricCard
          label="Avg Response"
          value={metrics ? `${metrics.avg_response_ms}ms` : undefined}
          icon={Clock}
          loading={metricsLoading}
        />
        <MetricCard
          label="Active Jobs"
          value={metrics?.active_jobs}
          icon={Activity}
          loading={metricsLoading}
        />
        <MetricCard
          label="Failed Jobs (24h)"
          value={metrics?.failed_jobs_24h}
          icon={AlertCircle}
          loading={metricsLoading}
        />
      </div>

      <div className="space-y-2">
        <h2 className="text-sm font-medium">Services</h2>
        {healthLoading ? (
          <div className="space-y-2">
            {Array.from({ length: 4 }).map((_, i) => (
              <Skeleton key={i} className="h-14 rounded-lg" />
            ))}
          </div>
        ) : (
          <div className="rounded-lg border bg-card divide-y">
            {health?.services.map((svc) => (
              <div key={svc.name} className="flex items-center justify-between px-4 py-3">
                <div>
                  <p className="font-medium text-sm">{svc.name}</p>
                  {svc.details && <p className="text-xs text-muted-foreground">{svc.details}</p>}
                </div>
                <div className="flex items-center gap-3">
                  {svc.latency_ms !== null && (
                    <span className="text-xs text-muted-foreground">{svc.latency_ms}ms</span>
                  )}
                  <StatusBadge status={svc.status} />
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
