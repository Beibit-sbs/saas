'use client';

import { Children, type ReactNode } from 'react';
import Link from 'next/link';
import { useQuery } from '@tanstack/react-query';
import { RequirePermission } from '@/shared/ui/permission-gate';
import { ErrorState, LoadingState } from '@/shared/ui/page-states';
import { cn } from '@/shared/utils/cn';
import { researchScienceApi } from './api';
import {
  EXPECTED_DATA_SOURCE,
  MASTER_MATRIX_COMMIT,
  MASTER_MATRIX_ROW_COUNT,
  RESEARCH_SCIENCE_BACKEND_PERMISSION_COUNT,
  RESEARCH_SCIENCE_BACKEND_ROUTE_COUNT,
  RESEARCH_SCIENCE_BRIDGE_TARGETS,
  RESEARCH_SCIENCE_DASHBOARD_SECTIONS,
  RESEARCH_SCIENCE_LIMITATIONS,
  RESEARCH_SCIENCE_NAV_ITEMS,
  RESEARCH_SCIENCE_PAGE_TITLES,
  RESEARCH_SCIENCE_ROUTES,
  RESEARCH_SCIENCE_TABLE_COUNT,
  RUNTIME_MODE,
} from './constants';
import {
  RESEARCH_SCIENCE_BOUNDARY_LABELS,
  type ResearchSciencePageKey,
} from './boundaryLabels';
import {
  RESEARCH_SCIENCE_PERMISSIONS,
  ResearchScienceDataQualityError,
  assertTrustedResearchScienceDashboard,
  assertTrustedResearchScienceHealth,
  assertTrustedResearchScienceMatrixSummary,
  getResearchScienceBoundaryLabels,
} from './guards';
import type {
  ConferenceParticipation,
  GrantApplication,
  GrantDeliverable,
  PublicationMetadata,
  ResearchAuditEvent,
  ResearchBridge,
  ResearchBridgeSummary,
  ResearchEthicsAmendment,
  ResearchEthicsRequest,
  ResearchEvidence,
  ResearchProject,
  ResearchScienceDashboardResponse,
  ResearchScienceHealthResponse,
  ResearchScienceLimitationsResponse,
  ResearchScienceMatrixSummaryResponse,
  ScientificSupervision,
  StudentResearchWork,
} from './types';

const CACHE_KEYS = {
  health: ['research-science:health'] as const,
  dashboard: ['research-science:dashboard'] as const,
  matrixSummary: ['research-science:matrix-summary'] as const,
  limitations: ['research-science:limitations'] as const,
  projects: ['research-science:projects'] as const,
  studentResearch: ['research-science:student-research'] as const,
  supervision: ['research-science:supervision'] as const,
  publications: ['research-science:publications'] as const,
  conferences: ['research-science:conferences'] as const,
  grants: ['research-science:grants'] as const,
  grantDeliverables: ['research-science:grant-deliverables'] as const,
  ethics: ['research-science:ethics'] as const,
  ethicsAmendments: ['research-science:ethics-amendments'] as const,
  evidence: ['research-science:evidence'] as const,
  audit: ['research-science:audit'] as const,
  bridges: ['research-science:bridges'] as const,
  bridgesSummary: ['research-science:bridges-summary'] as const,
};

function slugify(value: string) {
  return value.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');
}

function useTrustedResearchScienceHealth() {
  return useQuery({
    queryKey: CACHE_KEYS.health,
    queryFn: async () => {
      const payload = await researchScienceApi.getResearchScienceHealth();
      assertTrustedResearchScienceHealth(payload);
      return payload;
    },
    staleTime: 60000,
  });
}

function useTrustedResearchScienceDashboard() {
  return useQuery({
    queryKey: CACHE_KEYS.dashboard,
    queryFn: async () => {
      const payload = await researchScienceApi.getResearchScienceDashboard();
      assertTrustedResearchScienceDashboard(payload);
      return payload;
    },
    staleTime: 60000,
  });
}

function useTrustedResearchScienceMatrixSummary() {
  return useQuery({
    queryKey: CACHE_KEYS.matrixSummary,
    queryFn: async () => {
      const payload = await researchScienceApi.getResearchScienceMatrixSummary();
      assertTrustedResearchScienceMatrixSummary(payload);
      return payload;
    },
    staleTime: 60000,
  });
}

function useResearchScienceLimitations() {
  return useQuery({
    queryKey: CACHE_KEYS.limitations,
    queryFn: async () => (await researchScienceApi.getResearchScienceLimitations()).items,
    staleTime: 60000,
  });
}

