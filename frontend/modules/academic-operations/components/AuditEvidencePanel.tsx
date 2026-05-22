import { ACADEMIC_OPERATIONS_BOUNDARY_LABELS } from '../boundaryLabels';
import type { AcademicOperationsAuditEvent, AcademicOperationsEvidence } from '../types';

export function AuditEvidencePanel({ audit, evidence }: { audit: AcademicOperationsAuditEvent[]; evidence: AcademicOperationsEvidence[] }) {
  return (
    <div className="grid gap-4 lg:grid-cols-2" data-testid="audit-evidence-panel">
      <section className="rounded-lg border p-4">
        <h3 className="text-sm font-semibold">Audit events</h3>
        <p className="mt-1 text-sm text-muted-foreground">Metadata only. Human review remains explicit.</p>
        {audit.length ? (
          <ul className="mt-3 space-y-2 text-sm">
            {audit.map((event) => (
              <li key={event.id} className="rounded-md border p-3">
                <div className="font-medium">{event.event_type}</div>
                <div className="text-muted-foreground">{event.action} · {event.entity_type}</div>
              </li>
            ))}
          </ul>
        ) : (
          <p className="mt-2 text-sm text-muted-foreground">No audit metadata yet.</p>
        )}
      </section>

      <section className="rounded-lg border p-4">
        <h3 className="text-sm font-semibold">Evidence metadata</h3>
        <p className="mt-1 text-sm text-muted-foreground">{ACADEMIC_OPERATIONS_BOUNDARY_LABELS.noFakeEvidence}. {ACADEMIC_OPERATIONS_BOUNDARY_LABELS.noOfficialLegalDocumentClaim}.</p>
        {evidence.length ? (
          <ul className="mt-3 space-y-2 text-sm">
            {evidence.map((item) => (
              <li key={item.id} className="rounded-md border p-3">
                <div className="font-medium">{item.evidence_kind}</div>
                <div className="text-muted-foreground">{item.entity_type} · external ref {item.external_ref ?? 'n/a'}</div>
              </li>
            ))}
          </ul>
        ) : (
          <p className="mt-2 text-sm text-muted-foreground">No evidence metadata yet.</p>
        )}
      </section>
    </div>
  );
}