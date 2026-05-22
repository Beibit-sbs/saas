import { ACADEMIC_OPERATIONS_BOUNDARY_LABELS } from '../boundaryLabels';
import type { GradebookMetadata } from '../types';

export function GradebookMetadataRegistry({ items }: { items: GradebookMetadata[] }) {
  return (
    <section className="rounded-lg border p-4" data-testid="gradebook-metadata-registry">
      <h3 className="text-sm font-semibold">Gradebook metadata</h3>
      <p className="mt-1 text-sm text-muted-foreground">No official grade publication.</p>
      <p className="mt-1 text-sm text-muted-foreground">{ACADEMIC_OPERATIONS_BOUNDARY_LABELS.gradebookPage}</p>
      {items.length ? (
        <ul className="mt-3 space-y-2 text-sm">
          {items.map((item) => (
            <li key={item.id} className="rounded-md border p-3">
              <div className="font-medium">{item.gradebook_key}</div>
              <div className="text-muted-foreground">course ref {item.course_ref ?? 'n/a'} · status {item.status}</div>
            </li>
          ))}
        </ul>
      ) : (
        <p className="mt-2 text-sm text-muted-foreground">No gradebook metadata yet.</p>
      )}
    </section>
  );
}