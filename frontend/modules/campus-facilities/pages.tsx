'use client';

import Link from 'next/link';
import { useState, type ReactNode } from 'react';
import { useAdminAuth } from '@/shared/auth/context';
import {
  DateRangeFilter,
  EvidenceUploadPanel,
  ExportButton,
  FilterBar,
  KPIGrid,
  MetricCard,
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
  CAMPUS_FACILITIES_API_BASE,
  CAMPUS_FACILITIES_BACKEND_ROUTE_COUNT,
  CAMPUS_FACILITIES_BRIDGE_DEFINITIONS,
  CAMPUS_FACILITIES_DASHBOARD_CARDS,
  CAMPUS_FACILITIES_LIMITATIONS,
  CAMPUS_FACILITIES_PERMISSION_COUNT,
  CAMPUS_FACILITIES_PLANNED_ROUTE_COUNT,
  CAMPUS_FACILITIES_ROUTE_DEFINITIONS,
  CAMPUS_FACILITIES_TABLE_COUNT,
  RUNTIME_MODE,
} from './constants';
import { CAMPUS_FACILITIES_NO_OVERCLAIM_COPY } from './boundaryLabels';
import {
  canReadCampusFacilitiesRoute,
  getAllowedCampusFacilitiesRoutes,
} from './guards';
import type {
  CampusFacilitiesDashboardCard,
  CampusFacilitiesPageModel,
  CampusFacilitiesRouteDefinition,
  CampusFacilitiesRouteKey,
} from './types';

function slugify(value: string) {
  return value.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/(^-|-$)/g, '');
}

export function getCampusFacilitiesRouteDefinition(routeKey: CampusFacilitiesRouteKey): CampusFacilitiesRouteDefinition {
  const route = CAMPUS_FACILITIES_ROUTE_DEFINITIONS.find((item) => item.routeKey === routeKey);
  if (!route) throw new Error(`Unknown Campus Facilities route key: ${routeKey}`);
  return route;
}

export function buildCampusFacilitiesPageModel(routeKey: CampusFacilitiesRouteKey): CampusFacilitiesPageModel {
  const route = getCampusFacilitiesRouteDefinition(routeKey);
  return {
    ...route,
    backendApiBase: CAMPUS_FACILITIES_API_BASE,
  };
}

export function CampusFacilitiesRouteHeader({ route }: { route: CampusFacilitiesRouteDefinition }) {
  return (
    <header className="space-y-2" data-testid="campus-facilities-route-header">
      <p className="text-sm uppercase tracking-[0.2em] text-muted-foreground">Campus / Facilities / Housing / Transport Suite</p>
      <h1 className="text-3xl font-semibold">{route.title}</h1>
      <p className="text-sm text-muted-foreground">{route.description}</p>
    </header>
  );
}

export function CampusFacilitiesBoundaryBanner({ labels }: { labels: string[] }) {
  return (
    <section className="rounded-xl border border-amber-200 bg-amber-50 p-4" data-testid="campus-facilities-boundary-banner">
      <div className="flex flex-wrap gap-2">
        {labels.map((label) => (
          <span key={label} data-testid={`campus-facilities-boundary-${slugify(label)}`} className="inline-flex rounded-full border border-amber-300 px-3 py-1 text-xs font-medium text-amber-950">
            {label}
          </span>
        ))}
      </div>
    </section>
  );
}

export function CampusFacilitiesDashboardCards({ cards }: { cards: CampusFacilitiesDashboardCard[] }) {
  return (
    <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4" data-testid="campus-facilities-dashboard-cards">
      {cards.map((card) => (
        <article key={card.key} className="rounded-xl border bg-card p-4" data-testid={`campus-facilities-dashboard-card-${card.key}`}>
          <h3 className="text-base font-semibold">{card.title}</h3>
          <p className="mt-1 text-sm text-muted-foreground">{card.description}</p>
          <ul className="mt-3 space-y-1 text-xs text-muted-foreground">
            {card.backendEndpoints.map((endpoint) => <li key={endpoint}>{endpoint}</li>)}
          </ul>
        </article>
      ))}
    </section>
  );
}

