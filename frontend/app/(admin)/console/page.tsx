"use client";

import { MetricCard } from "@/shared/ui/metric-card";
import { PageHeader } from "@/shared/ui/page-header";
import { DataTable, Column } from "@/shared/ui/data-table";
import { StatusBadge } from "@/shared/ui/status-badge";
import { ErrorState } from "@/shared/ui/error-state";
import { useMetrics, useHealthStatus } from "@/modules/platform/health/hooks";
import { useJobs } from "@/modules/platform/jobs/hooks";
import { useNotifications } from "@/modules/platform/notifications/hooks";
import { Job } from "@/modules/platform/jobs/types";
import { Notification } from "@/modules/platform/notifications/types";
import { formatRelative } from "@/shared/utils/format";
import { Building2, Users, Activity, AlertCircle, LayoutDashboard } from "lucide-react";

const jobColumns: Column<Job>[] = [
  { key: "type", header: "Type", cell: (r) => r.job_type },
  { key: "tenant", header: "Tenant", cell: (r) => r.tenant_id ?? "global" },
  { key: "status", header: "Status", cell: (r) => <StatusBadge status={r.status} /> },
  { key: "created", header: "Created", cell: (r) => formatRelative(r.created_at) },
];

const notifColumns: Column<Notification>[] = [
  { key: "title", header: "Title", cell: (r) => r.title },
  { key: "severity", header: "Severity", cell: (r) => <StatusBadge status={r.severity} /> },
  { key: "created", header: "When", cell: (r) => formatRelative(r.created_at) },
];

export default function DashboardPage() {
  const { data: metrics, isLoading: metricsLoading, error: metricsError, refetch: refetchMetrics } = useMetrics();
  const { data: health } = useHealthStatus();
  const { data: jobsData, isLoading: jobsLoading } = useJobs({ page_size: 5 });
  const { data: notifsData, isLoading: notifsLoading } = useNotifications({ page_size: 5, read: false });

  if (metricsError) {
    return <ErrorState title="Failed to load dashboard" onRetry={refetchMetrics} />;
  }

  return (
    <div className="space-y-6">
      <PageHeader title="Dashboard" description="Platform overview" icon={LayoutDashboard} />

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <MetricCard
          label="Total Tenants"
          value={metrics?.total_tenants}
          icon={Building2}
          loading={metricsLoading}
        />
        <MetricCard
          label="Active Tenants"
          value={metrics?.active_tenants}
          icon={Building2}
          loading={metricsLoading}
        />
        <MetricCard
          label="Total Students"
          value={metrics?.total_students}
          icon={Users}
          loading={metricsLoading}
        />
        <MetricCard
          label="Platform Health"
          value={health?.status ?? "—"}
          icon={Activity}
          description={`${health?.services.length ?? 0} services checked`}
          loading={!health}
        />
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <div className="space-y-2">
          <h2 className="text-sm font-medium">Recent Jobs</h2>
          <DataTable
            columns={jobColumns}
            data={jobsData?.items ?? []}
            isLoading={jobsLoading}
            getRowKey={(r) => r.id}
            emptyTitle="No recent jobs"
          />
        </div>
        <div className="space-y-2">
          <h2 className="text-sm font-medium">Unread Notifications</h2>
          <DataTable
            columns={notifColumns}
            data={notifsData?.items ?? []}
            isLoading={notifsLoading}
            getRowKey={(r) => r.id}
            emptyTitle="No unread notifications"
          />
        </div>
      </div>
    </div>
  );
}
