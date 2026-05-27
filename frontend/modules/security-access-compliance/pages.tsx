'use client';

import Link from 'next/link';
import type { ReactNode } from 'react';
import { useAdminAuth } from '@/shared/auth/context';
import {
  SECURITY_ACCESS_COMPLIANCE_API_BASE,
  SECURITY_ACCESS_COMPLIANCE_BACKEND_ROUTE_COUNT,
  SECURITY_ACCESS_COMPLIANCE_PLANNED_ROUTE_COUNT,
  SECURITY_ACCESS_COMPLIANCE_ROUTE_DEFINITIONS,
  SECURITY_ACCESS_COMPLIANCE_RUNTIME_MODE,
  SECURITY_ACCESS_COMPLIANCE_SOURCE_BACKEND_B1_COMMIT,
  SECURITY_ACCESS_COMPLIANCE_SOURCE_BACKEND_RUNTIME_COMMIT,
  SECURITY_ACCESS_COMPLIANCE_TABLE_COUNT,
} from './constants';
import { SECURITY_ACCESS_COMPLIANCE_BOUNDARY_LABELS, SECURITY_ACCESS_COMPLIANCE_NO_OVERCLAIM_COPY } from './boundaryLabels';
import { hasSacPermission, hasAnySacPermission, getAllowedSacRoutes } from './guards';
import type {
  SacDashboardWidget,
  SacPageModel,
  SacRouteDefinition,
  SacRouteKey,
} from './types';

type RouteState = {
  incompleteData?: boolean;
  userPermissions?: string[];
};

function slugify(value: string) {
  return value.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/(^-|-$)/g, '');
}

export function getSacRouteDefinition(routeKey: SacRouteKey): SacRouteDefinition {
  const route = SECURITY_ACCESS_COMPLIANCE_ROUTE_DEFINITIONS.find((item) => item.key === routeKey);
  if (!route) throw new Error(`Unknown Security / Access / Compliance route key: ${routeKey}`);
  return route;
}

export function buildSacPageModel(routeKey: SacRouteKey): SacPageModel {
  const route = getSacRouteDefinition(routeKey);
  return {
    ...route,
    backendApiBase: SECURITY_ACCESS_COMPLIANCE_API_BASE,
    humanReviewRequired: true,
  };
}

export function SacBoundaryBanner({ labels }: { labels: string[] }) {
  return (
    <section className="rounded-xl border border-amber-200 bg-amber-50 p-4" data-testid="sac-boundary-banner">
      <div className="flex flex-wrap gap-2">
        {labels.map((label) => (
          <span key={label} data-testid={`sac-boundary-${slugify(label)}`} className="inline-flex rounded-full border border-amber-300 px-3 py-1 text-xs font-medium text-amber-950">
            {label}
          </span>
        ))}
      </div>
    </section>
  );
}

export function SacReadinessCard({ title, description }: { title: string; description: string }) {
  return (
    <article className="rounded-xl border bg-card p-4" data-testid={`sac-readiness-${slugify(title)}`}>
      <h3 className="text-base font-semibold">{title}</h3>
      <p className="mt-2 text-sm text-muted-foreground">{description}</p>
    </article>
  );
}

export function SacDashboardGrid({ widgets }: { widgets: SacDashboardWidget[] }) {
  return (
    <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-3" data-testid="sac-dashboard-grid">
      {widgets.map((widget) => (
        <article key={widget.key} className="rounded-xl border bg-card p-4" data-testid={`sac-widget-${widget.key}`}>
          <h3 className="text-base font-semibold">{widget.title}</h3>
          <p className="mt-1 text-sm text-muted-foreground">{widget.description}</p>
          <ul className="mt-3 space-y-1 text-xs text-muted-foreground">
            {widget.backendEndpoints.map((endpoint) => <li key={endpoint}>{endpoint}</li>)}
          </ul>
          <p className="mt-3 text-xs text-muted-foreground">Required permission: {widget.requiredPermission}</p>
        </article>
      ))}
    </section>
  );
}

export function SacMetricCard({ label, value }: { label: string; value: string }) {
  return (
    <article className="rounded-xl border bg-card p-4" data-testid={`sac-metric-${slugify(label)}`}>
      <div className="text-xs uppercase tracking-wide text-muted-foreground">{label}</div>
      <div className="mt-2 text-2xl font-semibold">{value}</div>
    </article>
  );
}

