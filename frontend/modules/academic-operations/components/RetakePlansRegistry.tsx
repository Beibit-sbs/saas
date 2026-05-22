import { ACADEMIC_OPERATIONS_BOUNDARY_LABELS } from '../boundaryLabels';
import type { RetakePlan } from '../types';

export function RetakePlansRegistry({ items }: { items: RetakePlan[] }) {
  return (
    <section className="rounded-lg border p-4" data-testid="retake-plans-registry">
      <h3 className="text-sm font-semibold">Retake plans</h3>
      <p className="mt-1 text-sm text-muted-foreground">{ACADEMIC_OPERATIONS_BOUNDARY_LABELS.retakesPage}</p>
      {items.length ? (
        <ul className="mt-3 space-y-2 text-sm">
          {items.map((item) => (
            <li key={item.id} className="rounded-md border p-3">
              <div className="font-medium">{item.plan_code}</div>
              <div className="text-muted-foreground">retake window {item.retake_window ?? 'n/a'} · course ref {item.course_ref ?? 'n/a'}</div>
            </li>
          ))}
        </ul>
      ) : (
        <p className="mt-2 text-sm text-muted-foreground">No retake metadata yet.</p>
      )}
    </section>
  );
}