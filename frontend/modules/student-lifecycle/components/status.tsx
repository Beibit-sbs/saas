import type { StudentLifecycleAuditEventResponse, StudentLifecycleEvidenceMetadataResponse } from '../types';

function humanize(value?: string | null) {
  if (!value) return 'Unknown';
  return value
    .toLowerCase()
    .replace(/_/g, ' ')
    .replace(/\b\w/g, (char) => char.toUpperCase());
}

function formatDate(value?: string | null) {
  if (!value) return 'Unavailable';
  try {
    return new Date(value).toLocaleString();
  } catch {
    return value;
  }
}

export function StudentLifecycleStatusBadge({ status }: { status?: string | null }) {
  return (
    <span className="inline-flex rounded-full border px-2.5 py-1 text-xs font-medium" data-testid="student-lifecycle-status-badge">
      {humanize(status)}
    </span>
  );
}

export function StudentLifecycleStatusTimeline({
  entries,
}: {
  entries: Array<{ id: number; previous_status?: string | null; new_status?: string | null; created_at: string; reason?: string | null; comment?: string | null }>;
}) {
  if (!entries.length) {
    return <p className="text-sm text-muted-foreground">No status history yet.</p>;
  }

  return (
    <ol className="space-y-3" data-testid="student-lifecycle-status-timeline">
      {entries.map((entry) => (
        <li key={entry.id} className="rounded-lg border p-3">
          <div className="flex flex-wrap items-center gap-2">
            <StudentLifecycleStatusBadge status={entry.previous_status} />
            <span className="text-xs text-muted-foreground">to</span>
            <StudentLifecycleStatusBadge status={entry.new_status} />
          </div>
          <p className="mt-2 text-xs text-muted-foreground">{formatDate(entry.created_at)}</p>
          {entry.reason || entry.comment ? <p className="mt-1 text-sm">{entry.reason ?? entry.comment}</p> : null}
        </li>
      ))}
    </ol>
  );
}

export function AuditTrailPanel({ events }: { events: StudentLifecycleAuditEventResponse[] }) {
  if (!events.length) {
    return <p className="text-sm text-muted-foreground">No audit events recorded yet.</p>;
  }

  return (
    <section className="rounded-lg border p-4" data-testid="student-lifecycle-audit-trail-panel">
      <h3 className="text-sm font-semibold">Audit-backed transitions</h3>
      <ul className="mt-3 space-y-3">
        {events.map((event) => (
          <li key={event.id} className="rounded-md border border-dashed p-3">
            <div className="flex flex-wrap items-center gap-2">
              <StudentLifecycleStatusBadge status={event.new_status} />
              <span className="text-sm font-medium">{humanize(event.event_type)}</span>
            </div>
            <p className="mt-2 text-sm text-muted-foreground">
              {event.entity_type} #{event.entity_id} · {formatDate(event.created_at)}
            </p>
            <p className="mt-1 text-sm">Action: {event.action}</p>
          </li>
        ))}
      </ul>
    </section>
  );
}

export function EvidenceMetadataPanel({ evidence }: { evidence: StudentLifecycleEvidenceMetadataResponse[] }) {
  if (!evidence.length) {
    return <p className="text-sm text-muted-foreground">No evidence metadata attached yet.</p>;
  }

  return (
    <section className="rounded-lg border p-4" data-testid="student-lifecycle-evidence-panel">
      <h3 className="text-sm font-semibold">Evidence metadata</h3>
      <ul className="mt-3 space-y-3">
        {evidence.map((item) => (
          <li key={item.id} className="rounded-md border border-dashed p-3">
            <p className="text-sm font-medium">{humanize(item.evidence_type)}</p>
            <p className="text-sm text-muted-foreground">Reference: {item.evidence_ref}</p>
            <p className="text-xs text-muted-foreground">Created {formatDate(item.created_at)}</p>
          </li>
        ))}
      </ul>
    </section>
  );
}