import { ACADEMIC_OPERATIONS_LIMITATIONS } from '../constants';

export function LimitationsPanel({ limitations = ACADEMIC_OPERATIONS_LIMITATIONS }: { limitations?: readonly string[] | string[] }) {
  if (!limitations.length) {
    return (
      <div className="rounded-lg border border-dashed p-4 text-sm text-muted-foreground" data-testid="academic-operations-limitations-panel">
        No additional limitations were reported.
      </div>
    );
  }

  return (
    <section className="rounded-lg border p-4" data-testid="academic-operations-limitations-panel">
      <h3 className="text-sm font-semibold">Known limitations</h3>
      <ul className="mt-2 list-disc space-y-1 pl-5 text-sm text-muted-foreground">
        {limitations.map((limitation) => (
          <li key={limitation}>{limitation}</li>
        ))}
      </ul>
    </section>
  );
}