export function CampusFacilitiesMetadataPanel({ route }: { route: CampusFacilitiesRouteDefinition }) {
  return (
    <section className="rounded-xl border bg-card p-4" data-testid="campus-facilities-metadata-panel">
      <h3 className="text-base font-semibold">Metadata and Readiness Contract</h3>
      <ul className="mt-3 space-y-1 text-sm text-muted-foreground">
        <li>Route group: {route.endpointGroup}</li>
        <li>Required permission: {route.requiredPermission}</li>
        <li>Backend API base: {CAMPUS_FACILITIES_API_BASE}</li>
        <li>Runtime mode: {RUNTIME_MODE}</li>
      </ul>
      <ul className="mt-3 space-y-1 text-xs text-muted-foreground">
        {route.backendEndpoints.map((endpoint) => <li key={endpoint}>{endpoint}</li>)}
      </ul>
    </section>
  );
}

export function CampusFacilitiesBridgePanel() {
  return (
    <section className="rounded-xl border bg-card p-4" data-testid="campus-facilities-bridge-panel">
      <h3 className="text-base font-semibold">Bridge Contracts</h3>
      <div className="mt-3 grid gap-3 md:grid-cols-2">
        {CAMPUS_FACILITIES_BRIDGE_DEFINITIONS.map((bridge) => (
          <article key={bridge.key} className="rounded-lg border p-3" data-testid={`campus-facilities-bridge-${bridge.key}`}>
            <p className="font-medium">{bridge.title}</p>
            <p className="text-xs text-muted-foreground">{bridge.backendEndpoint}</p>
          </article>
        ))}
      </div>
    </section>
  );
}

export function CampusFacilitiesLimitationsPanel({ limitations }: { limitations: readonly string[] }) {
  return (
    <section className="rounded-xl border bg-card p-4" data-testid="campus-facilities-limitations-panel">
      <h3 className="text-base font-semibold">Limitations</h3>
      <ul className="mt-3 space-y-2 text-sm text-muted-foreground">
        {limitations.map((item) => <li key={item}>{item}</li>)}
      </ul>
    </section>
  );
}

export function CampusFacilitiesNoOverclaimFooter() {
  return (
    <footer className="rounded-xl border border-dashed p-4 text-sm text-muted-foreground" data-testid="campus-facilities-no-overclaim-footer">
      {CAMPUS_FACILITIES_NO_OVERCLAIM_COPY.map((line) => <p key={line}>{line}</p>)}
    </footer>
  );
}

function CampusFacilitiesPermissionDeniedPanel({ permission }: { permission: string }) {
  return (
    <PermissionDeniedState role="tenant_admin" requiredPermission={permission} reason="This campus/facilities view is fail-closed for the current permission set." />
  );
}