export function SacEvidenceStatusBadge({ status }: { status: string }) {
  return <span className="rounded-full border px-2 py-1 text-xs font-medium" data-testid="sac-evidence-status-badge">{status}</span>;
}

export function SacHumanReviewBadge() {
  return <span className="rounded-full border border-blue-300 bg-blue-50 px-2 py-1 text-xs font-medium text-blue-900" data-testid="sac-human-review-badge">Human review required</span>;
}

export function SacComplianceReadinessBadge() {
  return <span className="rounded-full border border-slate-300 px-2 py-1 text-xs font-medium" data-testid="sac-compliance-readiness-badge">readiness/evidence only</span>;
}

export function SacIncidentMetadataBadge() {
  return <span className="rounded-full border border-slate-300 px-2 py-1 text-xs font-medium" data-testid="sac-incident-metadata-badge">metadata-only</span>;
}

export function SacPermissionDeniedPanel({ permission }: { permission: string }) {
  return (
    <div className="rounded-xl border border-destructive/30 bg-destructive/5 p-6" data-testid="sac-permission-denied-panel">
      <h2 className="text-lg font-semibold">Permission required</h2>
      <p className="mt-2 text-sm text-muted-foreground">This route is fail-closed and requires {permission}.</p>
    </div>
  );
}

export function SacIncompleteDataNotice() {
  return (
    <div className="rounded-xl border border-dashed p-4 text-sm text-muted-foreground" data-testid="sac-incomplete-data-notice">
      incompleteData supported. Missing fields stay visible instead of being replaced with fake values.
    </div>
  );
}

export function SacLimitationsPanel({ limitations }: { limitations: string[] }) {
  return (
    <section className="rounded-xl border bg-card p-4" data-testid="sac-limitations-panel">
      <h3 className="text-base font-semibold">Limitations</h3>
      <ul className="mt-3 space-y-2 text-sm text-muted-foreground">
        {limitations.map((limitation) => <li key={limitation}>{limitation}</li>)}
      </ul>
    </section>
  );
}

export function SacAuditTimeline({ items }: { items: string[] }) {
  return (
    <section className="rounded-xl border bg-card p-4" data-testid="sac-audit-timeline">
      <h3 className="text-base font-semibold">Audit / Review Timeline</h3>
      <ol className="mt-3 space-y-2 text-sm text-muted-foreground">
        {items.map((item) => <li key={item}>{item}</li>)}
      </ol>
    </section>
  );
}

export function SacEvidenceTable({ endpoints }: { endpoints: string[] }) {
  return (
    <section className="rounded-xl border bg-card p-4" data-testid="sac-evidence-table">
      <h3 className="text-base font-semibold">Evidence / Endpoint Contract</h3>
      <ul className="mt-3 space-y-2 text-sm text-muted-foreground">
        {endpoints.map((endpoint) => <li key={endpoint}>{endpoint}</li>)}
      </ul>
    </section>
  );
}

export function SacBridgeCard({ title, description, target }: { title: string; description: string; target: string }) {
  return (
    <article className="rounded-xl border bg-card p-4" data-testid={`sac-bridge-${slugify(target)}`}>
      <h3 className="text-base font-semibold">{title}</h3>
      <p className="mt-2 text-sm text-muted-foreground">{description}</p>
      <p className="mt-3 text-xs text-muted-foreground">Bridge target: {target}</p>
    </article>
  );
}

export function SacMetadataFormShell({ title, description, endpoints, testId }: { title: string; description: string; endpoints: string[]; testId?: string }) {
  return (
    <section className="rounded-xl border bg-card p-4" data-testid={testId ? `sac-form-shell-${testId}` : `sac-form-shell-${slugify(title)}`}>
      <h3 className="text-base font-semibold">{title}</h3>
      <p className="mt-2 text-sm text-muted-foreground">{description}</p>
      <ul className="mt-3 space-y-1 text-sm text-muted-foreground">
        {endpoints.map((endpoint) => <li key={endpoint}>{endpoint}</li>)}
      </ul>
    </section>
  );
}

