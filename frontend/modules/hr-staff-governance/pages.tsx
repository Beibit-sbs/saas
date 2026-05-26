'use client';

import Link from 'next/link';
import type { ReactNode } from 'react';
import { RequirePermission } from '@/shared/ui/permission-gate';
import {
  fakeMetrics,
  HR_STAFF_GOVERNANCE_BACKEND_ROUTE_COUNT,
  HR_STAFF_GOVERNANCE_DATA_SOURCE,
  HR_STAFF_GOVERNANCE_DASHBOARD_WIDGETS,
  HR_STAFF_GOVERNANCE_NAV_ITEMS,
  HR_STAFF_GOVERNANCE_PERMISSION_COUNT,
  HR_STAFF_GOVERNANCE_PROVIDER_PROFILES,
  HR_STAFF_GOVERNANCE_ROUTE_FAMILY,
  HR_STAFF_GOVERNANCE_ROUTES,
  HR_STAFF_GOVERNANCE_RUNTIME_MODE,
  HR_STAFF_GOVERNANCE_SAFETY_FLAGS,
  HR_STAFF_GOVERNANCE_WORKFLOWS,
} from './constants';
import {
  HR_STAFF_GOVERNANCE_BOUNDARY_COPY,
  HR_STAFF_GOVERNANCE_BOUNDARY_LABELS,
  HR_STAFF_GOVERNANCE_FORBIDDEN_LABELS,
  getHrBoundaryLabels,
} from './boundaryLabels';
import { hasHrPermission } from './guards';
import type { HrDashboardWidget, HrRouteDefinition, HrRouteKey, HrWorkflowDefinition } from './types';

interface HrPageModel {
  route: HrRouteDefinition;
  primaryWidgets: HrDashboardWidget[];
  workflows: HrWorkflowDefinition[];
  emptyState: string;
  incompleteDataMessage: string;
  noOverclaimAssertions: string[];
}

function slugify(value: string) {
  return value.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');
}

function titleToState(title: string) {
  return `${title} metadata is not populated yet. This runtime keeps incomplete data explicit and review-only.`;
}

export function HrBoundaryBanner({ labels }: { labels: string[] }) {
  return (
    <section className="rounded-xl border border-amber-200 bg-amber-50 p-4" data-testid="hr-boundary-banner">
      <div className="flex flex-wrap gap-2">
        {labels.map((label) => (
          <span
            key={label}
            data-testid={`hr-boundary-${slugify(label)}`}
            className="inline-flex rounded-full border border-amber-300 px-3 py-1 text-xs font-medium text-amber-950"
          >
            {label}
          </span>
        ))}
      </div>
    </section>
  );
}

export function HrReadinessCard({ title, items }: { title: string; items: string[] }) {
  return (
    <section className="rounded-xl border bg-card p-4" data-testid={`hr-readiness-${slugify(title)}`}>
      <h3 className="text-sm font-semibold">{title}</h3>
      <ul className="mt-3 space-y-2 text-sm text-muted-foreground">
        {items.map((item) => (
          <li key={item}>{item}</li>
        ))}
      </ul>
    </section>
  );
}

export function HrMetricCard({ label, value, helperText }: { label: string; value: string; helperText: string }) {
  return (
    <article className="rounded-xl border bg-card p-4" data-testid={`hr-metric-${slugify(label)}`}>
      <div className="text-xs uppercase tracking-wide text-muted-foreground">{label}</div>
      <div className="mt-2 text-2xl font-semibold">{value}</div>
      <p className="mt-2 text-sm text-muted-foreground">{helperText}</p>
    </article>
  );
}