function useResearchProjects() {
  return useQuery({ queryKey: CACHE_KEYS.projects, queryFn: async () => (await researchScienceApi.listResearchProjects()).items, staleTime: 30000 });
}

function useStudentResearchWorkItems() {
  return useQuery({ queryKey: CACHE_KEYS.studentResearch, queryFn: async () => (await researchScienceApi.listStudentResearchWork()).items, staleTime: 30000 });
}

function useScientificSupervisionItems() {
  return useQuery({ queryKey: CACHE_KEYS.supervision, queryFn: async () => (await researchScienceApi.listScientificSupervision()).items, staleTime: 30000 });
}

function usePublicationMetadataItems() {
  return useQuery({ queryKey: CACHE_KEYS.publications, queryFn: async () => (await researchScienceApi.listPublications()).items, staleTime: 30000 });
}

function useConferenceParticipationItems() {
  return useQuery({ queryKey: CACHE_KEYS.conferences, queryFn: async () => (await researchScienceApi.listConferences()).items, staleTime: 30000 });
}

function useGrantApplicationItems() {
  return useQuery({ queryKey: CACHE_KEYS.grants, queryFn: async () => (await researchScienceApi.listGrants()).items, staleTime: 30000 });
}

function useGrantDeliverableItems() {
  return useQuery({ queryKey: CACHE_KEYS.grantDeliverables, queryFn: async () => (await researchScienceApi.listGrantDeliverables()).items, staleTime: 30000 });
}

function useResearchEthicsRequests() {
  return useQuery({ queryKey: CACHE_KEYS.ethics, queryFn: async () => (await researchScienceApi.listEthicsRequests()).items, staleTime: 30000 });
}

function useResearchEthicsAmendments() {
  return useQuery({ queryKey: CACHE_KEYS.ethicsAmendments, queryFn: async () => (await researchScienceApi.listEthicsAmendments()).items, staleTime: 30000 });
}

function useResearchEvidenceItems() {
  return useQuery({ queryKey: CACHE_KEYS.evidence, queryFn: async () => (await researchScienceApi.listResearchEvidence()).items, staleTime: 30000 });
}

function useResearchAuditItems() {
  return useQuery({ queryKey: CACHE_KEYS.audit, queryFn: async () => (await researchScienceApi.listResearchAuditEvents()).items, staleTime: 30000 });
}

function useResearchBridgeItems() {
  return useQuery({ queryKey: CACHE_KEYS.bridges, queryFn: async () => (await researchScienceApi.listResearchBridges()).items, staleTime: 30000 });
}

function useResearchBridgeSummary() {
  return useQuery({ queryKey: CACHE_KEYS.bridgesSummary, queryFn: () => researchScienceApi.getResearchBridgeSummary(), staleTime: 30000 });
}

function PageError(message: string, error: unknown) {
  return <ErrorState error={error} message={message} />;
}

