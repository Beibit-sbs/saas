import type { AcademicOperationsCanonicalReuseSummary, AcademicOperationsDashboard as AcademicOperationsDashboardType, AcademicOperationsHealth, AcademicOperationsMatrixSummary } from '../types';
import { CanonicalReusePanel } from './CanonicalReusePanel';
import { AcademicOperationsCountsPanel } from './AcademicOperationsCountsPanel';
import { AcademicOperationsHealthPanel } from './AcademicOperationsHealthPanel';
import { LimitationsPanel } from './LimitationsPanel';
import { MatrixSummaryPanel } from './MatrixSummaryPanel';

function totalCount(values: Record<string, number>) {
  return Object.values(values).reduce((sum, value) => sum + value, 0);
}

function MetricCard({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-lg border p-4">
      <p className="text-sm text-muted-foreground">{label}</p>
      <p className="mt-2 text-2xl font-semibold">{value}</p>
    </div>
  );
}

export function AcademicOperationsDashboard({
  dashboard,
  health,
  matrixSummary,
  canonicalReuseSummary,
}: {
  dashboard: AcademicOperationsDashboardType;
  health: AcademicOperationsHealth;
  matrixSummary: AcademicOperationsMatrixSummary;
  canonicalReuseSummary?: AcademicOperationsCanonicalReuseSummary | null;
}) {
  return (
    <div className="space-y-6" data-testid="academic-operations-dashboard">
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <MetricCard label="Tracked metadata records" value={totalCount(dashboard.counts)} />
        <MetricCard label="Canonical bridge references" value={totalCount(dashboard.canonical_bridge_counts)} />
        <MetricCard label="Planning rows" value={dashboard.master_matrix_rows} />
        <MetricCard label="Human review required" value={dashboard.incomplete_data ? 1 : 0} />
      </div>

      <div className="grid gap-4 xl:grid-cols-2">
        <AcademicOperationsCountsPanel title="Module counts" counts={dashboard.counts} testId="academic-operations-module-counts" />
        <AcademicOperationsCountsPanel title="Bridge counts" counts={dashboard.canonical_bridge_counts} testId="academic-operations-bridge-counts" />
      </div>

      <div className="grid gap-4 xl:grid-cols-2">
        <AcademicOperationsHealthPanel health={health} />
        <MatrixSummaryPanel summary={matrixSummary} />
      </div>

      <CanonicalReusePanel summary={canonicalReuseSummary} />
      <LimitationsPanel limitations={dashboard.limitations} />
    </div>
  );
}