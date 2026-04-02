"use client";

import { PageHeader } from "@/shared/ui/page-header";
import { MetricCard } from "@/shared/ui/metric-card";
import { StatusBadge } from "@/shared/ui/status-badge";
import { Skeleton } from "@/shared/ui/skeleton";
import { ErrorState } from "@/shared/ui/error-state";
import { AccessDenied } from "@/shared/ui/permission-gate";
import { usePermissions } from "@/shared/hooks/use-permissions";
import { PERMISSIONS } from "@/shared/config/permissions";
import { useHealthStatus, useMetrics } from "@/modules/platform/health/hooks";
import { useLanguage } from "@/app/components/LanguageProvider";
import { Activity, Zap, Clock, AlertCircle } from "lucide-react";

type ServiceRow = {
  name: string;
  status: string;
  latency_ms: number | null;
  details: string | null;
};

export default function HealthPage() {
  const { t } = useLanguage();
  const { hasPermission } = usePermissions();
  const { data: health, isLoading: healthLoading, error, refetch } = useHealthStatus();
  const { data: metrics, isLoading: metricsLoading } = useMetrics();

  const services: ServiceRow[] = Array.isArray(health?.services)
    ? health.services
    : health
      ? [
        {
          name: String(health.service ?? "api"),
          status: String(health.status ?? "unknown"),
          latency_ms: null,
          details: null,
        },
      ]
      : [];

  if (!hasPermission(PERMISSIONS.HEALTH_READ)) return <AccessDenied />;
  if (error) return <ErrorState title="Failed to load health data" onRetry={refetch} />;

  return (
    <div className="space-y-6">
      <PageHeader title={t("nav.healthMetrics")} description={t("console.health.description")} icon={Activity} />

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <MetricCard
          label="API Requests (1h)"
          value={metrics?.api_requests_1h}
          icon={Zap}
          loading={metricsLoading}
        />
        <MetricCard
          label="Avg Response"
          value={metrics?.avg_response_ms != null ? `${metrics.avg_response_ms}ms` : undefined}
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
        ) : services.length === 0 ? (
          <div className="rounded-lg border bg-card px-4 py-6 text-sm text-muted-foreground">
            No service health details are available.
          </div>
        ) : (
          <div className="rounded-lg border bg-card divide-y">
            {services.map((svc) => (
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