export function ResearchSciencePageHeader({ title, description }: { title: string; description: string }) {
  return (
    <header className="space-y-2">
      <h1 className="text-2xl font-semibold">{title}</h1>
      <p className="text-sm text-muted-foreground">{description}</p>
    </header>
  );
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

export function ResearchScienceBoundaryBanner({ labels }: { labels: string[] }) {
  return (
    <section className="rounded-lg border border-amber-200 bg-amber-50/60 p-4" data-testid="research-science-boundary-banner">
      <div className="space-y-1">
        <h2 className="text-sm font-semibold text-amber-950">Research / Science boundaries</h2>
        <p className="text-sm text-amber-900">Metadata and evidence-only runtime. Human-reviewed, read-only-first, and non-provider-executing by default.</p>
      </div>
      <div className="mt-3 flex flex-wrap gap-2">
        {labels.map((label) => (
          <BoundaryBadge key={label} label={label} />
        ))}
      </div>
    </section>
  );
}

export function ResearchScienceMetricCard({ label, value, helper }: { label: string; value: string | number; helper?: string }) {
  return (
    <div className="rounded-lg border p-4">
      <p className="text-sm text-muted-foreground">{label}</p>
      <p className="mt-2 text-2xl font-semibold">{value}</p>
      {helper ? <p className="mt-1 text-xs text-muted-foreground">{helper}</p> : null}
    </div>
  );
}

export function ResearchScienceRegistryPanel({
  title,
  description,
  items,
  emptyMessage,
  renderItem,
  testId,
}: {
  title: string;
  description: string;
  items: readonly unknown[];
  emptyMessage: string;
  renderItem: (item: any, index: number) => ReactNode;
  testId: string;
}) {
  return (
    <section className="rounded-lg border p-4" data-testid={testId}>
      <div className="space-y-1">
        <h2 className="text-lg font-semibold">{title}</h2>
        <p className="text-sm text-muted-foreground">{description}</p>
      </div>
      {items.length === 0 ? (
        <p className="mt-4 text-sm text-muted-foreground">{emptyMessage}</p>
      ) : (
        <div className="mt-4 grid gap-3 md:grid-cols-2">{Children.toArray(items.map((item, index) => renderItem(item, index)))}</div>
      )}
    </section>
  );
}

export function ResearchScienceLimitationsPanel({ limitations }: { limitations: string[] }) {
  return (
    <section className="rounded-lg border p-4" data-testid="research-science-limitations-panel">
      <h2 className="text-lg font-semibold">Limitations</h2>
      <ul className="mt-3 space-y-2 text-sm text-muted-foreground">
        {limitations.map((limitation) => (
          <li key={limitation}>- {limitation}</li>
        ))}
      </ul>
    </section>
  );
}

export function ResearchScienceBridgeCard({ title, description, count }: { title: string; description: string; count?: number }) {
  return (
    <div className="rounded-lg border p-4" data-testid={`research-science-bridge-card-${slugify(title)}`}>
      <h3 className="font-medium">{title}</h3>
      <p className="mt-1 text-sm text-muted-foreground">{description}</p>
      <p className="mt-3 text-sm">Read-only-first. {count !== undefined ? `Tracked links: ${count}.` : 'No cross-suite mutation is allowed.'}</p>
    </div>
  );
}

export function ResearchScienceShell({
  title,
  description,
  currentPath,
  boundaryPage,
  children,
}: {
  title: string;
  description: string;
  currentPath: string;
  boundaryPage: ResearchSciencePageKey;
  children: ReactNode;
}) {
  return (
    <div className="space-y-6" data-testid="research-science-page">
      <ResearchSciencePageHeader title={title} description={description} />

      <nav className="flex flex-wrap gap-2" aria-label="Research Science navigation">
        {RESEARCH_SCIENCE_NAV_ITEMS.map((item) => {
          const active = currentPath === item.href;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                'rounded-full border px-3 py-1.5 text-sm transition-colors',
                active ? 'border-foreground bg-foreground text-background' : 'border-border text-foreground hover:bg-muted',
              )}
            >
              {item.title}
            </Link>
          );
        })}
      </nav>

      <ResearchScienceBoundaryBanner labels={getResearchScienceBoundaryLabels(boundaryPage)} />
      {children}
    </div>
  );
}

function renderMetadataCard(title: string, subtitle: string, details: Array<[string, string | number | null | undefined]>) {
  return (
    <div className="rounded-lg border p-4">
      <h3 className="font-medium">{title}</h3>
      <p className="mt-1 text-sm text-muted-foreground">{subtitle}</p>
      <dl className="mt-3 grid gap-2 text-sm">
        {details.map(([label, value]) => (
          <div key={label} className="grid grid-cols-[140px_1fr] gap-2">
            <dt className="text-muted-foreground">{label}</dt>
            <dd>{value ?? 'n/a'}</dd>
          </div>
        ))}
      </dl>
    </div>
  );
}

function OverviewContent({
  health,
  dashboard,
  matrix,
  limitations,
}: {
  health: ResearchScienceHealthResponse;
  dashboard: ResearchScienceDashboardResponse;
  matrix: ResearchScienceMatrixSummaryResponse;
  limitations: string[];
}) {
  return (
    <div className="space-y-6" data-testid="research-science-overview">
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <ResearchScienceMetricCard label="Backend tables" value={RESEARCH_SCIENCE_TABLE_COUNT} helper="Validated backend foundation" />
        <ResearchScienceMetricCard label="Backend routes" value={RESEARCH_SCIENCE_BACKEND_ROUTE_COUNT} helper="Frontend contract target" />
        <ResearchScienceMetricCard label="Permissions" value={RESEARCH_SCIENCE_BACKEND_PERMISSION_COUNT} helper="research_science.* namespace" />
        <ResearchScienceMetricCard label="Runtime mode" value={RUNTIME_MODE} helper="Evidence metadata only" />
      </div>

      <div className="grid gap-4 xl:grid-cols-2">
        {renderMetadataCard('Validated backend baseline', 'Ground truth carried forward from A-037.2-B1.R1.', [
          ['Matrix commit', MASTER_MATRIX_COMMIT],
          ['Matrix rows', MASTER_MATRIX_ROW_COUNT],
          ['fake_metrics', String(dashboard.fake_metrics)],
          ['Data source', dashboard.data_source],
        ])}
        {renderMetadataCard('Runtime safety posture', 'Frontend mirrors the backend fail-closed safety boundary.', [
          ['Human review required', String(dashboard.human_review_required)],
          ['Provider sync', String(health.provider_integration_enabled)],
          ['External DB sync', String(health.external_database_sync_enabled)],
          ['Official verification', String(health.official_verification_enabled)],
          ['Hidden score', String(health.hidden_score_present)],
        ])}
      </div>

      <ResearchScienceRegistryPanel
        title="Route navigation"
        description="First runtime focuses on list, dashboard, audit, bridge, and limitations views. Optional detail routes remain deferred."
        items={RESEARCH_SCIENCE_NAV_ITEMS}
        emptyMessage="No routes defined."
        testId="research-science-route-navigation"
        renderItem={(item: typeof RESEARCH_SCIENCE_NAV_ITEMS[number]) => (
          <Link key={item.href} href={item.href} className="rounded-lg border p-4 hover:bg-muted/40">
            <h3 className="font-medium">{item.title}</h3>
            <p className="mt-1 text-sm text-muted-foreground">{item.href}</p>
          </Link>
        )}
      />

      <ResearchScienceLimitationsPanel limitations={[...limitations, ...RESEARCH_SCIENCE_LIMITATIONS, `Route expectation: ${matrix.route_count_expected}`]} />
    </div>
  );
}