export function SacSafetyChecklist() {
  return (
    <section className="rounded-xl border bg-card p-4" data-testid="sac-safety-checklist">
      <h3 className="text-base font-semibold">Safety Checklist</h3>
      <ul className="mt-3 grid gap-2 text-sm text-muted-foreground md:grid-cols-2">
        <li>fakeSecurityCertification=false</li>
        <li>fakeComplianceCertification=false</li>
        <li>legalRegulatoryComplianceClaimed=false</li>
        <li>socSiemReplacementClaimed=false</li>
        <li>fakeIncidentResolution=false</li>
        <li>fakeAuditProof=false</li>
        <li>fakeRiskScore=false</li>
        <li>hiddenUserRiskScorePresent=false</li>
        <li>discriminatoryRankingPresent=false</li>
        <li>autonomousEnforcementEnabled=false</li>
        <li>automaticUserBlockingEnabled=false</li>
        <li>automaticUserSanctionEnabled=false</li>
        <li>automaticDataDeletionEnabled=false</li>
        <li>externalRegulatorSubmissionEnabled=false</li>
        <li>productionSecurityClaimed=false</li>
        <li>humanReviewRequired=true</li>
      </ul>
    </section>
  );
}

export function SacNoOverclaimFooter() {
  return (
    <footer className="rounded-xl border border-dashed p-4 text-sm text-muted-foreground" data-testid="sac-no-overclaim-footer">
      {SECURITY_ACCESS_COMPLIANCE_NO_OVERCLAIM_COPY.map((line: string) => <p key={line}>{line}</p>)}
    </footer>
  );
}

export function SecurityAccessCompliancePageShell({ routeKey, children }: { routeKey: SacRouteKey; children: ReactNode }) {
  const route = getSacRouteDefinition(routeKey);
  return (
    <div className="space-y-6" data-testid="sac-page-shell">
      <header className="space-y-2">
        <p className="text-sm uppercase tracking-[0.2em] text-muted-foreground">Security / Access / Compliance Suite</p>
        <h1 className="text-3xl font-semibold">{route.title}</h1>
        <p className="text-sm text-muted-foreground">{route.route}</p>
      </header>

      <nav className="flex flex-wrap gap-2" aria-label="Security access compliance navigation">
        {SECURITY_ACCESS_COMPLIANCE_ROUTE_DEFINITIONS.map((item) => (
          <Link key={item.key} href={item.route} className={`rounded-full border px-3 py-1 text-sm ${item.key === routeKey ? 'bg-primary text-primary-foreground' : 'text-muted-foreground'}`}>
            {item.title}
          </Link>
        ))}
      </nav>

      {children}
    </div>
  );
}

function buildWidgets(route: SacRouteDefinition): SacDashboardWidget[] {
  return route.primaryWidgets.map((key, index) => ({
    key: `${route.key}-${index}`,
    title: key.replace(/-/g, ' ').replace(/\b\w/g, (letter) => letter.toUpperCase()),
    description: `${route.title} surface ${index + 1}.`,
    backendEndpoints: route.backendEndpoints,
    requiredPermission: route.requiredPermission,
  }));
}

