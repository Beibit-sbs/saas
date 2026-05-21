import type { ReactNode } from 'react';
import { STUDENT_LIFECYCLE_BOUNDARY_LABELS } from '../constants';

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

export function StudentLifecycleBoundaryBanner({
  title = 'Student Lifecycle boundaries',
  description = 'Controlled frontend runtime only. Human-reviewed workflows and metadata-backed visibility.',
  labels = [
    STUDENT_LIFECYCLE_BOUNDARY_LABELS.humanReviewRequired,
    STUDENT_LIFECYCLE_BOUNDARY_LABELS.noAutomatedDecision,
    STUDENT_LIFECYCLE_BOUNDARY_LABELS.providerNotEnabled,
  ],
  children,
}: {
  title?: string;
  description?: string;
  labels?: string[];
  children?: ReactNode;
}) {
  return (
    <section className="rounded-lg border border-amber-200 bg-amber-50/60 p-4" data-testid="student-lifecycle-boundary-banner">
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

export function HumanReviewRequiredBadge() {
  return <BoundaryBadge label={STUDENT_LIFECYCLE_BOUNDARY_LABELS.humanReviewRequired} />;
}

export function NoAutomatedDecisionBadge() {
  return <BoundaryBadge label={STUDENT_LIFECYCLE_BOUNDARY_LABELS.noAutomatedDecision} />;
}

export function ProviderNotEnabledBadge() {
  return <BoundaryBadge label={STUDENT_LIFECYCLE_BOUNDARY_LABELS.providerNotEnabled} />;
}

export function UnofficialPreviewBadge() {
  return <BoundaryBadge label={STUDENT_LIFECYCLE_BOUNDARY_LABELS.unofficialPreview} />;
}

export function IncompleteDataNotice() {
  return <BoundaryBadge label={STUDENT_LIFECYCLE_BOUNDARY_LABELS.incompleteData} />;
}

export function SourceUnavailableNotice() {
  return <BoundaryBadge label={STUDENT_LIFECYCLE_BOUNDARY_LABELS.sourceUnavailable} />;
}

export function MetadataOnlyNotice() {
  return <BoundaryBadge label={STUDENT_LIFECYCLE_BOUNDARY_LABELS.metadataOnly} />;
}

export function NoHiddenScoreBadge() {
  return <BoundaryBadge label={STUDENT_LIFECYCLE_BOUNDARY_LABELS.noHiddenRiskScore} />;
}

export function SupportVisibilityOnlyBadge() {
  return <BoundaryBadge label={STUDENT_LIFECYCLE_BOUNDARY_LABELS.supportVisibilityOnly} />;
}

export function StudentLifecycleLimitationsPanel({ limitations }: { limitations?: string[] }) {
  if (!limitations?.length) {
    return (
      <div className="rounded-lg border border-dashed p-4 text-sm text-muted-foreground" data-testid="student-lifecycle-limitations-panel">
        No additional limitations were reported.
      </div>
    );
  }

  return (
    <section className="rounded-lg border p-4" data-testid="student-lifecycle-limitations-panel">
      <h3 className="text-sm font-semibold">Known limitations</h3>
      <ul className="mt-2 list-disc space-y-1 pl-5 text-sm text-muted-foreground">
        {limitations.map((limitation) => (
          <li key={limitation}>{limitation}</li>
        ))}
      </ul>
    </section>
  );
}