import type { Cohort } from '../types';

export function CohortsRegistry({ cohorts }: { cohorts: Cohort[] }) {
  return (
    <section className="rounded-lg border p-4" data-testid="cohorts-registry">
      <h3 className="text-sm font-semibold">Cohort metadata</h3>
      {cohorts.length ? (
        <ul className="mt-3 space-y-2 text-sm">
          {cohorts.map((cohort) => (
            <li key={cohort.id} className="rounded-md border p-3">
              <div className="font-medium">{cohort.cohort_name}</div>
              <div className="text-muted-foreground">{cohort.cohort_code} · group ref {cohort.academic_group_ref ?? 'n/a'}</div>
            </li>
          ))}
        </ul>
      ) : (
        <p className="mt-2 text-sm text-muted-foreground">No cohort metadata yet.</p>
      )}
    </section>
  );
}