"use client";

import { useMemo } from "react";
import { Button } from "@/shared/ui/button";
import { EmptyState } from "@/shared/ui/empty-state";
import { ErrorState } from "@/shared/ui/error-state";
import { PageHeader } from "@/shared/ui/page-header";
import { RequirePermission } from "@/shared/ui/permission-gate";
import { Skeleton } from "@/shared/ui/skeleton";
import { formatDate, formatRelative } from "@/shared/utils/format";
import { PERMISSIONS } from "@/shared/config/permissions";
import { LayoutDashboard, RefreshCw } from "lucide-react";
import { KpiCard } from "@/modules/platform/kpi/kpi-card";
import { useRectorDashboard } from "@/modules/platform/kpi/use-dashboard";

function DashboardSkeletonGrid() {
  return (
    <div className="grid gap-4 grid-cols-1 md:grid-cols-2 xl:grid-cols-3" data-testid="kpi-loading-grid">
      {Array.from({ length: 6 }).map((_, idx) => (
        <div key={idx} className="rounded-lg border bg-card p-6">
          <Skeleton className="h-4 w-40" />
          <Skeleton className="mt-3 h-8 w-24" />
          <Skeleton className="mt-4 h-8 w-full" />
        </div>
      ))}
    </div>
  );
}

export default function RectorDashboardPage() {
  const tenantId = 1;
  const { data, isLoading, isError, refetch } = useRectorDashboard(tenantId);

  const generatedLabel = useMemo(() => {
    if (!data?.generated_at) return "n/a";
    return formatRelative(data.generated_at);
  }, [data?.generated_at]);

  return (
    <RequirePermission
      permission={PERMISSIONS.METRICS_READ}
      message="You need metrics.read permission to access the executive dashboard."
    >
      <div className="space-y-6" data-testid="rector-dashboard-page">
        <PageHeader
          title="University Executive Dashboard"
          description={`Snapshot: ${data?.snapshot_date ? formatDate(data.snapshot_date) : "—"} | Generated: ${generatedLabel}`}
          icon={LayoutDashboard}
          actions={
            <Button
              variant="outline"
              size="sm"
              onClick={() => {
                void refetch();
              }}
              disabled={isLoading}
            >
              <RefreshCw className="mr-2 h-4 w-4" />
              Refresh
            </Button>
          }
        />

        <div className="rounded-lg border bg-card p-4 text-sm text-muted-foreground" data-testid="dashboard-meta">
          <p>Tenant: {data?.tenant_id ?? tenantId}</p>
          <p>Snapshot Date: {data?.snapshot_date ?? "—"}</p>
          <p>Generated At: {data?.generated_at ?? "—"}</p>
        </div>

        {isLoading && <DashboardSkeletonGrid />}

        {isError && !isLoading && (
          <ErrorState
            title="Failed to load executive dashboard"
            message="KPI data is temporarily unavailable."
            onRetry={() => {
              void refetch();
            }}
          />
        )}

        {!isLoading && !isError && (!data || data.cards.length === 0) && (
          <EmptyState
            title="No KPI data yet"
            description="No dashboard cards are available for the selected tenant snapshot."
            action={
              <Button
                variant="outline"
                onClick={() => {
                  void refetch();
                }}
              >
                Retry
              </Button>
            }
          />
        )}

        {!isLoading && !isError && data && data.cards.length > 0 && (
          <div className="grid gap-4 grid-cols-1 md:grid-cols-2 xl:grid-cols-3" data-testid="kpi-cards-grid">
            {data.cards.map((card) => (
              <KpiCard
                key={card.metric_key}
                title={card.title}
                value={card.value}
                trendPoints={card.trend_7d}
              />
            ))}
          </div>
        )}
      </div>
    </RequirePermission>
  );
}