export function ResearchScienceOverviewPage() {
  const health = useTrustedResearchScienceHealth();
  const dashboard = useTrustedResearchScienceDashboard();
  const matrix = useTrustedResearchScienceMatrixSummary();
  const limitations = useResearchScienceLimitations();

  if (health.isPending || dashboard.isPending || matrix.isPending || limitations.isPending) {
    return <LoadingState title="Loading Research / Science overview" />;
  }
  if (health.error) return PageError('Failed to load Research / Science health.', health.error);
  if (dashboard.error) return PageError('Failed to load Research / Science dashboard.', dashboard.error);
  if (matrix.error) return PageError('Failed to load Research / Science matrix summary.', matrix.error);
  if (limitations.error) return PageError('Failed to load Research / Science limitations.', limitations.error);
  if (!health.data || !dashboard.data || !matrix.data) {
    return <ErrorState message="Research / Science overview is unavailable." />;
  }

  return (
    <RequirePermission permission={RESEARCH_SCIENCE_PERMISSIONS.overviewRead}>
      <ResearchScienceShell
        title={RESEARCH_SCIENCE_PAGE_TITLES.overview}
        description="Controlled frontend runtime for research metadata, evidence, audit visibility, and read-only bridge summaries."
        currentPath={RESEARCH_SCIENCE_ROUTES.overview}
        boundaryPage="overview"
      >
        <OverviewContent health={health.data} dashboard={dashboard.data} matrix={matrix.data} limitations={limitations.data ?? []} />
      </ResearchScienceShell>
    </RequirePermission>
  );
}