function CampusFacilitiesShell({ routeKey, children }: { routeKey: CampusFacilitiesRouteKey; children: ReactNode }) {
  const currentRoute = getCampusFacilitiesRouteDefinition(routeKey);
  const [search, setSearch] = useState('');
  const [status, setStatus] = useState('');
  const [range, setRange] = useState({ from: '', to: '' });

  return (
    <div className="space-y-6" data-testid="campus-facilities-page-shell">
      <PageShell>
      <SectionHeader eyebrow="Campus / Facilities / Housing / Transport Suite" title={currentRoute.title} description={currentRoute.description} />
      <PageToolbar
        left={
          <PageActions>
            <PageActionBar
              secondaryActions={[
                { id: 'edit', label: 'Edit', disabled: true, disabledReason: 'No shell-level edit workflow.' },
                { id: 'refresh', label: 'Refresh', disabled: true, disabledReason: 'Use route-native refresh behavior.' },
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
        <StatusFilter value={status} onChange={setStatus} options={[{ value: 'active', label: 'Active' }, { value: 'planned', label: 'Planned' }]} />
        <DateRangeFilter value={range} onChange={setRange} />
      </FilterBar>
      <CampusFacilitiesRouteHeader route={currentRoute} />
      <nav className="flex flex-wrap gap-2" aria-label="Campus facilities navigation">
        {CAMPUS_FACILITIES_ROUTE_DEFINITIONS.map((route) => (
          <Link key={route.routeKey} href={route.path} className={`rounded-full border px-3 py-1 text-sm ${route.routeKey === routeKey ? 'bg-primary text-primary-foreground' : 'text-muted-foreground'}`}>
            {route.title}
          </Link>
        ))}
      </nav>
        <EvidenceUploadPanel uploadSupported={false} limitationLabel="Evidence upload remains disabled unless a route-specific backend contract is available." />
        {children}
      </PageShell>
    </div>
  );
}

function routeCards(route: CampusFacilitiesRouteDefinition): CampusFacilitiesDashboardCard[] {
  return route.backendEndpoints.map((endpoint, index) => ({
    key: `${route.routeKey}-${index}`,
    title: `${route.title} card ${index + 1}`,
    description: 'Metadata/readiness surface only.',
    backendEndpoints: [endpoint],
    requiredPermission: route.requiredPermission,
  }));
}

function CampusFacilitiesPageContent({ routeKey, userPermissions }: { routeKey: CampusFacilitiesRouteKey; userPermissions: string[] }) {
  const route = getCampusFacilitiesRouteDefinition(routeKey);
  const allowedRoutes = getAllowedCampusFacilitiesRoutes(userPermissions);
  const canView = canReadCampusFacilitiesRoute(routeKey, userPermissions) || allowedRoutes.some((item) => item.routeKey === routeKey);

  if (!canView) return <CampusFacilitiesPermissionDeniedPanel permission={route.requiredPermission} />;

  return (
    <CampusFacilitiesShell routeKey={routeKey}>
      <div className="space-y-4" data-testid={`campus-facilities-page-${route.routeKey}`}>
        <CampusFacilitiesBoundaryBanner labels={route.boundaryLabels} />
        <div className="rounded-xl border border-dashed p-4 text-sm text-muted-foreground" data-testid="campus-facilities-incomplete-data-notice">
          incompleteData supported. Missing fields remain explicit and are never replaced with fake values.
        </div>
        <KPIGrid>
          <MetricCard label="Backend routes" value={CAMPUS_FACILITIES_BACKEND_ROUTE_COUNT} source="campus_facilities_contract" timestamp="runtime" limitations={["metadata_only"]} incompleteData={true} />
          <MetricCard label="Tables" value={CAMPUS_FACILITIES_TABLE_COUNT} source="campus_facilities_contract" timestamp="runtime" limitations={["metadata_only"]} incompleteData={true} />
          <MetricCard label="Permissions" value={CAMPUS_FACILITIES_PERMISSION_COUNT} source="campus_facilities_contract" timestamp="runtime" limitations={["metadata_only"]} incompleteData={true} />
          <MetricCard label="Frontend routes" value={CAMPUS_FACILITIES_PLANNED_ROUTE_COUNT} source="campus_facilities_contract" timestamp="runtime" limitations={["metadata_only"]} incompleteData={true} />
        </KPIGrid>
        <CampusFacilitiesDashboardCards cards={route.dashboardLike ? CAMPUS_FACILITIES_DASHBOARD_CARDS : routeCards(route)} />
        <CampusFacilitiesMetadataPanel route={route} />
        {route.bridgeRoute ? <CampusFacilitiesBridgePanel /> : null}
        {route.routeKey === 'limitations' ? <CampusFacilitiesLimitationsPanel limitations={CAMPUS_FACILITIES_LIMITATIONS} /> : null}
        <CampusFacilitiesNoOverclaimFooter />
      </div>
    </CampusFacilitiesShell>
  );
}

function CampusFacilitiesPageRuntime({ routeKey }: { routeKey: CampusFacilitiesRouteKey }) {
  const { user } = useAdminAuth();
  return <CampusFacilitiesPageContent routeKey={routeKey} userPermissions={user?.permissions ?? []} />;
}

export function CampusFacilitiesPage({ routeKey, userPermissions }: { routeKey: CampusFacilitiesRouteKey; userPermissions?: string[] }) {
  if (userPermissions) {
    return <CampusFacilitiesPageContent routeKey={routeKey} userPermissions={userPermissions} />;
  }
  return <CampusFacilitiesPageRuntime routeKey={routeKey} />;
}

export { CAMPUS_FACILITIES_ROUTE_DEFINITIONS } from './constants';
