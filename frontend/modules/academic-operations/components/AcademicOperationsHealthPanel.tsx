import { ACADEMIC_OPERATIONS_BACKEND_ROUTE_COUNT, MASTER_MATRIX_ROW_COUNT } from '../constants';
import type { AcademicOperationsHealth } from '../types';
import { AcademicOperationsBoundaryBadge } from './BoundaryBanner';

export function AcademicOperationsHealthPanel({ health }: { health: AcademicOperationsHealth }) {
  return (
    <section className="rounded-lg border p-4" data-testid="academic-operations-health-panel">
      <h3 className="text-sm font-semibold">Module health</h3>
      <div className="mt-3 flex flex-wrap gap-2">
        <AcademicOperationsBoundaryBadge label={`fake_metrics=${String(health.fake_metrics)}`} />
        <AcademicOperationsBoundaryBadge label={`route_count=${health.route_count}`} />
        <AcademicOperationsBoundaryBadge label={`table_count=${health.table_count}`} />
        <AcademicOperationsBoundaryBadge label={`matrix_rows=${MASTER_MATRIX_ROW_COUNT}`} />
      </div>
      <p className="mt-3 text-sm text-muted-foreground">
        Foundation status {health.foundation_status} with {health.route_count} routes against backend target {ACADEMIC_OPERATIONS_BACKEND_ROUTE_COUNT}.
      </p>
    </section>
  );
}