export function ResearchScienceDashboardPage() {
  const health = useTrustedResearchScienceHealth();
  const dashboard = useTrustedResearchScienceDashboard();
  const matrix = useTrustedResearchScienceMatrixSummary();
  const limitations = useResearchScienceLimitations();

  if (health.isPending || dashboard.isPending || matrix.isPending || limitations.isPending) {
    return <LoadingState title="Loading Research / Science dashboard" />;
  }
  if (health.error || dashboard.error || matrix.error || limitations.error) {
    return PageError('Failed to load Research / Science dashboard.', health.error ?? dashboard.error ?? matrix.error ?? limitations.error);
  }
  if (!health.data || !dashboard.data || !matrix.data) {
    return <ErrorState message="Research / Science dashboard is unavailable." />;
  }

  const summaryCounts: Array<[string, number]> = [
    ['Projects', Object.values(dashboard.data.projects_summary).reduce((a, b) => a + b, 0)],
    ['Publications', Object.values(dashboard.data.publications_summary).reduce((a, b) => a + b, 0)],
    ['Grants', Object.values(dashboard.data.grants_summary).reduce((a, b) => a + b, 0)],
    ['Ethics', Object.values(dashboard.data.ethics_summary).reduce((a, b) => a + b, 0)],
  ];

  return (
    <RequirePermission permission={RESEARCH_SCIENCE_PERMISSIONS.dashboardRead}>
      <ResearchScienceShell
        title={RESEARCH_SCIENCE_PAGE_TITLES.dashboard}
        description="Summary visibility only. fake_metrics=false and metadata-derived counts are explicitly displayed."
        currentPath={RESEARCH_SCIENCE_ROUTES.dashboard}
        boundaryPage="dashboard"
      >
        <div className="space-y-6" data-testid="research-science-dashboard">
          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
            {summaryCounts.map(([label, value]) => (
              <ResearchScienceMetricCard key={label} label={label} value={value} helper="Metadata-derived summary" />
            ))}
          </div>
          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
            <ResearchScienceMetricCard label="Matrix commit" value={dashboard.data.master_matrix_commit} helper="Contract anchor" />
            <ResearchScienceMetricCard label="Planning rows" value={dashboard.data.master_matrix_rows} helper="Master matrix rows" />
            <ResearchScienceMetricCard label="fake_metrics" value={String(dashboard.data.fake_metrics)} helper={EXPECTED_DATA_SOURCE} />
            <ResearchScienceMetricCard label="Brain readiness signals" value={Object.keys(dashboard.data.brain_readiness_summary).length} helper="No hidden score" />
          </div>
          {renderMetadataCard('Backend baseline counts', 'Visible backend anchors preserved in the frontend runtime.', [
            ['Tables', RESEARCH_SCIENCE_TABLE_COUNT],
            ['Routes', RESEARCH_SCIENCE_BACKEND_ROUTE_COUNT],
            ['Permissions', RESEARCH_SCIENCE_BACKEND_PERMISSION_COUNT],
            ['Capability count', dashboard.data.capability_count],
          ])}
          {renderMetadataCard('Boundary summary', 'All safety booleans remain fail-closed.', [
            ['Human review required', String(dashboard.data.human_review_required)],
            ['Autonomous decision', String(dashboard.data.autonomous_decision)],
            ['Provider integration enabled', String(dashboard.data.provider_integration_enabled)],
            ['External database sync enabled', String(dashboard.data.external_database_sync_enabled)],
            ['Official verification enabled', String(dashboard.data.official_verification_enabled)],
            ['Hidden score present', String(dashboard.data.hidden_score_present)],
          ])}
          <ResearchScienceLimitationsPanel limitations={[...(limitations.data ?? []), ...RESEARCH_SCIENCE_DASHBOARD_SECTIONS.map((section) => `Dashboard section available: ${section}`)]} />
        </div>
      </ResearchScienceShell>
    </RequirePermission>
  );
}

export function ResearchProjectsPage() {
  const projects = useResearchProjects();
  if (projects.isPending) return <LoadingState title="Loading research projects" />;
  if (projects.error) return PageError('Failed to load research projects.', projects.error);
  return (
    <RequirePermission permission={RESEARCH_SCIENCE_PERMISSIONS.projectsRead}>
      <ResearchScienceShell title={RESEARCH_SCIENCE_PAGE_TITLES.projects} description="Project registry metadata only. No official external verification or provider execution is available." currentPath={RESEARCH_SCIENCE_ROUTES.projects} boundaryPage="projects">
        <ResearchScienceRegistryPanel
          title="Research project registry"
          description="Project status, department, program, and evidence readiness metadata."
          items={projects.data ?? []}
          emptyMessage="No research projects available."
          testId="research-projects-page"
          renderItem={(project: ResearchProject) => renderMetadataCard(project.title, 'Metadata registry', [
            ['Project ref', project.project_ref],
            ['Department ref', project.department_ref],
            ['Program ref', project.program_ref],
            ['Status', project.status],
          ])}
        />
      </ResearchScienceShell>
    </RequirePermission>
  );
}

export function StudentResearchWorkPage() {
  const items = useStudentResearchWorkItems();
  if (items.isPending) return <LoadingState title="Loading student research work" />;
  if (items.error) return PageError('Failed to load student research work.', items.error);
  return (
    <RequirePermission permission={RESEARCH_SCIENCE_PERMISSIONS.studentResearchRead}>
      <ResearchScienceShell title={RESEARCH_SCIENCE_PAGE_TITLES.studentResearch} description="Student research metadata only. No hidden student research score is computed or shown." currentPath={RESEARCH_SCIENCE_ROUTES.studentResearch} boundaryPage="studentResearch">
        <ResearchScienceRegistryPanel
          title="Student research work"
          description="Topics, supervision references, and milestone context in metadata form only."
          items={items.data ?? []}
          emptyMessage="No student research work available."
          testId="student-research-page"
          renderItem={(item: StudentResearchWork) => renderMetadataCard(item.topic_title, 'Student research metadata', [
            ['Student ref', item.student_ref],
            ['Faculty ref', item.faculty_ref],
            ['Project ref', item.project_ref],
            ['Publication ref', item.publication_ref],
          ])}
        />
      </ResearchScienceShell>
    </RequirePermission>
  );
}

