'use client';

import Link from 'next/link';
import { useState, type ReactNode } from 'react';
import { RequirePermission } from '@/shared/ui/permission-gate';
import {
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
  fakeFinanceData,
  fakeMetrics,
  fakePaymentData,
  FINANCE_PROCUREMENT_ASSET_BACKEND_ROUTE_COUNT,
  FINANCE_PROCUREMENT_ASSET_DASHBOARD_WIDGETS,
  FINANCE_PROCUREMENT_ASSET_DATA_SOURCE,
  FINANCE_PROCUREMENT_ASSET_NAV_ITEMS,
  FINANCE_PROCUREMENT_ASSET_PERMISSION_COUNT,
  FINANCE_PROCUREMENT_ASSET_PROVIDER_PROFILES,
  FINANCE_PROCUREMENT_ASSET_ROUTES,
  FINANCE_PROCUREMENT_ASSET_RUNTIME_MODE,
  FINANCE_PROCUREMENT_ASSET_SAFETY_FLAGS,
  FINANCE_PROCUREMENT_ASSET_WORKFLOWS,
} from './constants';
import {
  FINANCE_PROCUREMENT_ASSET_BOUNDARY_COPY,
  FINANCE_PROCUREMENT_ASSET_BOUNDARY_LABELS,
  FINANCE_PROCUREMENT_ASSET_FORBIDDEN_LABELS,
} from './boundaryLabels';
import { hasFpaPermission } from './guards';
import type { FpaDashboardWidget, FpaRouteDefinition, FpaRouteKey, FpaWorkflowDefinition } from './types';

interface FpaPageModel {
  route: FpaRouteDefinition;
  primaryWidgets: FpaDashboardWidget[];
  workflows: FpaWorkflowDefinition[];
  emptyState: string;
  incompleteDataMessage: string;
  noOverclaimAssertions: string[];
}

type FpaRegistryRow = {
  key: string;
  surface: string;
  visibility: string;
  endpoints: string[];
  limitation: string;
};

function slugify(value: string) {
  return value.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');
}