function getRouteSpecificBody(route: SacRouteDefinition) {
  switch (route.key) {
    case 'overview':
      return <SacDashboardGrid widgets={buildWidgets(route)} />;
    case 'dashboard':
      return (
        <div className="space-y-4">
          <SacDashboardGrid widgets={buildWidgets(route)} />
          <div className="grid gap-4 md:grid-cols-3">
            <SacMetricCard label="Backend route count" value={String(SECURITY_ACCESS_COMPLIANCE_BACKEND_ROUTE_COUNT)} />
            <SacMetricCard label="Table count" value={String(SECURITY_ACCESS_COMPLIANCE_TABLE_COUNT)} />
            <SacMetricCard label="Planned frontend routes" value={String(SECURITY_ACCESS_COMPLIANCE_PLANNED_ROUTE_COUNT)} />
          </div>
          <SacSafetyChecklist />
        </div>
      );
    case 'roles-permissions':
      return <SacEvidenceTable endpoints={route.backendEndpoints} />;
    case 'rbac-abac':
      return <SacEvidenceTable endpoints={route.backendEndpoints} />;
    case 'access-governance':
      return <SacReadinessCard title="Access Governance" description="Metadata and evidence only. Human review required for every surface." />;
    case 'sessions':
    case 'login-events':
    case 'tenant-isolation':
    case 'mfa-readiness':
      return <SacEvidenceTable endpoints={route.backendEndpoints} />;
    case 'incidents':
    case 'incident-review':
    case 'remediation':
    case 'risks':
    case 'compliance-controls':
    case 'policy-controls':
    case 'audit-events':
    case 'sensitive-actions':
    case 'data-protection':
    case 'privacy-readiness':
    case 'exceptions':
    case 'visitor-access':
      return (
        <div className="space-y-4">
          <SacEvidenceTable endpoints={route.backendEndpoints} />
          <SacMetadataFormShell testId={route.key} title={route.title} description="Metadata/evidence shell only. No action buttons or autonomous execution." endpoints={route.backendEndpoints} />
        </div>
      );
    case 'bridges':
      return (
        <div className="grid gap-4 md:grid-cols-2">
          <SacBridgeCard title="HR bridge" description="Metadata-only bridge to HR readiness inputs." target="hr" />
          <SacBridgeCard title="Finance bridge" description="Metadata-only bridge to finance readiness inputs." target="finance" />
          <SacBridgeCard title="Documents bridge" description="Metadata-only bridge to document evidence inputs." target="documents" />
          <SacBridgeCard title="Student services bridge" description="Metadata-only bridge to student-services readiness inputs." target="student-services" />
        </div>
      );
    case 'limitations':
      return <SacLimitationsPanel limitations={route.noOverclaimFooter} />;
    default:
      return <SacEvidenceTable endpoints={route.backendEndpoints} />;
  }
}

function SecurityAccessCompliancePageContent({ routeKey, userPermissions }: { routeKey: SacRouteKey; userPermissions: string[] }) {
  const route = getSacRouteDefinition(routeKey);
  const allowedRoutes = getAllowedSacRoutes(userPermissions);
  const canView = hasSacPermission(userPermissions, route.requiredPermission) || hasAnySacPermission(userPermissions, [route.requiredPermission]) || allowedRoutes.some((item) => item.key === routeKey);

  if (!canView) {
    return (
      <div data-testid="sac-permission-denied-panel-wrap">
        <SacPermissionDeniedPanel permission={route.requiredPermission} />
      </div>
    );
  }

  return (
    <SecurityAccessCompliancePageShell routeKey={routeKey}>
      <div className="space-y-4" data-testid={`sac-page-${route.key}`}>
        <SacBoundaryBanner labels={route.safetyBoundaryLabels} />
        <div className="flex flex-wrap items-center gap-3">
          <SacHumanReviewBadge />
          <SacComplianceReadinessBadge />
          <SacIncidentMetadataBadge />
        </div>
        <SacIncompleteDataNotice />
        {getRouteSpecificBody(route)}
        <section className="rounded-xl border bg-card p-4 text-sm text-muted-foreground" data-testid="sac-route-contract-panel">
          <p>Route: {route.route}</p>
          <p>Required permission: {route.requiredPermission}</p>
          <p>Runtime mode: {SECURITY_ACCESS_COMPLIANCE_RUNTIME_MODE}</p>
          <p>Backend API base: {SECURITY_ACCESS_COMPLIANCE_API_BASE}</p>
          <p>Source runtime commit: {SECURITY_ACCESS_COMPLIANCE_SOURCE_BACKEND_RUNTIME_COMMIT}</p>
          <p>Source B1 commit: {SECURITY_ACCESS_COMPLIANCE_SOURCE_BACKEND_B1_COMMIT}</p>
        </section>
        {route.key !== 'limitations' ? <SacNoOverclaimFooter /> : null}
      </div>
    </SecurityAccessCompliancePageShell>
  );
}

function SecurityAccessCompliancePageRuntime({ routeKey }: { routeKey: SacRouteKey }) {
  const { user } = useAdminAuth();
  return <SecurityAccessCompliancePageContent routeKey={routeKey} userPermissions={user?.permissions ?? []} />;
}

export function SecurityAccessCompliancePage({ routeKey, userPermissions }: { routeKey: SacRouteKey; userPermissions?: string[] }) {
  if (userPermissions) {
    return <SecurityAccessCompliancePageContent routeKey={routeKey} userPermissions={userPermissions} />;
  }

  return <SecurityAccessCompliancePageRuntime routeKey={routeKey} />;
}
