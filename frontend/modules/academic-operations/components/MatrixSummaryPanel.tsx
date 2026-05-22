import { MASTER_MATRIX_COMMIT, MASTER_MATRIX_ROW_COUNT } from '../constants';
import type { AcademicOperationsMatrixSummary } from '../types';

export function MatrixSummaryPanel({ summary }: { summary: AcademicOperationsMatrixSummary }) {
  return (
    <section className="rounded-lg border p-4" data-testid="academic-operations-matrix-summary-panel">
      <h3 className="text-sm font-semibold">Matrix summary</h3>
      <dl className="mt-3 grid gap-3 md:grid-cols-2">
        <div>
          <dt className="text-xs uppercase text-muted-foreground">Master matrix commit</dt>
          <dd className="text-sm font-medium">{summary.master_matrix_commit}</dd>
        </div>
        <div>
          <dt className="text-xs uppercase text-muted-foreground">Planning rows</dt>
          <dd className="text-sm font-medium">{summary.master_matrix_rows}</dd>
        </div>
        <div>
          <dt className="text-xs uppercase text-muted-foreground">Contract version</dt>
          <dd className="text-sm font-medium">{summary.contract_version}</dd>
        </div>
        <div>
          <dt className="text-xs uppercase text-muted-foreground">Target level</dt>
          <dd className="text-sm font-medium">{summary.target_level}</dd>
        </div>
      </dl>
      <p className="mt-3 text-sm text-muted-foreground">
        Canonical reuse is required, capability rows do not equal backend packages, and the runtime implements only a controlled subset of {MASTER_MATRIX_ROW_COUNT} rows from {MASTER_MATRIX_COMMIT}.
      </p>
    </section>
  );
}