export function ScientificSupervisionPage() {
  const items = useScientificSupervisionItems();
  if (items.isPending) return <LoadingState title="Loading scientific supervision" />;
  if (items.error) return PageError('Failed to load scientific supervision.', items.error);
  return (
    <RequirePermission permission={RESEARCH_SCIENCE_PERMISSIONS.supervisionRead}>
      <ResearchScienceShell title={RESEARCH_SCIENCE_PAGE_TITLES.supervision} description="Scientific supervision metadata with human review framing and no autonomous evaluation." currentPath={RESEARCH_SCIENCE_ROUTES.supervision} boundaryPage="supervision">
        <ResearchScienceRegistryPanel
          title="Scientific supervision"
          description="Supervision references, milestones, and review status in metadata-only form."
          items={items.data ?? []}
          emptyMessage="No supervision records available."
          testId="scientific-supervision-page"
          renderItem={(item: ScientificSupervision) => renderMetadataCard(item.supervision_ref, 'Supervision metadata', [
            ['Student ref', item.student_ref],
            ['Faculty ref', item.faculty_ref],
            ['Project ref', item.project_ref],
            ['Status', item.status],
          ])}
        />
      </ResearchScienceShell>
    </RequirePermission>
  );
}

export function PublicationRegistryPage() {
  const items = usePublicationMetadataItems();
  if (items.isPending) return <LoadingState title="Loading publication metadata" />;
  if (items.error) return PageError('Failed to load publication metadata.', items.error);
  return (
    <RequirePermission permission={RESEARCH_SCIENCE_PERMISSIONS.publicationsRead}>
      <ResearchScienceShell title={RESEARCH_SCIENCE_PAGE_TITLES.publications} description="Publication metadata only. No citation score, official verification, or fake publication workflow exists." currentPath={RESEARCH_SCIENCE_ROUTES.publications} boundaryPage="publications">
        <ResearchScienceRegistryPanel
          title="Publication registry"
          description="Author, project, and indexing references only. Official publication verification is disabled."
          items={items.data ?? []}
          emptyMessage="No publication metadata available."
          testId="publication-registry-page"
          renderItem={(item: PublicationMetadata) => renderMetadataCard(item.title, 'Publication metadata only', [
            ['Publication ref', item.publication_ref],
            ['Faculty ref', item.faculty_ref],
            ['Student ref', item.student_ref],
            ['fake_publication', String(item.fake_publication)],
          ])}
        />
      </ResearchScienceShell>
    </RequirePermission>
  );
}

export function ConferenceParticipationPage() {
  const items = useConferenceParticipationItems();
  if (items.isPending) return <LoadingState title="Loading conference participation" />;
  if (items.error) return PageError('Failed to load conference participation.', items.error);
  return (
    <RequirePermission permission={RESEARCH_SCIENCE_PERMISSIONS.conferencesRead}>
      <ResearchScienceShell title={RESEARCH_SCIENCE_PAGE_TITLES.conferences} description="Conference participation metadata only. No official certificate validation or fake certificate flow is present." currentPath={RESEARCH_SCIENCE_ROUTES.conferences} boundaryPage="conferences">
        <ResearchScienceRegistryPanel
          title="Conference participation"
          description="Submission, presentation, and certificate metadata without certificate issuance workflows."
          items={items.data ?? []}
          emptyMessage="No conference participation metadata available."
          testId="conference-participation-page"
          renderItem={(item: ConferenceParticipation) => renderMetadataCard(item.title, 'Conference participation metadata', [
            ['Conference ref', item.conference_ref],
            ['Project ref', item.project_ref],
            ['External ref', item.external_ref],
            ['fake_certificate', String(item.fake_certificate)],
          ])}
        />
      </ResearchScienceShell>
    </RequirePermission>
  );
}