export function HrDashboardGrid({ widgets }: { widgets: HrDashboardWidget[] }) {
  return (
    <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-3" data-testid="hr-dashboard-grid">
      {widgets.map((widget) => (
        <article key={widget.key} className="rounded-xl border bg-card p-4" data-testid={`hr-widget-${widget.key}`}>
          <div className="flex items-start justify-between gap-3">
            <div>
              <h3 className="text-base font-semibold">{widget.title}</h3>
              <p className="mt-1 text-sm text-muted-foreground">{widget.description}</p>
            </div>
            <HrEvidenceStatusBadge status="metadata-only" />
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

export function HrEvidenceStatusBadge({ status }: { status: string }) {
  return <span className="rounded-full border border-slate-300 px-2 py-1 text-xs font-medium">{status}</span>;
}

export function HrHumanReviewBadge() {
  return <span className="rounded-full border border-blue-300 bg-blue-50 px-2 py-1 text-xs font-medium text-blue-900" data-testid="hr-human-review-badge">Human review required</span>;
}

export function HrProviderDeferredBadge() {
  return <span className="rounded-full border border-slate-300 px-2 py-1 text-xs font-medium" data-testid="hr-provider-deferred-badge">providerConnected=false / liveProviderSync=false</span>;
}

export function HrPayrollReadinessBadge() {
  return <span className="rounded-full border border-slate-300 px-2 py-1 text-xs font-medium" data-testid="hr-payroll-readiness-badge">payrollExecutionEnabled=false</span>;
}

export function HrIncompleteDataNotice() {
  return (
    <div className="rounded-xl border border-dashed p-4 text-sm text-muted-foreground" data-testid="hr-incomplete-data-notice">
      incompleteData=true. The runtime keeps incomplete metadata visible instead of masking gaps.
    </div>
  );
}

export function HrPermissionDeniedPanel({ permission }: { permission: string }) {
  return (
    <div className="rounded-xl border border-destructive/30 bg-destructive/5 p-6" data-testid="hr-permission-denied-panel">
      <h2 className="text-lg font-semibold">Permission required</h2>
      <p className="mt-2 text-sm text-muted-foreground">This route is fail-closed and requires `{permission}`.</p>
    </div>
  );
}

export function HrLimitationsPanel({ limitations }: { limitations: string[] }) {
  return (
    <section className="rounded-xl border bg-card p-4" data-testid="hr-limitations-panel">
      <h3 className="text-base font-semibold">Limitations</h3>
      <ul className="mt-3 space-y-2 text-sm text-muted-foreground">
        {limitations.map((limitation) => (
          <li key={limitation}>{limitation}</li>
        ))}
      </ul>
    </section>
  );
}

export function HrAuditTimeline({ items }: { items: HrWorkflowDefinition[] }) {
  return (
    <section className="rounded-xl border bg-card p-4" data-testid="hr-audit-timeline">
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

export function HrEvidenceTable({ endpoints }: { endpoints: string[] }) {
  return (
    <section className="rounded-xl border bg-card p-4" data-testid="hr-evidence-table">
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

export function HrBridgeCard({ title, description, target }: { title: string; description: string; target: string }) {
  return (
    <article className="rounded-xl border bg-card p-4" data-testid={`hr-bridge-${slugify(target)}`}>
      <h3 className="text-base font-semibold">{title}</h3>
      <p className="mt-2 text-sm text-muted-foreground">{description}</p>
      <p className="mt-3 text-xs text-muted-foreground">Bridge target: {target}</p>
    </article>
  );
}

export function HrReviewActionPanel({ title, permission, description }: { title: string; permission: string; description: string }) {
  return (
    <section className="rounded-xl border bg-card p-4" data-testid={`hr-review-panel-${slugify(title)}`}>
      <div className="flex items-center gap-2">
        <HrHumanReviewBadge />
        <span className="text-xs text-muted-foreground">Sensitive actions require explicit review permission.</span>
      </div>
      <h3 className="mt-3 text-base font-semibold">{title}</h3>
      <p className="mt-2 text-sm text-muted-foreground">{description}</p>
      <p className="mt-3 text-xs text-muted-foreground">Required action permission: {permission}</p>
    </section>
  );
}

export function HrMetadataFormShell({ title, description, endpoints }: { title: string; description: string; endpoints: string[] }) {
  return (
    <section className="rounded-xl border bg-card p-4" data-testid={`hr-form-shell-${slugify(title)}`}>
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

export function HrSafetyChecklist() {
  return (
    <section className="rounded-xl border bg-card p-4" data-testid="hr-safety-checklist">
      <h3 className="text-base font-semibold">Safety Checklist</h3>
      <ul className="mt-3 grid gap-2 text-sm text-muted-foreground md:grid-cols-2">
        <li>fakeMetrics=false</li>
        <li>fakeHrData=false</li>
        <li>providerConnected=false</li>
        <li>liveProviderSync=false</li>
        <li>payrollExecutionEnabled=false</li>
        <li>automaticDecisionEnabled=false</li>
        <li>hiddenScorePresent=false</li>
        <li>humanReviewRequired=true</li>
      </ul>
    </section>
  );
}

export function HrNoOverclaimFooter() {
  return (
    <footer className="rounded-xl border border-dashed p-4 text-sm text-muted-foreground" data-testid="hr-no-overclaim-footer">
      <p>No automatic hiring/firing UI.</p>
      <p>No automatic disciplinary UI.</p>
      <p>No automatic leave approval/rejection UI.</p>
      <p>No payroll execution UI.</p>
      <p>No provider live sync UI.</p>
      <p>No autonomous access revocation UI.</p>
      <p>No hidden employee/faculty score UI.</p>
      <p>No production/sales/GCC/L5/L6 claim.</p>
    </footer>
  );
}

export function getHrRouteDefinition(routeKey: HrRouteKey) {
  const route = HR_STAFF_GOVERNANCE_ROUTES.find((candidate) => candidate.key === routeKey);
  if (!route) {
    throw new Error(`Unknown HR route key: ${routeKey}`);
  }
  return route;
}

export function buildHrPageModel(routeKey: HrRouteKey): HrPageModel {
  const route = getHrRouteDefinition(routeKey);
  const primaryWidgets = routeKey === 'dashboard'
    ? HR_STAFF_GOVERNANCE_DASHBOARD_WIDGETS
    : HR_STAFF_GOVERNANCE_DASHBOARD_WIDGETS.filter((widget) => widget.relatedRoutes.includes(routeKey));
  const workflows = HR_STAFF_GOVERNANCE_WORKFLOWS.filter((workflow) => workflow.routeKeys.includes(routeKey));
  return {
    route,
    primaryWidgets,
    workflows,
    emptyState: titleToState(route.title),
    incompleteDataMessage: 'Incomplete data is expected and explicitly supported in this runtime.',
    noOverclaimAssertions: [
      'No automatic HR decisions are available.',
      'No live provider or payroll execution controls are available.',
      'No hidden employee or faculty score is rendered.',
    ],
  };
}

function HrPageContent({ model }: { model: HrPageModel }) {
  const readinessItems = [
    `Runtime mode: ${HR_STAFF_GOVERNANCE_RUNTIME_MODE}`,
    `Data source: ${HR_STAFF_GOVERNANCE_DATA_SOURCE}`,
    `Backend route count used: ${HR_STAFF_GOVERNANCE_BACKEND_ROUTE_COUNT}`,
    `Backend permission count used: ${HR_STAFF_GOVERNANCE_PERMISSION_COUNT}`,
  ];

  return (
    <HrStaffGovernancePageShell routeKey={model.route.key}>
      <div className="space-y-6" data-testid={`hr-page-${model.route.key}`}>
        <section className="space-y-3">
          <p className="text-sm text-muted-foreground">{model.route.description}</p>
          <div className="flex flex-wrap items-center gap-3 text-sm text-muted-foreground">
            <span>Route: {model.route.path}</span>
            <span>Permission: {model.route.requiredPermission}</span>
            {model.route.sensitive ? <HrHumanReviewBadge /> : null}
            {model.route.key === 'provider-readiness' ? <HrProviderDeferredBadge /> : null}
            {model.route.key === 'payroll-readiness' ? <HrPayrollReadinessBadge /> : null}
          </div>
        </section>

        <HrBoundaryBanner labels={model.route.boundaryLabels} />
        <HrIncompleteDataNotice />

        <div className="grid gap-4 xl:grid-cols-[1.4fr,1fr]">
          <HrMetadataFormShell title={`${model.route.title} surface`} description={model.emptyState} endpoints={model.route.backendEndpoints} />
          <HrReadinessCard title="Runtime baseline" items={readinessItems} />
        </div>

        {model.route.dashboardLike || model.primaryWidgets.length > 0 ? <HrDashboardGrid widgets={model.primaryWidgets} /> : null}

        <div className="grid gap-4 lg:grid-cols-2">
          <HrEvidenceTable endpoints={model.route.backendEndpoints} />
          <HrAuditTimeline items={model.workflows.length > 0 ? model.workflows : HR_STAFF_GOVERNANCE_WORKFLOWS.slice(0, 2)} />
        </div>

        <div className="grid gap-4 lg:grid-cols-2 xl:grid-cols-3">
          <HrMetricCard label="fakeMetrics" value={String(fakeMetrics)} helperText="All dashboard-like surfaces expose fakeMetrics=false." />
          <HrMetricCard label="fakeHrData" value={String(HR_STAFF_GOVERNANCE_SAFETY_FLAGS.fake_hr_data)} helperText="No fake HR records or demo payroll data are generated." />
          <HrMetricCard label="humanReviewRequired" value={String(HR_STAFF_GOVERNANCE_SAFETY_FLAGS.human_review_required)} helperText={model.incompleteDataMessage} />
        </div>

        <div className="grid gap-4 xl:grid-cols-2">
          <HrReviewActionPanel title="Human review boundary" permission={model.route.requiredPermission} description={model.noOverclaimAssertions.join(' ')} />
          <HrLimitationsPanel limitations={[...HR_STAFF_GOVERNANCE_SAFETY_FLAGS.limitations, ...model.noOverclaimAssertions]} />
        </div>

        {(model.route.key === 'provider-readiness' || model.route.key === 'payroll-readiness' || model.route.key === 'workload-bridge' || model.route.key === 'access-lifecycle' || model.route.key === 'faculty-profile') ? (
          <div className="grid gap-4 lg:grid-cols-2 xl:grid-cols-3">
            {HR_STAFF_GOVERNANCE_PROVIDER_PROFILES.map((profile) => (
              <HrBridgeCard key={profile.key} title={profile.title} description={profile.description} target={profile.key} />
            ))}
          </div>
        ) : null}

        <HrSafetyChecklist />
        <HrNoOverclaimFooter />
      </div>
    </HrStaffGovernancePageShell>
  );
}

export function HrStaffGovernancePageShell({ routeKey, children }: { routeKey: HrRouteKey; children: ReactNode }) {
  const route = getHrRouteDefinition(routeKey);
  return (
    <div className="space-y-6" data-testid="hr-page-shell">
      <header className="space-y-2">
        <p className="text-sm uppercase tracking-[0.2em] text-muted-foreground">HR / Staff Governance Suite</p>
        <h1 className="text-3xl font-semibold">{route.title}</h1>
        <p className="text-sm text-muted-foreground">{route.description}</p>
      </header>

      <nav className="flex flex-wrap gap-2" aria-label="HR staff governance navigation">
        {HR_STAFF_GOVERNANCE_NAV_ITEMS.map((item) => (
          <Link
            key={item.key}
            href={item.href}
            className={`rounded-full border px-3 py-1 text-sm ${item.key === routeKey ? 'bg-primary text-primary-foreground' : 'text-muted-foreground'}`}
          >
            {item.title}
          </Link>
        ))}
      </nav>

      {children}
    </div>
  );
}

export function HrStaffGovernancePage({ routeKey, userPermissions }: { routeKey: HrRouteKey; userPermissions?: string[] }) {
  const model = buildHrPageModel(routeKey);
  if (userPermissions) {
    return hasHrPermission(userPermissions, model.route.requiredPermission)
      ? <HrPageContent model={model} />
      : <HrPermissionDeniedPanel permission={model.route.requiredPermission} />;
  }

  return (
    <RequirePermission permission={model.route.requiredPermission} message="This HR route is fail-closed until the required permission is granted.">
      <HrPageContent model={model} />
    </RequirePermission>
  );
}

export function HrStaffGovernanceOverviewPage() { return <HrStaffGovernancePage routeKey="overview" />; }
export function HrStaffGovernanceDashboardPage() { return <HrStaffGovernancePage routeKey="dashboard" />; }
export function HrStaffGovernanceRecruitmentPage() { return <HrStaffGovernancePage routeKey="recruitment" />; }
export function HrStaffGovernanceOnboardingPage() { return <HrStaffGovernancePage routeKey="onboarding" />; }
export function HrStaffGovernanceEmployeeRecordsPage() { return <HrStaffGovernancePage routeKey="employee-records" />; }
export function HrStaffGovernanceStaffProfilesPage() { return <HrStaffGovernancePage routeKey="staff-profiles" />; }
export function HrStaffGovernanceFacultyProfilePage() { return <HrStaffGovernancePage routeKey="faculty-profile" />; }
export function HrStaffGovernanceLeavePage() { return <HrStaffGovernancePage routeKey="leave" />; }
export function HrStaffGovernancePerformancePage() { return <HrStaffGovernancePage routeKey="performance" />; }
export function HrStaffGovernanceTrainingPage() { return <HrStaffGovernancePage routeKey="training" />; }
export function HrStaffGovernanceRequestsPage() { return <HrStaffGovernancePage routeKey="requests" />; }
export function HrStaffGovernanceAppealsPage() { return <HrStaffGovernancePage routeKey="appeals" />; }
export function HrStaffGovernancePolicyExceptionsPage() { return <HrStaffGovernancePage routeKey="policy-exceptions" />; }
export function HrStaffGovernanceDisciplinaryPage() { return <HrStaffGovernancePage routeKey="disciplinary" />; }
export function HrStaffGovernanceOffboardingPage() { return <HrStaffGovernancePage routeKey="offboarding" />; }
export function HrStaffGovernanceAccessLifecyclePage() { return <HrStaffGovernancePage routeKey="access-lifecycle" />; }
export function HrStaffGovernanceWorkloadBridgePage() { return <HrStaffGovernancePage routeKey="workload-bridge" />; }
export function HrStaffGovernancePayrollReadinessPage() { return <HrStaffGovernancePage routeKey="payroll-readiness" />; }
export function HrStaffGovernanceProviderReadinessPage() { return <HrStaffGovernancePage routeKey="provider-readiness" />; }
export function HrStaffGovernanceLimitationsPage() { return <HrStaffGovernancePage routeKey="limitations" />; }

export { HR_STAFF_GOVERNANCE_BOUNDARY_COPY, HR_STAFF_GOVERNANCE_FORBIDDEN_LABELS };

void HR_STAFF_GOVERNANCE_BOUNDARY_LABELS;
void HR_STAFF_GOVERNANCE_FORBIDDEN_LABELS;