import { ACADEMIC_OPERATIONS_CANONICAL_REUSE_MAP } from '../constants';
import type { AcademicOperationsCanonicalReuseSummary } from '../types';

export function CanonicalReusePanel({ summary }: { summary?: AcademicOperationsCanonicalReuseSummary | null }) {
  const reuseMap = Object.entries(summary?.canonical_reuse_map ?? ACADEMIC_OPERATIONS_CANONICAL_REUSE_MAP);
  const trueNewModules = summary?.true_new_modules ?? [];

  return (
    <section className="rounded-lg border p-4" data-testid="academic-operations-canonical-reuse-panel">
      <h3 className="text-sm font-semibold">Canonical reuse / no duplicate modules</h3>
      <ul className="mt-3 space-y-2 text-sm">
        {reuseMap.map(([key, value]) => (
          <li key={key} className="flex items-center justify-between gap-3">
            <span>{key.replace(/_/g, ' ')}</span>
            <span className="font-medium text-muted-foreground">{value}</span>
          </li>
        ))}
      </ul>
      <p className="mt-3 text-sm text-muted-foreground">No duplicate module warning: capability rows in the 467-row matrix remain larger than the implemented package surface.</p>
      {trueNewModules.length ? (
        <div className="mt-3 text-sm text-muted-foreground">
          True-new metadata families: {trueNewModules.join(', ')}
        </div>
      ) : null}
    </section>
  );
}