import { ACADEMIC_OPERATIONS_BOUNDARY_LABELS, ACADEMIC_OPERATIONS_BOUNDARY_COPY } from '../boundaryLabels';
import type { BridgeSummary, CanonicalModuleBridge } from '../types';

function BridgeGroup({ title, items }: { title: string; items: Array<CanonicalModuleBridge | BridgeSummary> }) {
  return (
    <section className="rounded-lg border p-4">
      <h3 className="text-sm font-semibold">{title}</h3>
      {items.length ? (
        <ul className="mt-3 space-y-2 text-sm">
          {items.map((item) => (
            <li key={`${title}-${item.id}`} className="rounded-md border p-3">
              <div className="font-medium">{'bridge_type' in item ? item.bridge_type : item.bridge_key}</div>
              <div className="text-muted-foreground">canonical ref {'canonical_module_ref' in item ? item.canonical_module_ref : item.external_ref ?? item.student_ref ?? 'n/a'}</div>
            </li>
          ))}
        </ul>
      ) : (
        <p className="mt-2 text-sm text-muted-foreground">No bridge metadata yet.</p>
      )}
    </section>
  );
}

export function BridgeMetadataPanel({
  bridges,
  studentLifecycle,
  documentWorkflow,
  executiveGovernance,
  qualityAccreditation,
}: {
  bridges: CanonicalModuleBridge[];
  studentLifecycle: BridgeSummary[];
  documentWorkflow: BridgeSummary[];
  executiveGovernance: BridgeSummary[];
  qualityAccreditation: BridgeSummary[];
}) {
  return (
    <div className="space-y-4" data-testid="bridge-metadata-panel">
      <div className="flex flex-wrap gap-2">
        {[ACADEMIC_OPERATIONS_BOUNDARY_LABELS.canonicalReuse, ACADEMIC_OPERATIONS_BOUNDARY_LABELS.readOnlyFirstBridge, ACADEMIC_OPERATIONS_BOUNDARY_LABELS.bridgesPage].map((label) => (
          <span key={label} className="rounded-full border border-amber-200 bg-amber-50 px-2.5 py-1 text-xs font-medium text-amber-900">
            {label}
          </span>
        ))}
      </div>
      <BridgeGroup title="Canonical bridge registry" items={bridges} />
      <div className="grid gap-4 lg:grid-cols-2">
        <BridgeGroup title="Student lifecycle bridge" items={studentLifecycle} />
        <BridgeGroup title="Document workflow bridge" items={documentWorkflow} />
        <BridgeGroup title="Executive governance bridge" items={executiveGovernance} />
        <BridgeGroup title="Quality accreditation bridge" items={qualityAccreditation} />
      </div>
      <p className="text-sm text-muted-foreground">{ACADEMIC_OPERATIONS_BOUNDARY_COPY[2]}. Mutation remains disabled by default.</p>
    </div>
  );
}