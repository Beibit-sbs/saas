import type { ReactNode } from 'react';
import { ACADEMIC_OPERATIONS_BOUNDARY_LABELS } from '../boundaryLabels';

function slugify(value: string) {
  return value.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');
}

function BoundaryBadge({ label }: { label: string }) {
  return (
    <span
      className="inline-flex items-center rounded-full border border-amber-200 bg-amber-50 px-2.5 py-1 text-xs font-medium text-amber-900"
      data-testid={`${slugify(label)}-label`}
    >
      {label}
    </span>
  );
}

export function BoundaryBanner({
  title = 'Academic Operations boundaries',
  description = 'Metadata-only frontend runtime. Canonical-aware, bridge-first, and read-only-first by default.',
  labels = [
    ACADEMIC_OPERATIONS_BOUNDARY_LABELS.metadataOnlyFoundation,
    ACADEMIC_OPERATIONS_BOUNDARY_LABELS.noOfficialGradePublication,
    ACADEMIC_OPERATIONS_BOUNDARY_LABELS.noProviderSync,
  ],
  children,
}: {
  title?: string;
  description?: string;
  labels?: string[];
  children?: ReactNode;
}) {
  return (
    <section className="rounded-lg border border-amber-200 bg-amber-50/60 p-4" data-testid="academic-operations-boundary-banner">
      <div className="space-y-1">
        <h2 className="text-sm font-semibold text-amber-950">{title}</h2>
        <p className="text-sm text-amber-900">{description}</p>
      </div>
      <div className="mt-3 flex flex-wrap gap-2">
        {labels.map((label) => (
          <BoundaryBadge key={label} label={label} />
        ))}
      </div>
      {children ? <div className="mt-3">{children}</div> : null}
    </section>
  );
}

export function AcademicOperationsBoundaryBadge({ label }: { label: string }) {
  return <BoundaryBadge label={label} />;
}