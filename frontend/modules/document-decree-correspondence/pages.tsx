'use client';

import Link from 'next/link';
import { useState, type ReactNode } from 'react';
import { RequirePermission } from '@/shared/ui/permission-gate';
import {
  AuditTrailPanel,
  DataTableShell,
  DateRangeFilter,
  EmptyState,
  EvidenceUploadPanel,
  ExportButton,
  FilterBar,
  PageActionBar,
  PageActions,
  PageShell,
  PageToolbar,
  PermissionDeniedState,
  SearchInput,
  SectionHeader,
  StatusFilter,
} from '@/shared/ui-framework';
import {
  automaticDecreeApprovalEnabled,
  automaticDocumentSigningEnabled,
  automaticRectorDecisionEnabled,
  DOCUMENT_DECREE_CORRESPONDENCE_BACKEND_ROUTE_COUNT,
  DOCUMENT_DECREE_CORRESPONDENCE_DASHBOARD_WIDGETS,
  DOCUMENT_DECREE_CORRESPONDENCE_DATA_SOURCE,
  DOCUMENT_DECREE_CORRESPONDENCE_NAV_ITEMS,
  DOCUMENT_DECREE_CORRESPONDENCE_PERMISSION_COUNT,
  DOCUMENT_DECREE_CORRESPONDENCE_ROUTES,
  DOCUMENT_DECREE_CORRESPONDENCE_RUNTIME_MODE,
  DOCUMENT_DECREE_CORRESPONDENCE_SAFETY_FLAGS,
  DOCUMENT_DECREE_CORRESPONDENCE_WORKFLOWS,
  externalSubmissionEnabled,
  fakeArchiveLegalRecord,
  fakeDecrees,
  fakeDeliveryConfirmations,
  fakeDocuments,
  fakeSignatures,
  hiddenScorePresent,
  humanReviewRequired,
  officialLegalEffect,
} from './constants';
import {
  DOCUMENT_DECREE_CORRESPONDENCE_BOUNDARY_COPY,
  DOCUMENT_DECREE_CORRESPONDENCE_BOUNDARY_LABELS,
  DOCUMENT_DECREE_CORRESPONDENCE_FORBIDDEN_LABELS,
} from './boundaryLabels';
import { hasDdcPermission } from './guards';
import type {
  DdcDashboardWidget,
  DdcRouteDefinition,
  DdcRouteKey,
  DdcWorkflowDefinition,
} from './types';

interface DdcPageModel {
  route: DdcRouteDefinition;
  primaryWidgets: DdcDashboardWidget[];
  workflows: DdcWorkflowDefinition[];
  emptyState: string;
  incompleteDataMessage: string;
  noOverclaimAssertions: string[];
}

type DdcRegistryRow = {
  key: string;
  surface: string;
  visibility: string;
  endpoints: string[];
  limitation: string;
};

function slugify(value: string) {
  return value.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');
}

function buildDdcRegistryRows(model: DdcPageModel): DdcRegistryRow[] {
  const widgetRows = model.primaryWidgets.map((widget) => ({
    key: widget.key,
    surface: widget.title,
    visibility: 'Lifecycle visibility',
    endpoints: widget.endpointRefs,
    limitation: widget.forbiddenAction,
  }));

  if (widgetRows.length > 0) {
    return widgetRows;
  }

  return model.route.backendEndpoints.map((endpoint, index) => ({
    key: `${model.route.key}-${index}`,
    surface: `${model.route.title} contract ${index + 1}`,
    visibility: 'Metadata only',
    endpoints: [endpoint],
    limitation: model.emptyState,
  }));
}

function buildDdcAuditEvents(model: DdcPageModel) {
  const workflows = model.workflows.length > 0 ? model.workflows : DOCUMENT_DECREE_CORRESPONDENCE_WORKFLOWS.slice(0, 2);
  return workflows.map((workflow, index) => ({
    id: workflow.key,
    actor: 'Human review',
    timestamp: `contract-step-${index + 1}`,
    status: 'metadata_only',
    event: workflow.title,
    metadata: {
      routeCount: workflow.routeKeys.length,
      endpointCount: workflow.endpointRefs.length,
      review: workflow.humanReviewPoint,
    },
  }));
}