function buildFpaRegistryRows(model: FpaPageModel): FpaRegistryRow[] {
  const widgetRows = model.primaryWidgets.map((widget) => ({
    key: widget.key,
    surface: widget.title,
    visibility: 'Registry visibility',
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

function FpaRegistryTable({ rows }: { rows: FpaRegistryRow[] }) {
  return (
    <table className="w-full text-left text-sm" data-testid="fpa-registry-table">
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

function FpaStateGallery() {
  return (
    <section className="grid gap-4 xl:grid-cols-2" data-testid="fpa-state-gallery">
      <EmptyState variant="no_data" title="No finance registry data" description="No registry rows are available for the current route contract." />
      <EmptyState variant="no_results" title="No procurement results" description="The shared search and filters can narrow the visible finance registry without inventing execution controls." />
      <EmptyState variant="metadata_only" title="Metadata-only visibility" description="Execution remains disabled until a real backend contract supports it." limitation="No live payment, bank, or ERP execution is exposed." />
      <EmptyState variant="future_scope" title="Future scope remains gated" description="Live procurement execution, vendor award, and settlement flows remain deferred outside A-044.R6." />
    </section>
  );
}

export function FpaBoundaryBanner({ labels }: { labels: string[] }) {
  return (
    <section className="rounded-xl border border-amber-200 bg-amber-50 p-4" data-testid="fpa-boundary-banner">
      <div className="flex flex-wrap gap-2">
        {labels.map((label) => (
          <span key={label} data-testid={`fpa-boundary-${slugify(label)}`} className="inline-flex rounded-full border border-amber-300 px-3 py-1 text-xs font-medium text-amber-950">
            {label}
          </span>
        ))}
      </div>
    </section>
  );
}

export function FpaReadinessCard({ title, items }: { title: string; items: string[] }) {
  return (
    <section className="rounded-xl border bg-card p-4" data-testid={`fpa-readiness-${slugify(title)}`}>
      <h3 className="text-sm font-semibold">{title}</h3>
      <ul className="mt-3 space-y-2 text-sm text-muted-foreground">
        {items.map((item) => (
          <li key={item}>{item}</li>
        ))}
      </ul>
    </section>
  );
}

export function FpaMetricCard({ label, value, helperText }: { label: string; value: string; helperText: string }) {
  return (
    <article className="rounded-xl border bg-card p-4" data-testid={`fpa-metric-${slugify(label)}`}>
      <div className="text-xs uppercase tracking-wide text-muted-foreground">{label}</div>
      <div className="mt-2 text-2xl font-semibold">{value}</div>
      <p className="mt-2 text-sm text-muted-foreground">{helperText}</p>
    </article>
  );
}

export function FpaDashboardGrid({ widgets }: { widgets: FpaDashboardWidget[] }) {
  return (
    <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-3" data-testid="fpa-dashboard-grid">
      {widgets.map((widget) => (
        <article key={widget.key} className="rounded-xl border bg-card p-4" data-testid={`fpa-widget-${widget.key}`}>
          <div className="flex items-start justify-between gap-3">
            <div>
              <h3 className="text-base font-semibold">{widget.title}</h3>
              <p className="mt-1 text-sm text-muted-foreground">{widget.description}</p>
            </div>
            <FpaEvidenceStatusBadge status="metadata-only" />
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

export function FpaEvidenceStatusBadge({ status }: { status: string }) {
  return <span className="rounded-full border border-slate-300 px-2 py-1 text-xs font-medium">{status}</span>;
}

export function FpaHumanReviewBadge() {
  return <span className="rounded-full border border-blue-300 bg-blue-50 px-2 py-1 text-xs font-medium text-blue-900" data-testid="fpa-human-review-badge">Human review required</span>;
}

export function FpaProviderDeferredBadge() {
  return <span className="rounded-full border border-slate-300 px-2 py-1 text-xs font-medium" data-testid="fpa-provider-deferred-badge">providerConnected=false / liveBankSync=false / liveErpSync=false</span>;
}

export function FpaPaymentReadinessBadge() {
  return <span className="rounded-full border border-slate-300 px-2 py-1 text-xs font-medium" data-testid="fpa-payment-readiness-badge">paymentExecutionEnabled=false</span>;
}

export function FpaIncompleteDataNotice() {
  return (
    <div className="rounded-xl border border-dashed p-4 text-sm text-muted-foreground" data-testid="fpa-incomplete-data-notice">
      incompleteData=true. The runtime keeps incomplete metadata visible instead of masking gaps.
    </div>
  );
}

export function FpaPermissionDeniedPanel({ permission }: { permission: string }) {
  return (
    <div data-testid="fpa-permission-denied-panel">
      <PermissionDeniedState role="tenant_admin" requiredPermission={permission} reason="This finance/procurement/asset view is fail-closed for the current permission set." />
    </div>
  );
}

export function FpaLimitationsPanel({ limitations }: { limitations: string[] }) {
  return (
    <section className="rounded-xl border bg-card p-4" data-testid="fpa-limitations-panel">
      <h3 className="text-base font-semibold">Limitations</h3>
      <ul className="mt-3 space-y-2 text-sm text-muted-foreground">
        {limitations.map((limitation) => (
          <li key={limitation}>{limitation}</li>
        ))}
      </ul>
    </section>
  );
}

export function FpaAuditTimeline({ items }: { items: FpaWorkflowDefinition[] }) {
  return (
    <section className="rounded-xl border bg-card p-4" data-testid="fpa-audit-timeline">
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

export function FpaEvidenceTable({ endpoints }: { endpoints: string[] }) {
  return (
    <section className="rounded-xl border bg-card p-4" data-testid="fpa-evidence-table">
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

export function FpaBridgeCard({ title, description, target }: { title: string; description: string; target: string }) {
  return (
    <article className="rounded-xl border bg-card p-4" data-testid={`fpa-bridge-${slugify(target)}`}>
      <h3 className="text-base font-semibold">{title}</h3>
      <p className="mt-2 text-sm text-muted-foreground">{description}</p>
      <p className="mt-3 text-xs text-muted-foreground">Bridge target: {target}</p>
    </article>
  );
}

export function FpaReviewActionPanel({ title, permission, description }: { title: string; permission: string; description: string }) {
  return (
    <section className="rounded-xl border bg-card p-4" data-testid={`fpa-review-panel-${slugify(title)}`}>
      <div className="flex items-center gap-2">
        <FpaHumanReviewBadge />
        <span className="text-xs text-muted-foreground">Sensitive actions require explicit review, manage, or evidence permission.</span>
      </div>
      <h3 className="mt-3 text-base font-semibold">{title}</h3>
      <p className="mt-2 text-sm text-muted-foreground">{description}</p>
      <p className="mt-3 text-xs text-muted-foreground">Required action permission: {permission}</p>
    </section>
  );
}

export function FpaMetadataFormShell({ title, description, endpoints }: { title: string; description: string; endpoints: string[] }) {
  return (
    <section className="rounded-xl border bg-card p-4" data-testid={`fpa-form-shell-${slugify(title)}`}>
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

export function FpaSafetyChecklist() {
  return (
    <section className="rounded-xl border bg-card p-4" data-testid="fpa-safety-checklist">
      <h3 className="text-base font-semibold">Safety Checklist</h3>
      <ul className="mt-3 grid gap-2 text-sm text-muted-foreground md:grid-cols-2">
        <li>fakeMetrics=false</li>
        <li>fakeFinanceData=false</li>
        <li>fakePaymentData=false</li>
        <li>providerConnected=false</li>
        <li>liveBankSync=false</li>
        <li>liveErpSync=false</li>
        <li>paymentExecutionEnabled=false</li>
        <li>automaticProcurementApprovalEnabled=false</li>
        <li>automaticBudgetApprovalEnabled=false</li>
        <li>automaticVendorAwardEnabled=false</li>
        <li>hiddenScorePresent=false</li>
        <li>humanReviewRequired=true</li>
      </ul>
    </section>
  );
}

export function FpaNoOverclaimFooter() {
  return (
    <footer className="rounded-xl border border-dashed p-4 text-sm text-muted-foreground" data-testid="fpa-no-overclaim-footer">
      <p>No live bank integration UI.</p>
      <p>No live ERP/1C sync UI.</p>
      <p>No payment execution UI.</p>
      <p>No automatic procurement approval UI.</p>
      <p>No automatic budget approval UI.</p>
      <p>No automatic vendor award UI.</p>
      <p>No hidden finance/vendor score UI.</p>
      <p>No production/sales/GCC/L5/L6 claim.</p>
    </footer>
  );
}

export function getFpaRouteDefinition(routeKey: FpaRouteKey) {
  const route = FINANCE_PROCUREMENT_ASSET_ROUTES.find((candidate) => candidate.key === routeKey);
  if (!route) {
    throw new Error(`Unknown FPA route key: ${routeKey}`);
  }
  return route;
}

export function buildFpaPageModel(routeKey: FpaRouteKey): FpaPageModel {
  const route = getFpaRouteDefinition(routeKey);
  const primaryWidgets = routeKey === 'dashboard'
    ? FINANCE_PROCUREMENT_ASSET_DASHBOARD_WIDGETS
    : FINANCE_PROCUREMENT_ASSET_DASHBOARD_WIDGETS.filter((widget) => widget.relatedRoutes.includes(routeKey));
  const workflows = FINANCE_PROCUREMENT_ASSET_WORKFLOWS.filter((workflow) => workflow.routeKeys.includes(routeKey));

  return {
    route,
    primaryWidgets,
    workflows,
    emptyState: route.emptyState,
    incompleteDataMessage: route.incompleteDataState,
    noOverclaimAssertions: [
      'No live bank integration or ERP sync controls are available.',
      'No payment execution or settlement controls are available.',
      'No hidden finance or vendor score is rendered.',
    ],
  };
}

function FpaPageContent({ model }: { model: FpaPageModel }) {
  const readinessItems = [
    `Runtime mode: ${FINANCE_PROCUREMENT_ASSET_RUNTIME_MODE}`,
    `Data source: ${FINANCE_PROCUREMENT_ASSET_DATA_SOURCE}`,
    `Backend route count used: ${FINANCE_PROCUREMENT_ASSET_BACKEND_ROUTE_COUNT}`,
    `Backend permission count used: ${FINANCE_PROCUREMENT_ASSET_PERMISSION_COUNT}`,
  ];
  const registryRows = buildFpaRegistryRows(model);

  return (
    <FinanceProcurementAssetPageShell routeKey={model.route.key}>
      <div className="space-y-6" data-testid={`fpa-page-${model.route.key}`}>
        <section className="space-y-3">
          <p className="text-sm text-muted-foreground">{model.route.description}</p>
          <div className="flex flex-wrap items-center gap-3 text-sm text-muted-foreground">
            <span>Route: {model.route.path}</span>
            <span>Permission: {model.route.requiredPermission}</span>
            {model.route.sensitive ? <FpaHumanReviewBadge /> : null}
            {model.route.key === 'provider-readiness' || model.route.key === 'erp-readiness' || model.route.key === 'bank-readiness' ? <FpaProviderDeferredBadge /> : null}
            {model.route.key === 'payment-readiness' ? <FpaPaymentReadinessBadge /> : null}
          </div>
        </section>

        <FpaBoundaryBanner labels={model.route.boundaryLabels} />
        <FpaIncompleteDataNotice />

        <div className="grid gap-4 xl:grid-cols-[1.4fr,1fr]">
          <FpaMetadataFormShell title={`${model.route.title} surface`} description={model.emptyState} endpoints={model.route.backendEndpoints} />
          <FpaReadinessCard title="Runtime baseline" items={readinessItems} />
        </div>

        {model.route.dashboardLike || model.primaryWidgets.length > 0 ? <FpaDashboardGrid widgets={model.primaryWidgets} /> : null}

        <section className="space-y-4" data-testid="fpa-operability-registry">
          <div className="space-y-1">
            <h2 className="text-lg font-semibold">Procurement and asset registry visibility</h2>
            <p className="text-sm text-muted-foreground">The shared table shell makes finance, procurement, and asset contract surfaces scannable without enabling fake execution.</p>
          </div>
          <DataTableShell
            toolbar={<div className="px-1 text-sm text-muted-foreground">Rows: {registryRows.length}. Search/filter controls remain shell-level and metadata-only.</div>}
            table={<FpaRegistryTable rows={registryRows} />}
            isEmpty={registryRows.length === 0}
            emptyTitle="No finance registry data"
            emptyDescription={model.emptyState}
          />
        </section>

        <div className="grid gap-4 lg:grid-cols-2">
          <FpaEvidenceTable endpoints={model.route.backendEndpoints} />
          <FpaAuditTimeline items={model.workflows.length > 0 ? model.workflows : FINANCE_PROCUREMENT_ASSET_WORKFLOWS.slice(0, 2)} />
        </div>

        <FpaStateGallery />

        <div className="grid gap-4 lg:grid-cols-2 xl:grid-cols-3">
          <FpaMetricCard label="fakeMetrics" value={String(fakeMetrics)} helperText="All dashboard-like surfaces expose fakeMetrics=false." />
          <FpaMetricCard label="fakeFinanceData" value={String(fakeFinanceData)} helperText="No fake finance, invoice, or vendor records are generated." />
          <FpaMetricCard label="fakePaymentData" value={String(fakePaymentData)} helperText="Payment readiness remains non-live and evidence-only." />
          <FpaMetricCard label="humanReviewRequired" value={String(FINANCE_PROCUREMENT_ASSET_SAFETY_FLAGS.human_review_required)} helperText={model.incompleteDataMessage} />
        </div>

        <div className="grid gap-4 xl:grid-cols-2">
          <FpaReviewActionPanel title="Human review boundary" permission={model.route.requiredPermission} description={model.noOverclaimAssertions.join(' ')} />
          <FpaLimitationsPanel limitations={[...FINANCE_PROCUREMENT_ASSET_SAFETY_FLAGS.limitations, ...model.noOverclaimAssertions]} />
        </div>

        {(model.route.key === 'provider-readiness' || model.route.key === 'payment-readiness' || model.route.key === 'erp-readiness' || model.route.key === 'bank-readiness' || model.route.key === 'bridges') ? (
          <div className="grid gap-4 lg:grid-cols-2 xl:grid-cols-3">
            {FINANCE_PROCUREMENT_ASSET_PROVIDER_PROFILES.map((profile) => (
              <FpaBridgeCard key={profile.key} title={profile.title} description={profile.description} target={profile.key} />
            ))}
          </div>
        ) : null}

        <FpaSafetyChecklist />
        <FpaNoOverclaimFooter />
      </div>
    </FinanceProcurementAssetPageShell>
  );
}

export function FinanceProcurementAssetPageShell({ routeKey, children }: { routeKey: FpaRouteKey; children: ReactNode }) {
  const route = getFpaRouteDefinition(routeKey);
  const [search, setSearch] = useState('');
  const [status, setStatus] = useState('');
  const [range, setRange] = useState({ from: '', to: '' });

  return (
    <div className="space-y-6" data-testid="fpa-page-shell">
      <PageShell>
      <SectionHeader eyebrow="Finance / Procurement / Asset Suite" title={route.title} description={route.description} />
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

      <nav className="flex flex-wrap gap-2" aria-label="Finance procurement asset navigation">
        {FINANCE_PROCUREMENT_ASSET_NAV_ITEMS.map((item) => (
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

export function FinanceProcurementAssetPage({ routeKey, userPermissions }: { routeKey: FpaRouteKey; userPermissions?: string[] }) {
  const model = buildFpaPageModel(routeKey);
  if (userPermissions) {
    return hasFpaPermission(userPermissions, model.route.requiredPermission)
      ? <FpaPageContent model={model} />
      : <FpaPermissionDeniedPanel permission={model.route.requiredPermission} />;
  }

  return (
    <RequirePermission permission={model.route.requiredPermission} message="This finance procurement asset route is fail-closed until the required permission is granted.">
      <FpaPageContent model={model} />
    </RequirePermission>
  );
}

export { FINANCE_PROCUREMENT_ASSET_BOUNDARY_COPY, FINANCE_PROCUREMENT_ASSET_FORBIDDEN_LABELS };

void FINANCE_PROCUREMENT_ASSET_BOUNDARY_LABELS;
void FINANCE_PROCUREMENT_ASSET_FORBIDDEN_LABELS;
