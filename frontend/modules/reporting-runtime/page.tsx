'use client';

import { useQuery } from '@tanstack/react-query';

import { reportingRuntimeApi } from './api';
import { PERMISSIONS } from '@/shared/config/permissions';
import { RequirePermission } from '@/shared/ui/permission-gate';
import { ErrorState, LoadingState } from '@/shared/ui/page-states';

function MetricCard({ label, value, helper }: { label: string; value: string | number; helper?: string }) {
  return (
    <div className="rounded-lg border p-4">
      <p className="text-sm text-muted-foreground">{label}</p>
      <p className="mt-2 text-2xl font-semibold">{value}</p>
      {helper ? <p className="mt-1 text-xs text-muted-foreground">{helper}</p> : null}
    </div>
  );
}

export function ReportingRuntimeShellPage() {
  const runtime = useQuery({
    queryKey: ['reporting-runtime:shell'],
    queryFn: reportingRuntimeApi.getRuntimeShell,
    staleTime: 30000,
  });

  if (runtime.isPending) {
    return <LoadingState title="Loading Reporting Runtime shell" />;
  }

  if (runtime.error) {
    return <ErrorState message="Failed to load Reporting Runtime shell." error={runtime.error} />;
  }

  if (!runtime.data) {
    return <ErrorState message="Reporting Runtime shell is unavailable." />;
  }

  return (
    <RequirePermission permission={PERMISSIONS.REPORTING_RUNTIME_SUMMARY_READ}>
      <div className="space-y-6" data-testid="reporting-runtime-shell">
        <header className="space-y-2">
          <h1 className="text-2xl font-semibold">Reporting Runtime Shell</h1>
          <p className="text-sm text-muted-foreground">
            Read-only runtime shell for Ministry and Regulatory Reporting Brain. No provider synchronization and no submission execution.
          </p>
        </header>

        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          <MetricCard label="Reporting Cycles" value={runtime.data.active_reporting_cycles} helper="Reporting lifecycle overview" />
          <MetricCard label="Active Submissions" value={runtime.data.active_submissions} helper="Read-only submission state" />
          <MetricCard label="Active Deadlines" value={runtime.data.active_deadlines} helper="Deadline monitoring" />
          <MetricCard label="Compliance Score" value={runtime.data.compliance_score} helper={`Risk band: ${runtime.data.compliance.risk_band}`} />
        </div>

        <section className="rounded-lg border p-4" data-testid="reporting-overview-section">
          <h2 className="text-lg font-semibold">Reporting Overview</h2>
          <p className="mt-1 text-sm text-muted-foreground">
            {runtime.data.overview.reporting_center_name} owned by {runtime.data.overview.owner_module}
          </p>
        </section>

        <section className="rounded-lg border p-4" data-testid="provider-readiness-section">
          <h2 className="text-lg font-semibold">Provider Readiness</h2>
          <p className="mt-1 text-sm text-muted-foreground">
            Owner: {runtime.data.provider_readiness.owner_module} | Status: {runtime.data.provider_readiness.provider_readiness}
          </p>
          <p className="mt-1 text-sm">
            NOT_CONNECTED={runtime.data.provider_readiness.provider_status_counts.NOT_CONNECTED ?? 0}, READY={runtime.data.provider_readiness.provider_status_counts.READY ?? 0}, PENDING={runtime.data.provider_readiness.provider_status_counts.PENDING ?? 0}
          </p>
        </section>

        <section className="rounded-lg border p-4" data-testid="compliance-summary-section">
          <h2 className="text-lg font-semibold">Compliance Summary</h2>
          <p className="mt-1 text-sm text-muted-foreground">Risk band: {runtime.data.compliance.risk_band}</p>
          <p className="mt-1 text-sm">Compliance score: {runtime.data.compliance.compliance_score}</p>
        </section>

        <section className="rounded-lg border p-4" data-testid="reporting-deadlines-section">
          <h2 className="text-lg font-semibold">Reporting Deadlines</h2>
          <p className="mt-1 text-sm">Overdue: {runtime.data.deadlines.overdue_deadlines} | Upcoming: {runtime.data.deadlines.upcoming_deadlines}</p>
        </section>

        <section className="rounded-lg border p-4" data-testid="reporting-status-section">
          <h2 className="text-lg font-semibold">Reporting Status</h2>
          <p className="mt-1 text-sm">Open: {runtime.data.reporting_status.open_items}</p>
          <p className="text-sm">In review: {runtime.data.reporting_status.in_review_items}</p>
          <p className="text-sm">Blocked: {runtime.data.reporting_status.blocked_items}</p>
          <p className="mt-2 text-xs text-muted-foreground">
            read_only={String(runtime.data.read_only)} | auditability_preserved={String(runtime.data.auditability_preserved)}
          </p>
        </section>
      </div>
    </RequirePermission>
  );
}