function DdcRegistryTable({ rows }: { rows: DdcRegistryRow[] }) {
  return (
    <table className="w-full text-left text-sm" data-testid="ddc-registry-table">
      <thead>
        <tr className="border-b text-xs uppercase tracking-wide text-muted-foreground">
          <th className="px-4 py-3 font-medium">Surface</th>
          <th className="px-4 py-3 font-medium">Visibility</th>
          <th className="px-4 py-3 font-medium">Endpoints</th>
          <th className="px-4 py-3 font-medium">Limitation</th>
        </tr>
      </thead>
      <tbody>
        {rows.map((row) => (
          <tr key={row.key} className="border-b align-top last:border-0">
            <td className="px-4 py-3 font-medium">{row.surface}</td>
            <td className="px-4 py-3 text-muted-foreground">{row.visibility}</td>
            <td className="px-4 py-3 text-xs text-muted-foreground">
              {row.endpoints.map((endpoint) => (
                <div key={endpoint}>{endpoint}</div>
              ))}
            </td>
            <td className="px-4 py-3 text-muted-foreground">{row.limitation}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

function DdcStateGallery() {
  return (
    <section className="grid gap-4 xl:grid-cols-2" data-testid="ddc-state-gallery">
      <EmptyState variant="no_data" title="No document lifecycle data" description="No document, decree, or correspondence rows are available for the selected route contract." />
      <EmptyState variant="no_results" title="No matching lifecycle results" description="Shared search and status filters can narrow document visibility without enabling fake actions." />
      <EmptyState variant="metadata_only" title="Metadata-only document visibility" description="Read-only lifecycle and evidence surfaces remain visible while execution stays disabled." limitation="No fake signing, approval, or legal-effect transition is exposed." />
      <EmptyState variant="future_scope" title="Future-scope document execution" description="Live signing, decree approval, and external delivery execution remain outside A-044.R6." />
    </section>
  );
}

export function DdcBoundaryBanner({ labels }: { labels: string[] }) {
  return (
    <section className="rounded-xl border border-amber-200 bg-amber-50 p-4" data-testid="ddc-boundary-banner">
      <div className="flex flex-wrap gap-2">
        {labels.map((label) => (
          <span key={label} data-testid={`ddc-boundary-${slugify(label)}`} className="inline-flex rounded-full border border-amber-300 px-3 py-1 text-xs font-medium text-amber-950">
            {label}
          </span>
        ))}
      </div>
    </section>
  );
}

export function DdcReadinessCard({ title, items }: { title: string; items: string[] }) {
  return (
    <section className="rounded-xl border bg-card p-4" data-testid={`ddc-readiness-${slugify(title)}`}>
      <h3 className="text-sm font-semibold">{title}</h3>
      <ul className="mt-3 space-y-2 text-sm text-muted-foreground">
        {items.map((item) => (
          <li key={item}>{item}</li>
        ))}
      </ul>
    </section>
  );
}

export function DdcMetricCard({ label, value, helperText }: { label: string; value: string; helperText: string }) {
  return (
    <article className="rounded-xl border bg-card p-4" data-testid={`ddc-metric-${slugify(label)}`}>
      <div className="text-xs uppercase tracking-wide text-muted-foreground">{label}</div>
      <div className="mt-2 text-2xl font-semibold">{value}</div>
      <p className="mt-2 text-sm text-muted-foreground">{helperText}</p>
    </article>
  );
}

export function DdcDashboardGrid({ widgets }: { widgets: DdcDashboardWidget[] }) {
  return (
    <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-3" data-testid="ddc-dashboard-grid">
      {widgets.map((widget) => (
        <article key={widget.key} className="rounded-xl border bg-card p-4" data-testid={`ddc-widget-${widget.key}`}>
          <div className="flex items-start justify-between gap-3">
            <div>
              <h3 className="text-base font-semibold">{widget.title}</h3>
              <p className="mt-1 text-sm text-muted-foreground">{widget.description}</p>
            </div>
            <DdcEvidenceStatusBadge status="metadata-only" />
          </div>
          <ul className="mt-3 space-y-1 text-sm text-muted-foreground">
            {widget.endpointRefs.map((endpoint) => (
              <li key={endpoint}>{endpoint}</li>
            ))}
          </ul>
          <div className="mt-3 flex flex-wrap gap-2">
            {widget.boundaryLabels.map((label) => (
              <span key={label} className="rounded-full border px-2 py-1 text-xs">{label}</span>
            ))}
          </div>
          <p className="mt-3 text-xs text-muted-foreground">{widget.forbiddenAction}</p>
          <Link href={widget.drilldownPath} className="mt-4 inline-flex text-sm font-medium text-primary underline-offset-4 hover:underline">
            Open drilldown
          </Link>
        </article>
      ))}
    </section>
  );
}

export function DdcEvidenceStatusBadge({ status }: { status: string }) {
  return <span className="rounded-full border border-slate-300 px-2 py-1 text-xs font-medium">{status}</span>;
}

export function DdcHumanReviewBadge() {
  return <span className="rounded-full border border-blue-300 bg-blue-50 px-2 py-1 text-xs font-medium text-blue-900" data-testid="ddc-human-review-badge">Human review required</span>;
}

export function DdcSignatureReadinessBadge() {
  return <span className="rounded-full border border-slate-300 px-2 py-1 text-xs font-medium" data-testid="ddc-signature-readiness-badge">automaticDocumentSigningEnabled=false</span>;
}

export function DdcDeliveryReadinessBadge() {
  return <span className="rounded-full border border-slate-300 px-2 py-1 text-xs font-medium" data-testid="ddc-delivery-readiness-badge">externalSubmissionEnabled=false</span>;
}

export function DdcArchiveReadinessBadge() {
  return <span className="rounded-full border border-slate-300 px-2 py-1 text-xs font-medium" data-testid="ddc-archive-readiness-badge">officialLegalEffect=false</span>;
}

export function DdcIncompleteDataNotice() {
  return (
    <div className="rounded-xl border border-dashed p-4 text-sm text-muted-foreground" data-testid="ddc-incomplete-data-notice">
      incompleteData=true. The runtime keeps incomplete metadata visible instead of masking gaps.
    </div>
  );
}

export function DdcPermissionDeniedPanel({ permission }: { permission: string }) {
  return (
    <div data-testid="ddc-permission-denied-panel">
      <PermissionDeniedState role="tenant_admin" requiredPermission={permission} reason="This document/decree/correspondence view is fail-closed for the current permission set." />
    </div>
  );
}

export function DdcLimitationsPanel({ limitations }: { limitations: string[] }) {
  return (
    <section className="rounded-xl border bg-card p-4" data-testid="ddc-limitations-panel">
      <h3 className="text-base font-semibold">Limitations</h3>
      <ul className="mt-3 space-y-2 text-sm text-muted-foreground">
        {limitations.map((limitation) => (
          <li key={limitation}>{limitation}</li>
        ))}
      </ul>
    </section>
  );
}

export function DdcAuditTimeline({ items }: { items: DdcWorkflowDefinition[] }) {
  return (
    <section className="rounded-xl border bg-card p-4" data-testid="ddc-audit-timeline">
      <h3 className="text-base font-semibold">Audit / Review Timeline</h3>
      <ol className="mt-3 space-y-3 text-sm text-muted-foreground">
        {items.map((item) => (
          <li key={item.key}>
            <div className="font-medium text-foreground">{item.title}</div>
            <div>{item.humanReviewPoint}</div>
          </li>
        ))}
      </ol>
    </section>
  );
}

export function DdcEvidenceTable({ endpoints }: { endpoints: string[] }) {
  return (
    <section className="rounded-xl border bg-card p-4" data-testid="ddc-evidence-table">
      <h3 className="text-base font-semibold">Evidence / Endpoint Contract</h3>
      <table className="mt-3 w-full text-left text-sm">
        <thead>
          <tr className="border-b">
            <th className="pb-2 font-medium">Endpoint</th>
            <th className="pb-2 font-medium">Status</th>
          </tr>
        </thead>
        <tbody>
          {endpoints.map((endpoint) => (
            <tr key={endpoint} className="border-b last:border-0">
              <td className="py-2">{endpoint}</td>
              <td className="py-2">metadata/evidence-only</td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}

export function DdcBridgeCard({ title, description, target }: { title: string; description: string; target: string }) {
  return (
    <article className="rounded-xl border bg-card p-4" data-testid={`ddc-bridge-${slugify(target)}`}>
      <h3 className="text-base font-semibold">{title}</h3>
      <p className="mt-2 text-sm text-muted-foreground">{description}</p>
      <p className="mt-3 text-xs text-muted-foreground">Bridge target: {target}</p>
    </article>
  );
}

export function DdcMetadataFormShell({ title, description, endpoints }: { title: string; description: string; endpoints: string[] }) {
  return (
    <section className="rounded-xl border bg-card p-4" data-testid={`ddc-form-shell-${slugify(title)}`}>
      <h3 className="text-base font-semibold">{title}</h3>
      <p className="mt-2 text-sm text-muted-foreground">{description}</p>
      <ul className="mt-3 space-y-1 text-sm text-muted-foreground">
        {endpoints.map((endpoint) => (
          <li key={endpoint}>{endpoint}</li>
        ))}
      </ul>
    </section>
  );
}

export function DdcSafetyChecklist() {
  return (
    <section className="rounded-xl border bg-card p-4" data-testid="ddc-safety-checklist">
      <h3 className="text-base font-semibold">Safety Checklist</h3>
      <ul className="mt-3 grid gap-2 text-sm text-muted-foreground md:grid-cols-2">
        <li>fakeDocuments=false</li>
        <li>fakeDecrees=false</li>
        <li>fakeSignatures=false</li>
        <li>fakeDeliveryConfirmations=false</li>
        <li>fakeArchiveLegalRecord=false</li>
        <li>officialLegalEffect=false</li>
        <li>externalSubmissionEnabled=false</li>
        <li>automaticRectorDecisionEnabled=false</li>
        <li>automaticDecreeApprovalEnabled=false</li>
        <li>automaticDocumentSigningEnabled=false</li>
        <li>hiddenScorePresent=false</li>
        <li>humanReviewRequired=true</li>
      </ul>
    </section>
  );
}

export function DdcNoOverclaimFooter() {
  return (
    <footer className="rounded-xl border border-dashed p-4 text-sm text-muted-foreground" data-testid="ddc-no-overclaim-footer">
      <p>No sign document UI.</p>
      <p>No issue official decree UI.</p>
      <p>No automatic rector/decree approval UI.</p>
      <p>No external submission or delivery execution UI.</p>
      <p>No legal-effect archive confirmation UI.</p>
      <p>No hidden staff/department score UI.</p>
      <p>No production/sales/GCC/L5/L6 claim.</p>
    </footer>
  );
}

export function getDdcRouteDefinition(routeKey: DdcRouteKey) {
  const route = DOCUMENT_DECREE_CORRESPONDENCE_ROUTES.find((candidate) => candidate.key === routeKey);
  if (!route) {
    throw new Error(`Unknown DDC route key: ${routeKey}`);
  }
  return route;
}

export function buildDdcPageModel(routeKey: DdcRouteKey): DdcPageModel {
  const route = getDdcRouteDefinition(routeKey);
  const primaryWidgets = routeKey === 'dashboard'
    ? DOCUMENT_DECREE_CORRESPONDENCE_DASHBOARD_WIDGETS
    : DOCUMENT_DECREE_CORRESPONDENCE_DASHBOARD_WIDGETS.filter((widget) => widget.relatedRoutes.includes(routeKey));
  const workflows = DOCUMENT_DECREE_CORRESPONDENCE_WORKFLOWS.filter((workflow) => workflow.routeKeys.includes(routeKey));

  return {
    route,
    primaryWidgets,
    workflows,
    emptyState: route.emptyState,
    incompleteDataMessage: route.incompleteDataState,
    noOverclaimAssertions: [
      'No sign document action is available.',
      'No legal-effect decree execution action is available.',
      'No external submission/delivery execution action is available.',
    ],
  };
}

function DdcPageContent({ model }: { model: DdcPageModel }) {
  const readinessItems = [
    `Runtime mode: ${DOCUMENT_DECREE_CORRESPONDENCE_RUNTIME_MODE}`,
    `Data source: ${DOCUMENT_DECREE_CORRESPONDENCE_DATA_SOURCE}`,
    `Backend route count used: ${DOCUMENT_DECREE_CORRESPONDENCE_BACKEND_ROUTE_COUNT}`,
    `Backend permission count used: ${DOCUMENT_DECREE_CORRESPONDENCE_PERMISSION_COUNT}`,
  ];
  const registryRows = buildDdcRegistryRows(model);
  const auditEvents = buildDdcAuditEvents(model);

  return (
    <DocumentDecreeCorrespondencePageShell routeKey={model.route.key}>
      <div className="space-y-6" data-testid={`ddc-page-${model.route.key}`}>
        <section className="space-y-3">
          <p className="text-sm text-muted-foreground">{model.route.description}</p>
          <div className="flex flex-wrap items-center gap-3 text-sm text-muted-foreground">
            <span>Route: {model.route.path}</span>
            <span>Permission: {model.route.requiredPermission}</span>
            {model.route.sensitive ? <DdcHumanReviewBadge /> : null}
            {model.route.key === 'signature-readiness' ? <DdcSignatureReadinessBadge /> : null}
            {model.route.key === 'delivery-readiness' ? <DdcDeliveryReadinessBadge /> : null}
            {model.route.key === 'archive' ? <DdcArchiveReadinessBadge /> : null}
          </div>
        </section>

        <DdcBoundaryBanner labels={model.route.boundaryLabels} />
        <DdcIncompleteDataNotice />

        <div className="grid gap-4 xl:grid-cols-[1.4fr,1fr]">
          <DdcMetadataFormShell title={`${model.route.title} surface`} description={model.emptyState} endpoints={model.route.backendEndpoints} />
          <DdcReadinessCard title="Runtime baseline" items={readinessItems} />
        </div>

        {model.route.dashboardLike || model.primaryWidgets.length > 0 ? <DdcDashboardGrid widgets={model.primaryWidgets} /> : null}

        <section className="space-y-4" data-testid="ddc-operability-registry">
          <div className="space-y-1">
            <h2 className="text-lg font-semibold">Document lifecycle registry</h2>
            <p className="text-sm text-muted-foreground">The shared table shell consolidates intake, routing, decree, and correspondence visibility without inventing approval or signing behavior.</p>
          </div>
          <DataTableShell
            toolbar={<div className="px-1 text-sm text-muted-foreground">Rows: {registryRows.length}. Actions remain disabled unless backed by a real endpoint.</div>}
            table={<DdcRegistryTable rows={registryRows} />}
            isEmpty={registryRows.length === 0}
            emptyTitle="No document lifecycle data"
            emptyDescription={model.emptyState}
          />
        </section>

        <div className="grid gap-4 lg:grid-cols-2">
          <DdcEvidenceTable endpoints={model.route.backendEndpoints} />
          <AuditTrailPanel events={auditEvents} />
        </div>

        <DdcStateGallery />

        <div className="grid gap-4 lg:grid-cols-2 xl:grid-cols-3">
          <DdcMetricCard label="fakeDocuments" value={String(fakeDocuments)} helperText="No fake official document generation is exposed." />
          <DdcMetricCard label="fakeDecrees" value={String(fakeDecrees)} helperText="No fake decree generation is exposed." />
          <DdcMetricCard label="fakeSignatures" value={String(fakeSignatures)} helperText="No fake signing surface exists." />
          <DdcMetricCard label="fakeDeliveryConfirmations" value={String(fakeDeliveryConfirmations)} helperText="No fake delivery confirmation surface exists." />
          <DdcMetricCard label="fakeArchiveLegalRecord" value={String(fakeArchiveLegalRecord)} helperText="No legal-effect archive confirmation exists." />
          <DdcMetricCard label="humanReviewRequired" value={String(humanReviewRequired)} helperText={model.incompleteDataMessage} />
        </div>

        <div className="grid gap-4 xl:grid-cols-2">
          <DdcLimitationsPanel limitations={[...DOCUMENT_DECREE_CORRESPONDENCE_SAFETY_FLAGS.limitations, ...model.noOverclaimAssertions]} />
          <DdcReadinessCard title="Safety booleans" items={[
            `officialLegalEffect=${String(officialLegalEffect)}`,
            `externalSubmissionEnabled=${String(externalSubmissionEnabled)}`,
            `automaticRectorDecisionEnabled=${String(automaticRectorDecisionEnabled)}`,
            `automaticDecreeApprovalEnabled=${String(automaticDecreeApprovalEnabled)}`,
            `automaticDocumentSigningEnabled=${String(automaticDocumentSigningEnabled)}`,
            `hiddenScorePresent=${String(hiddenScorePresent)}`,
          ]} />
        </div>

        {model.route.key === 'bridges' || model.route.key === 'signature-readiness' || model.route.key === 'delivery-readiness' ? (
          <div className="grid gap-4 lg:grid-cols-2 xl:grid-cols-3">
            <DdcBridgeCard title="Executive Bridge" description="Read-only-first executive bridge summary." target="executive" />
            <DdcBridgeCard title="Assignments Bridge" description="Read-only-first assignments bridge summary." target="assignments" />
            <DdcBridgeCard title="Archive/Readiness Bridge" description="Readiness and archive context with no legal effect." target="archive-readiness" />
          </div>
        ) : null}

        <DdcSafetyChecklist />
        <DdcNoOverclaimFooter />
      </div>
    </DocumentDecreeCorrespondencePageShell>
  );
}

export function DocumentDecreeCorrespondencePageShell({ routeKey, children }: { routeKey: DdcRouteKey; children: ReactNode }) {
  const route = getDdcRouteDefinition(routeKey);
  const [search, setSearch] = useState('');
  const [status, setStatus] = useState('');
  const [range, setRange] = useState({ from: '', to: '' });

  return (
    <div className="space-y-6" data-testid="ddc-page-shell">
      <PageShell>
      <SectionHeader eyebrow="Document / Decree / Correspondence Suite" title={route.title} description={route.description} />
      <PageToolbar
        left={
          <PageActions>
            <PageActionBar
              secondaryActions={[
                { id: 'edit', label: 'Edit', disabled: true, disabledReason: 'No shell-level edit workflow.' },
                { id: 'refresh', label: 'Refresh', disabled: true, disabledReason: 'Use route-native refresh behavior.' },
                { id: 'upload', label: 'Upload', disabled: true, disabledReason: 'No upload endpoint on shell.' },
              ]}
              primaryAction={{ id: 'create', label: 'Create', disabled: true, disabledReason: 'No create endpoint on shell.' }}
            />
          </PageActions>
        }
        right={
          <PageActions>
            <ExportButton exportAvailable={false} unavailableReason="Export endpoint unavailable for this route shell." />
          </PageActions>
        }
      />
      <FilterBar onApply={() => undefined} onClear={() => { setSearch(''); setStatus(''); setRange({ from: '', to: '' }); }} onPersistToUrl={() => undefined}>
        <SearchInput value={search} onChange={setSearch} placeholder="Search records" />
        <StatusFilter value={status} onChange={setStatus} options={[{ value: 'active', label: 'Active' }, { value: 'draft', label: 'Draft' }]} />
        <DateRangeFilter value={range} onChange={setRange} />
      </FilterBar>

      <nav className="flex flex-wrap gap-2" aria-label="Document decree correspondence navigation">
        {DOCUMENT_DECREE_CORRESPONDENCE_NAV_ITEMS.map((item) => (
          <Link key={item.key} href={item.href} className={`rounded-full border px-3 py-1 text-sm ${item.key === routeKey ? 'bg-primary text-primary-foreground' : 'text-muted-foreground'}`}>
            {item.title}
          </Link>
        ))}
      </nav>

        <EvidenceUploadPanel uploadSupported={false} limitationLabel="Evidence upload remains disabled unless a route-specific backend contract is available." />
        {children}
      </PageShell>
    </div>
  );
}

export function DocumentDecreeCorrespondencePage({ routeKey, userPermissions }: { routeKey: DdcRouteKey; userPermissions?: string[] }) {
  const model = buildDdcPageModel(routeKey);
  if (userPermissions) {
    return hasDdcPermission(userPermissions, model.route.requiredPermission)
      ? <DdcPageContent model={model} />
      : <DdcPermissionDeniedPanel permission={model.route.requiredPermission} />;
  }

  return (
    <RequirePermission permission={model.route.requiredPermission} message="This document decree correspondence route is fail-closed until the required permission is granted.">
      <DdcPageContent model={model} />
    </RequirePermission>
  );
}

export { DOCUMENT_DECREE_CORRESPONDENCE_BOUNDARY_COPY, DOCUMENT_DECREE_CORRESPONDENCE_FORBIDDEN_LABELS };

void DOCUMENT_DECREE_CORRESPONDENCE_BOUNDARY_LABELS;
void DOCUMENT_DECREE_CORRESPONDENCE_FORBIDDEN_LABELS;