export function GrantApplicationPage() {
  const grants = useGrantApplicationItems();
  const deliverables = useGrantDeliverableItems();
  if (grants.isPending || deliverables.isPending) return <LoadingState title="Loading grant metadata" />;
  if (grants.error || deliverables.error) return PageError('Failed to load grant metadata.', grants.error ?? deliverables.error);
  return (
    <RequirePermission permission={RESEARCH_SCIENCE_PERMISSIONS.grantsRead}>
      <ResearchScienceShell title={RESEARCH_SCIENCE_PAGE_TITLES.grants} description="Grant application and deliverable metadata only. No autonomous submission, financial approval, or official award confirmation UI exists." currentPath={RESEARCH_SCIENCE_ROUTES.grants} boundaryPage="grants">
        <div className="space-y-6">
          <ResearchScienceRegistryPanel
            title="Grant applications"
            description="Grant proposal metadata with fail-closed safety flags."
            items={grants.data ?? []}
            emptyMessage="No grant applications available."
            testId="grant-application-page"
            renderItem={(item: GrantApplication) => renderMetadataCard(item.title, 'Grant application metadata', [
              ['Grant ref', item.grant_ref],
              ['Project ref', item.project_ref],
              ['Faculty ref', item.faculty_ref],
              ['autonomous_grant_submission_enabled', String(item.autonomous_grant_submission_enabled)],
            ])}
          />
          <ResearchScienceRegistryPanel
            title="Grant deliverables"
            description="Deliverable tracking metadata without external submission or fake grant evidence."
            items={deliverables.data ?? []}
            emptyMessage="No grant deliverables available."
            testId="grant-deliverables-page"
            renderItem={(item: GrantDeliverable) => renderMetadataCard(item.title, 'Grant deliverable metadata', [
              ['Deliverable ref', item.deliverable_ref],
              ['Grant ref', item.grant_ref],
              ['Project ref', item.project_ref],
              ['fake_grant_evidence', String(item.fake_grant_evidence)],
            ])}
          />
        </div>
      </ResearchScienceShell>
    </RequirePermission>
  );
}

export function ResearchEthicsPage() {
  const ethics = useResearchEthicsRequests();
  const amendments = useResearchEthicsAmendments();
  if (ethics.isPending || amendments.isPending) return <LoadingState title="Loading research ethics metadata" />;
  if (ethics.error || amendments.error) return PageError('Failed to load research ethics metadata.', ethics.error ?? amendments.error);
  return (
    <RequirePermission permission={RESEARCH_SCIENCE_PERMISSIONS.ethicsRead}>
      <ResearchScienceShell title={RESEARCH_SCIENCE_PAGE_TITLES.ethics} description="Research ethics metadata only. Human committee review remains mandatory, with no autonomous approval flow." currentPath={RESEARCH_SCIENCE_ROUTES.ethics} boundaryPage="ethics">
        <div className="space-y-6">
          <ResearchScienceRegistryPanel
            title="Ethics requests"
            description="Human-review-gated ethics request metadata."
            items={ethics.data ?? []}
            emptyMessage="No ethics requests available."
            testId="research-ethics-page"
            renderItem={(item: ResearchEthicsRequest) => renderMetadataCard(item.title, 'Ethics request metadata', [
              ['Ethics ref', item.ethics_ref],
              ['Project ref', item.project_ref],
              ['Faculty ref', item.faculty_ref],
              ['autonomous_ethics_approval_enabled', String(item.autonomous_ethics_approval_enabled)],
            ])}
          />
          <ResearchScienceRegistryPanel
            title="Ethics amendments"
            description="Amendment metadata only."
            items={amendments.data ?? []}
            emptyMessage="No ethics amendments available."
            testId="research-ethics-amendments-page"
            renderItem={(item: ResearchEthicsAmendment) => renderMetadataCard(item.title, 'Amendment metadata', [
              ['Amendment ref', item.amendment_ref],
              ['Ethics ref', item.ethics_ref],
              ['Project ref', item.project_ref],
              ['External ref', item.external_ref],
            ])}
          />
        </div>
      </ResearchScienceShell>
    </RequirePermission>
  );
}

export function ResearchEvidencePage() {
  const evidence = useResearchEvidenceItems();
  if (evidence.isPending) return <LoadingState title="Loading research evidence" />;
  if (evidence.error) return PageError('Failed to load research evidence.', evidence.error);
  return (
    <RequirePermission permission={RESEARCH_SCIENCE_PERMISSIONS.evidenceRead}>
      <ResearchScienceShell title={RESEARCH_SCIENCE_PAGE_TITLES.evidence} description="Evidence metadata only. No provider verification or official external verification is claimed." currentPath={RESEARCH_SCIENCE_ROUTES.evidence} boundaryPage="evidence">
        <ResearchScienceRegistryPanel
          title="Evidence metadata"
          description="Submitted evidence remains metadata-only until reviewed by humans."
          items={evidence.data ?? []}
          emptyMessage="No evidence metadata available."
          testId="research-evidence-page"
          renderItem={(item: ResearchEvidence) => renderMetadataCard(item.title, 'Evidence metadata only', [
            ['Evidence type', item.evidence_type],
            ['Verification status', item.verification_status],
            ['Provider verified', String(item.provider_verified)],
            ['Official external verification', String(item.official_external_verification)],
          ])}
        />
      </ResearchScienceShell>
    </RequirePermission>
  );
}

export function ResearchAuditPage() {
  const audit = useResearchAuditItems();
  if (audit.isPending) return <LoadingState title="Loading research audit events" />;
  if (audit.error) return PageError('Failed to load research audit events.', audit.error);
  return (
    <RequirePermission permission={RESEARCH_SCIENCE_PERMISSIONS.auditRead}>
      <ResearchScienceShell title={RESEARCH_SCIENCE_PAGE_TITLES.audit} description="Append-only audit events with human-review flags and autonomous_decision=false preserved." currentPath={RESEARCH_SCIENCE_ROUTES.audit} boundaryPage="audit">
        <ResearchScienceRegistryPanel
          title="Audit events"
          description="Audit trail metadata only. Status changes remain append-only support artifacts."
          items={audit.data ?? []}
          emptyMessage="No audit events available."
          testId="research-audit-page"
          renderItem={(item: ResearchAuditEvent) => renderMetadataCard(item.event_type, 'Audit event metadata', [
            ['Source entity type', item.source_entity_type],
            ['Previous status', item.previous_status],
            ['New status', item.new_status],
            ['autonomous_decision', String(item.autonomous_decision)],
          ])}
        />
      </ResearchScienceShell>
    </RequirePermission>
  );
}

export function ResearchBridgePage() {
  const bridges = useResearchBridgeItems();
  const summary = useResearchBridgeSummary();
  if (bridges.isPending || summary.isPending) return <LoadingState title="Loading research bridges" />;
  if (bridges.error || summary.error) return PageError('Failed to load research bridges.', bridges.error ?? summary.error);
  const summaryData = summary.data as ResearchBridgeSummary | undefined;
  return (
    <RequirePermission permission={RESEARCH_SCIENCE_PERMISSIONS.bridgesRead}>
      <ResearchScienceShell title={RESEARCH_SCIENCE_PAGE_TITLES.bridges} description="Read-only-first bridge cards only. No cross-suite mutation, provider sync, or external submission is enabled." currentPath={RESEARCH_SCIENCE_ROUTES.bridges} boundaryPage="bridges">
        <div className="space-y-6" data-testid="research-bridges-page">
          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
            <ResearchScienceMetricCard label="Tracked bridges" value={(bridges.data ?? []).length} helper="Metadata registry only" />
            <ResearchScienceMetricCard label="Read-only-first" value={String(summaryData?.read_only_first ?? true)} helper="Mutation disabled" />
            <ResearchScienceMetricCard label="Provider sync enabled" value={String(summaryData?.provider_sync_enabled ?? false)} helper="Must remain false" />
            <ResearchScienceMetricCard label="External submission enabled" value={String(summaryData?.external_submission_enabled ?? false)} helper="Must remain false" />
          </div>
          <div className="grid gap-4 lg:grid-cols-2">
            {RESEARCH_SCIENCE_BRIDGE_TARGETS.map((target) => (
              <ResearchScienceBridgeCard
                key={target.key}
                title={target.title}
                description={target.description}
                count={summaryData?.bridge_counts?.[target.key]}
              />
            ))}
          </div>
          <ResearchScienceRegistryPanel
            title="Bridge registry"
            description="Existing bridge metadata captured from the backend contract."
            items={bridges.data ?? []}
            emptyMessage="No bridge metadata available."
            testId="research-bridge-registry"
            renderItem={(item: ResearchBridge) => renderMetadataCard(item.bridge_target, 'Bridge metadata', [
              ['Source entity type', item.source_entity_type],
              ['Target reference', item.target_reference],
              ['Read-only-first', String(item.read_only_first)],
              ['Provider sync enabled', String(item.provider_sync_enabled)],
            ])}
          />
        </div>
      </ResearchScienceShell>
    </RequirePermission>
  );
}

export function ResearchLimitationsPage() {
  const limitations = useResearchScienceLimitations();
  if (limitations.isPending) return <LoadingState title="Loading Research / Science limitations" />;
  if (limitations.error) return PageError('Failed to load Research / Science limitations.', limitations.error);
  return (
    <RequirePermission permission={RESEARCH_SCIENCE_PERMISSIONS.limitationsRead}>
      <ResearchScienceShell title={RESEARCH_SCIENCE_PAGE_TITLES.limitations} description="Explicit runtime boundaries, limitations, and no-overclaim posture for the first frontend slice." currentPath={RESEARCH_SCIENCE_ROUTES.limitations} boundaryPage="limitations">
        <ResearchScienceLimitationsPanel limitations={[...(limitations.data ?? []), ...RESEARCH_SCIENCE_LIMITATIONS, RESEARCH_SCIENCE_BOUNDARY_LABELS.limitationsPage]} />
      </ResearchScienceShell>
    </RequirePermission>
  );
}