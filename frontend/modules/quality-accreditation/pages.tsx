'use client';

import { Children, type ReactNode } from 'react';
import Link from 'next/link';
import { useQuery } from '@tanstack/react-query';
import type { Permission } from '@/shared/config/permissions';
import { RequirePermission } from '@/shared/ui/permission-gate';
import { ErrorState, LoadingState } from '@/shared/ui/page-states';
import { qualityAccreditationApi } from './api';
import {
  API_PREFIX,
  DATA_SOURCE,
  FAKE_EVIDENCE,
  FAKE_METRICS,
  HUMAN_REVIEW_REQUIRED,
  QUALITY_ACCREDITATION_BACKEND_PERMISSION_COUNT,
  QUALITY_ACCREDITATION_BACKEND_ROUTE_COUNT,
  QUALITY_ACCREDITATION_BACKEND_TABLE_COUNT,
  QUALITY_ACCREDITATION_BRIDGE_TARGETS,
  QUALITY_ACCREDITATION_DASHBOARD_SECTIONS,
  QUALITY_ACCREDITATION_FORBIDDEN_ACTIONS,
  QUALITY_ACCREDITATION_LIMITATIONS,
  QUALITY_ACCREDITATION_NAV_ITEMS,
  QUALITY_ACCREDITATION_PAGE_TITLES,
  QUALITY_ACCREDITATION_ROUTES,
  RUNTIME_MODE,
  SOURCE_BACKEND_B1_COMMIT,
} from './constants';
import {
  QUALITY_ACCREDITATION_BOUNDARY_COPY,
  type QualityAccreditationPageKey,
} from './boundaryLabels';
import {
  QUALITY_ACCREDITATION_PERMISSIONS,
  assertTrustedQualityAccreditationDashboard,
  assertTrustedQualityAccreditationHealth,
  assertTrustedQualityAccreditationMatrixSummary,
  assertTrustedQualityAccreditationOverview,
  getQualityAccreditationBoundaryLabels,
} from './guards';
import type {
  AccreditationCalendarItem,
  AccreditationCommitteeWorkflow,
  AccreditationStandard,
  ComplianceGapAnalysis,
  EvidenceLimitation,
  ExpertRecommendationResponsePlan,
  ExternalExpertReview,
  InstitutionalReadiness,
  InternalQualityAudit,
  LearningOutcomesAssessment,
  ProgramReadiness,
  ProgramReviewCycle,
  QualityAccreditationDashboardResponse,
  QualityAccreditationHealthResponse,
  QualityAccreditationLimitationsResponse,
  QualityAccreditationMatrixSummaryResponse,
  QualityAccreditationMetadataEntity,
  QualityAccreditationOverviewResponse,
  QualityAccreditationRuntimeShellResponse,
  QualityAuditEvent,
  QualityAuditFinding,
  QualityBrainSignal,
  QualityBridge,
  QualityEvidence,
  QualityFramework,
  QualityImprovementAction,
  QualityImprovementPlan,
  QualityRisk,
  QualityStatusHistory,
  SelfAssessmentReport,
  SelfAssessmentSection,
  StakeholderFeedbackMetadata,
  StandardCriterion,
  StandardsEvidenceRequirement,
  SurveyQualityMetadata,
} from './types';

const CACHE_KEYS = {
  health: ['quality-accreditation:health'] as const,
  overview: ['quality-accreditation:overview'] as const,
  dashboard: ['quality-accreditation:dashboard'] as const,
  matrixSummary: ['quality-accreditation:matrix-summary'] as const,
  limitations: ['quality-accreditation:limitations'] as const,
  frameworks: ['quality-accreditation:frameworks'] as const,
  standards: ['quality-accreditation:standards'] as const,
  criteria: ['quality-accreditation:criteria'] as const,
  standardsEvidenceRequirements: ['quality-accreditation:standards-evidence-requirements'] as const,
  evidence: ['quality-accreditation:evidence'] as const,
  evidenceLimitations: ['quality-accreditation:evidence-limitations'] as const,
  programReadiness: ['quality-accreditation:program-readiness'] as const,
  institutionalReadiness: ['quality-accreditation:institutional-readiness'] as const,
  selfAssessment: ['quality-accreditation:self-assessment'] as const,
  selfAssessmentSections: ['quality-accreditation:self-assessment-sections'] as const,
  improvementPlans: ['quality-accreditation:improvement-plans'] as const,
  improvementActions: ['quality-accreditation:improvement-actions'] as const,
  internalAudits: ['quality-accreditation:internal-audits'] as const,
  auditFindings: ['quality-accreditation:audit-findings'] as const,
  programReview: ['quality-accreditation:program-review'] as const,
  learningOutcomes: ['quality-accreditation:learning-outcomes'] as const,
  stakeholderFeedback: ['quality-accreditation:stakeholder-feedback'] as const,
  surveyQualityMetadata: ['quality-accreditation:survey-quality-metadata'] as const,
  committee: ['quality-accreditation:committee'] as const,
  externalReview: ['quality-accreditation:external-review'] as const,
  expertResponsePlans: ['quality-accreditation:expert-response-plans'] as const,
  gapAnalysis: ['quality-accreditation:gap-analysis'] as const,
  calendar: ['quality-accreditation:calendar'] as const,
  riskRegister: ['quality-accreditation:risk-register'] as const,
  bridges: ['quality-accreditation:bridges'] as const,
  brainSignals: ['quality-accreditation:brain-signals'] as const,
  audit: ['quality-accreditation:audit'] as const,
  statusHistory: ['quality-accreditation:status-history'] as const,
};

function slugify(value: string) {
  return value.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');
}

function formatKey(value: string) {
  return value.replace(/_/g, ' ').replace(/\b\w/g, (char) => char.toUpperCase());
}

function extractReference(item: Partial<QualityAccreditationMetadataEntity>) {
  return (
    item.framework_ref ??
    item.policy_ref ??
    item.standard_ref ??
    item.criterion_ref ??
    item.requirement_ref ??
    item.evidence_ref ??
    item.readiness_ref ??
    item.report_ref ??
    item.section_ref ??
    item.plan_ref ??
    item.action_ref ??
    item.audit_ref ??
    item.finding_ref ??
    item.cycle_ref ??
    item.assessment_ref ??
    item.feedback_ref ??
    item.survey_ref ??
    item.review_ref ??
    item.response_plan_ref ??
    item.workflow_ref ??
    item.gap_ref ??
    item.calendar_ref ??
    item.risk_ref ??
    item.bridge_ref ??
    item.signal_ref ??
    item.target_reference ??
    null
  );
}

function PageError(message: string, error: unknown) {
  return <ErrorState error={error} message={message} />;
}

function useTrustedQualityAccreditationHealth() {
  return useQuery({
    queryKey: CACHE_KEYS.health,
    queryFn: async () => {
      const payload = await qualityAccreditationApi.getQualityAccreditationHealth();
      assertTrustedQualityAccreditationHealth(payload);
      return payload;
    },
    staleTime: 60000,
  });
}

function useQualityAccreditationRuntimeShell() {
  return useQuery({
    queryKey: ['quality-accreditation:runtime-shell'],
    queryFn: qualityAccreditationApi.getQualityAccreditationRuntimeShell,
    staleTime: 30000,
  });
}

function useTrustedQualityAccreditationOverview() {
  return useQuery({
    queryKey: CACHE_KEYS.overview,
    queryFn: async () => {
      const payload = await qualityAccreditationApi.getQualityAccreditationOverview();
      assertTrustedQualityAccreditationOverview(payload);
      return payload;
    },
    staleTime: 60000,
  });
}

function useTrustedQualityAccreditationDashboard() {
  return useQuery({
    queryKey: CACHE_KEYS.dashboard,
    queryFn: async () => {
      const payload = await qualityAccreditationApi.getQualityAccreditationDashboard();
      assertTrustedQualityAccreditationDashboard(payload);
      return payload;
    },
    staleTime: 60000,
  });
}

function useTrustedQualityAccreditationMatrixSummary() {
  return useQuery({
    queryKey: CACHE_KEYS.matrixSummary,
    queryFn: async () => {
      const payload = await qualityAccreditationApi.getQualityAccreditationMatrixSummary();
      assertTrustedQualityAccreditationMatrixSummary(payload);
      return payload;
    },
    staleTime: 60000,
  });
}

function useQualityAccreditationLimitations() {
  return useQuery({
    queryKey: CACHE_KEYS.limitations,
    queryFn: async () => (await qualityAccreditationApi.getQualityAccreditationLimitations()).items,
    staleTime: 60000,
  });
}

function useItems<T>(queryKey: readonly string[], queryFn: () => Promise<{ items: T[] }>) {
  return useQuery({ queryKey, queryFn: async () => (await queryFn()).items, staleTime: 30000 });
}

function useQualityFrameworks() { return useItems(CACHE_KEYS.frameworks, qualityAccreditationApi.listQualityFrameworks); }
function useAccreditationStandards() { return useItems(CACHE_KEYS.standards, qualityAccreditationApi.listAccreditationStandards); }
function useStandardCriteria() { return useItems(CACHE_KEYS.criteria, qualityAccreditationApi.listStandardCriteria); }
function useStandardsEvidenceRequirements() { return useItems(CACHE_KEYS.standardsEvidenceRequirements, qualityAccreditationApi.listStandardsEvidenceRequirements); }
function useQualityEvidence() { return useItems(CACHE_KEYS.evidence, qualityAccreditationApi.listQualityEvidence); }
function useEvidenceLimitations() { return useItems(CACHE_KEYS.evidenceLimitations, qualityAccreditationApi.listEvidenceLimitations); }
function useProgramReadinessItems() { return useItems(CACHE_KEYS.programReadiness, qualityAccreditationApi.listProgramReadiness); }
function useInstitutionalReadinessItems() { return useItems(CACHE_KEYS.institutionalReadiness, qualityAccreditationApi.listInstitutionalReadiness); }
function useSelfAssessmentReports() { return useItems(CACHE_KEYS.selfAssessment, qualityAccreditationApi.listSelfAssessmentReports); }
function useSelfAssessmentSections() { return useItems(CACHE_KEYS.selfAssessmentSections, qualityAccreditationApi.listSelfAssessmentSections); }
function useImprovementPlans() { return useItems(CACHE_KEYS.improvementPlans, qualityAccreditationApi.listQualityImprovementPlans); }
function useImprovementActions() { return useItems(CACHE_KEYS.improvementActions, qualityAccreditationApi.listQualityImprovementActions); }
function useInternalAudits() { return useItems(CACHE_KEYS.internalAudits, qualityAccreditationApi.listInternalQualityAudits); }
function useAuditFindings() { return useItems(CACHE_KEYS.auditFindings, qualityAccreditationApi.listQualityAuditFindings); }
function useProgramReviewCycles() { return useItems(CACHE_KEYS.programReview, qualityAccreditationApi.listProgramReviewCycles); }
function useLearningOutcomesAssessments() { return useItems(CACHE_KEYS.learningOutcomes, qualityAccreditationApi.listLearningOutcomesAssessments); }
function useStakeholderFeedbackItems() { return useItems(CACHE_KEYS.stakeholderFeedback, qualityAccreditationApi.listStakeholderFeedback); }
function useSurveyQualityMetadataItems() { return useItems(CACHE_KEYS.surveyQualityMetadata, qualityAccreditationApi.listSurveyQualityMetadata); }
function useCommitteeWorkflows() { return useItems(CACHE_KEYS.committee, qualityAccreditationApi.listAccreditationCommitteeWorkflows); }
function useExternalExpertReviews() { return useItems(CACHE_KEYS.externalReview, qualityAccreditationApi.listExternalExpertReviews); }
function useExpertResponsePlans() { return useItems(CACHE_KEYS.expertResponsePlans, qualityAccreditationApi.listExpertResponsePlans); }
function useGapAnalysisItems() { return useItems(CACHE_KEYS.gapAnalysis, qualityAccreditationApi.listComplianceGapAnalysis); }
function useCalendarItems() { return useItems(CACHE_KEYS.calendar, qualityAccreditationApi.listAccreditationCalendar); }
function useRiskRegisterItems() { return useItems(CACHE_KEYS.riskRegister, qualityAccreditationApi.listQualityRisks); }
function useBridgeItems() { return useItems(CACHE_KEYS.bridges, qualityAccreditationApi.listQualityBridges); }
function useBrainSignals() { return useItems(CACHE_KEYS.brainSignals, qualityAccreditationApi.listQualityBrainSignals); }
function useAuditEvents() { return useItems(CACHE_KEYS.audit, qualityAccreditationApi.listQualityAuditEvents); }
function useStatusHistoryItems() { return useItems(CACHE_KEYS.statusHistory, qualityAccreditationApi.listQualityStatusHistory); }

export function QualityAccreditationPageHeader({ title, description }: { title: string; description: string }) {
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

export function QualityAccreditationBoundaryBanner({ labels }: { labels: string[] }) {
  return (
    <section className="rounded-lg border border-amber-200 bg-amber-50/60 p-4" data-testid="quality-accreditation-boundary-banner">
      <div className="space-y-1">
        <h2 className="text-sm font-semibold text-amber-950">Quality / Accreditation boundaries</h2>
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

export function QualityAccreditationMetricCard({ label, value, helper }: { label: string; value: string | number; helper?: string }) {
  return (
    <div className="rounded-lg border p-4">
      <p className="text-sm text-muted-foreground">{label}</p>
      <p className="mt-2 text-2xl font-semibold">{value}</p>
      {helper ? <p className="mt-1 text-xs text-muted-foreground">{helper}</p> : null}
    </div>
  );
}

function QualityAccreditationNavCard({ title, href }: { title: string; href: string }) {
  return (
    <Link href={href} className="rounded-lg border p-4 transition-colors hover:bg-muted/40">
      <p className="text-sm font-semibold">{title}</p>
      <p className="mt-1 text-xs text-muted-foreground">{href}</p>
    </Link>
  );
}

export function QualityAccreditationRegistryPanel({
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

export function QualityAccreditationLimitationsPanel({ limitations }: { limitations: string[] }) {
  return (
    <section className="rounded-lg border p-4" data-testid="quality-accreditation-limitations-panel">
      <h2 className="text-lg font-semibold">Limitations</h2>
      <ul className="mt-3 space-y-2 text-sm text-muted-foreground">
        {limitations.map((item, index) => (
          <li key={`${item}-${index}`}>- {item}</li>
        ))}
      </ul>
    </section>
  );
}

export function QualityAccreditationBridgeCard({ title, description }: { title: string; description: string }) {
  return (
    <div className="rounded-lg border p-4" data-testid={`bridge-${slugify(title)}`}>
      <h3 className="font-semibold">{title}</h3>
      <p className="mt-1 text-sm text-muted-foreground">{description}</p>
    </div>
  );
}

function SummaryPanel({ title, summary, testId }: { title: string; summary: Record<string, number>; testId: string }) {
  return (
    <section className="rounded-lg border p-4" data-testid={testId}>
      <h2 className="text-lg font-semibold">{title}</h2>
      <div className="mt-3 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {Object.entries(summary).length === 0 ? (
          <p className="text-sm text-muted-foreground">No summary rows available.</p>
        ) : (
          Object.entries(summary).map(([key, value]) => (
            <QualityAccreditationMetricCard key={key} label={formatKey(key)} value={value} />
          ))
        )}
      </div>
    </section>
  );
}

function recordCard(item: QualityAccreditationMetadataEntity) {
  const ref = extractReference(item);
  return (
    <div className="rounded-lg border p-4">
      <p className="text-sm font-semibold">{item.title ?? ref ?? `Record ${item.id}`}</p>
      <p className="mt-1 text-xs text-muted-foreground">Status: {item.status}</p>
      {ref ? <p className="mt-1 text-xs text-muted-foreground">Reference: {ref}</p> : null}
      {item.risk_band ? <p className="mt-1 text-xs text-muted-foreground">Risk band: {item.risk_band}</p> : null}
      {item.owner_ref ? <p className="mt-1 text-xs text-muted-foreground">Owner: {item.owner_ref}</p> : null}
      {item.notes ? <p className="mt-2 text-sm text-muted-foreground">{item.notes}</p> : null}
    </div>
  );
}

function auditEventCard(item: QualityAuditEvent) {
  return (
    <div className="rounded-lg border p-4">
      <p className="text-sm font-semibold">{item.event_type}</p>
      <p className="mt-1 text-xs text-muted-foreground">Source: {item.source_entity_type}</p>
      <p className="mt-1 text-xs text-muted-foreground">Human review required: {String(item.human_review_required)}</p>
    </div>
  );
}

function statusHistoryCard(item: QualityStatusHistory) {
  return (
    <div className="rounded-lg border p-4">
      <p className="text-sm font-semibold">{item.new_status}</p>
      <p className="mt-1 text-xs text-muted-foreground">Entity: {item.source_entity_type}</p>
      {item.previous_status ? <p className="mt-1 text-xs text-muted-foreground">Previous: {item.previous_status}</p> : null}
    </div>
  );
}

export function QualityAccreditationShell({
  title,
  description,
  currentPath,
  boundaryPage,
  children,
}: {
  title: string;
  description: string;
  currentPath: string;
  boundaryPage: QualityAccreditationPageKey;
  children: ReactNode;
}) {
  return (
    <div className="space-y-6" data-testid="quality-accreditation-shell">
      <QualityAccreditationPageHeader title={title} description={description} />
      <QualityAccreditationBoundaryBanner labels={getQualityAccreditationBoundaryLabels(boundaryPage)} />
      <section className="rounded-lg border p-4">
        <h2 className="text-sm font-semibold">Navigation</h2>
        <div className="mt-3 grid gap-3 md:grid-cols-2 xl:grid-cols-3">
          {QUALITY_ACCREDITATION_NAV_ITEMS.map((item) => (
            <QualityAccreditationNavCard key={item.href} title={item.title} href={item.href} />
          ))}
        </div>
        <p className="mt-3 text-xs text-muted-foreground">Current path: {currentPath}</p>
      </section>
      {children}
    </div>
  );
}

function ModuleShell({
  title,
  description,
  currentPath,
  boundaryPage,
  children,
}: {
  title: string;
  description: string;
  currentPath: string;
  boundaryPage: QualityAccreditationPageKey;
  children: ReactNode;
}) {
  return (
    <QualityAccreditationShell title={title} description={description} currentPath={currentPath} boundaryPage={boundaryPage}>
      {children}
    </QualityAccreditationShell>
  );
}

function usePageLoaders(...states: Array<{ isPending: boolean; error: unknown; data: unknown }>) {
  if (states.some((state) => state.isPending)) {
    return { loading: true, error: null };
  }
  const errored = states.find((state) => state.error);
  if (errored) {
    return { loading: false, error: errored.error };
  }
  return { loading: false, error: null };
}

function BaselineCards({ overview, health }: { overview: QualityAccreditationOverviewResponse; health: QualityAccreditationHealthResponse }) {
  return (
    <section className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
      <QualityAccreditationMetricCard label="Backend tables" value={overview.table_count} helper="Confirmed backend baseline." />
      <QualityAccreditationMetricCard label="Backend routes" value={overview.route_count} helper="Confirmed broad API pass." />
      <QualityAccreditationMetricCard label="Backend permissions" value={QUALITY_ACCREDITATION_BACKEND_PERMISSION_COUNT} helper="Aligned to shared permission registry." />
      <QualityAccreditationMetricCard label="Runtime mode" value={health.runtime_mode} helper={`Backend B1 commit ${SOURCE_BACKEND_B1_COMMIT}`} />
    </section>
  );
}

function RuntimeShellCard({
  title,
  section,
  testId,
}: {
  title: string;
  section: QualityAccreditationRuntimeShellResponse['overview'];
  testId: string;
}) {
  return (
    <section className="rounded-lg border p-4" data-testid={testId}>
      <h2 className="text-lg font-semibold">{title}</h2>
      <div className="mt-3 grid gap-3 md:grid-cols-2 xl:grid-cols-4">
        <QualityAccreditationMetricCard label="Owner" value={section.owner_module} />
        <QualityAccreditationMetricCard label="Records" value={section.records} />
        <QualityAccreditationMetricCard label="Read-only" value={String(section.read_only)} />
        <QualityAccreditationMetricCard label="Aggregator-only" value={String(section.aggregator_only)} />
      </div>
      <p className="mt-3 text-xs text-muted-foreground">Sources: {section.source_modules.join(', ') || 'none'}</p>
    </section>
  );
}

export function QualityAccreditationRuntimeShellPage() {
  const runtimeShell = useQualityAccreditationRuntimeShell();

  if (runtimeShell.isPending) return <LoadingState title="Loading Quality / Accreditation runtime shell" />;
  if (runtimeShell.error) return PageError('Failed to load Quality / Accreditation runtime shell.', runtimeShell.error);
  if (!runtimeShell.data) return <ErrorState message="Quality / Accreditation runtime shell is unavailable." />;

  return (
    <RequirePermission permission={QUALITY_ACCREDITATION_PERMISSIONS.overviewRead}>
      <ModuleShell
        title={QUALITY_ACCREDITATION_PAGE_TITLES.runtimeShell}
        description="Unified read-only runtime shell that aggregates quality accreditation overview, readiness, evidence, risk, and dashboard surfaces."
        currentPath={QUALITY_ACCREDITATION_ROUTES.runtimeShell}
        boundaryPage="runtimeShell"
      >
        <section className="grid gap-6" data-testid="quality-accreditation-runtime-shell">
          <RuntimeShellCard title="Overview" section={runtimeShell.data.overview} testId="quality-accreditation-overview" />
          <RuntimeShellCard title="Readiness" section={runtimeShell.data.readiness} testId="quality-accreditation-readiness" />
          <RuntimeShellCard title="Evidence" section={runtimeShell.data.evidence} testId="quality-accreditation-evidence" />
          <RuntimeShellCard title="Risk" section={runtimeShell.data.risk} testId="quality-accreditation-risk" />
          <RuntimeShellCard title="Dashboard" section={runtimeShell.data.dashboard} testId="quality-accreditation-dashboard" />
          <section className="rounded-lg border p-4" data-testid="quality-accreditation-runtime-safety">
            <h2 className="text-lg font-semibold">Runtime safety</h2>
            <div className="mt-3 grid gap-3 md:grid-cols-2 xl:grid-cols-4">
              <QualityAccreditationMetricCard label="Human review required" value={String(runtimeShell.data.safety.human_review_required)} />
              <QualityAccreditationMetricCard label="Provider integration" value={String(runtimeShell.data.safety.provider_integration_enabled)} />
              <QualityAccreditationMetricCard label="Official approval" value={String(runtimeShell.data.safety.official_accreditation_approval_enabled)} />
              <QualityAccreditationMetricCard label="Official ministry submission" value={String(runtimeShell.data.safety.official_ministry_submission_enabled)} />
            </div>
            <QualityAccreditationLimitationsPanel limitations={runtimeShell.data.safety.limitations} />
          </section>
        </section>
      </ModuleShell>
    </RequirePermission>
  );
}

export function QualityAccreditationOverviewPage() {
  const overview = useTrustedQualityAccreditationOverview();
  const health = useTrustedQualityAccreditationHealth();
  const dashboard = useTrustedQualityAccreditationDashboard();
  const matrixSummary = useTrustedQualityAccreditationMatrixSummary();
  const limitations = useQualityAccreditationLimitations();
  const state = usePageLoaders(overview, health, dashboard, matrixSummary, limitations as any);

  if (state.loading) return <LoadingState title="Loading Quality / Accreditation overview" />;
  if (state.error) return PageError('Failed to load Quality / Accreditation overview.', state.error);
  if (!overview.data || !health.data || !dashboard.data || !matrixSummary.data || !limitations.data) {
    return <ErrorState message="Quality / Accreditation overview is unavailable." />;
  }

  return (
    <RequirePermission permission={QUALITY_ACCREDITATION_PERMISSIONS.overviewRead}>
      <ModuleShell
        title={QUALITY_ACCREDITATION_PAGE_TITLES.overview}
        description="Safe metadata and evidence-only frontend runtime for accreditation readiness, gap visibility, internal reviews, and read-only bridges."
        currentPath={QUALITY_ACCREDITATION_ROUTES.overview}
        boundaryPage="overview"
      >
        <section className="grid gap-6" data-testid="quality-accreditation-overview">
          <BaselineCards overview={overview.data} health={health.data} />
          <section className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
            <QualityAccreditationMetricCard label="Backend B1 commit" value={SOURCE_BACKEND_B1_COMMIT} helper="Quality baseline anchor" />
            <QualityAccreditationMetricCard label="Data source" value={DATA_SOURCE} helper="Computed metadata only" />
            <QualityAccreditationMetricCard label="fake_metrics" value={String(FAKE_METRICS)} helper="Must remain false" />
            <QualityAccreditationMetricCard label="fake_evidence" value={String(FAKE_EVIDENCE)} helper="Must remain false" />
          </section>
          <SummaryPanel title="Boundary summary" summary={Object.fromEntries(Object.entries(dashboard.data.boundary_summary).map(([key, value]) => [key, value ? 1 : 0]))} testId="quality-accreditation-boundary-summary" />
          <QualityAccreditationLimitationsPanel limitations={[...limitations.data, ...QUALITY_ACCREDITATION_LIMITATIONS]} />
        </section>
      </ModuleShell>
    </RequirePermission>
  );
}

export function QualityAccreditationDashboardPage() {
  const health = useTrustedQualityAccreditationHealth();
  const dashboard = useTrustedQualityAccreditationDashboard();
  const matrixSummary = useTrustedQualityAccreditationMatrixSummary();
  const limitations = useQualityAccreditationLimitations();
  const state = usePageLoaders(health, dashboard, matrixSummary, limitations as any);

  if (state.loading) return <LoadingState title="Loading Quality / Accreditation dashboard" />;
  if (state.error) return PageError('Failed to load Quality / Accreditation dashboard.', state.error);
  if (!health.data || !dashboard.data || !matrixSummary.data || !limitations.data) {
    return <ErrorState message="Quality / Accreditation dashboard is unavailable." />;
  }

  return (
    <RequirePermission permission={QUALITY_ACCREDITATION_PERMISSIONS.dashboardRead}>
      <ModuleShell
        title={QUALITY_ACCREDITATION_PAGE_TITLES.dashboard}
        description="Readiness, evidence, gap, audit, and bridge visibility with explicit no-overclaim boundaries."
        currentPath={QUALITY_ACCREDITATION_ROUTES.dashboard}
        boundaryPage="dashboard"
      >
        <section className="grid gap-6" data-testid="quality-accreditation-dashboard">
          <section className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
            <QualityAccreditationMetricCard label="Backend baseline counts" value={`${QUALITY_ACCREDITATION_BACKEND_TABLE_COUNT}/${QUALITY_ACCREDITATION_BACKEND_ROUTE_COUNT}/${QUALITY_ACCREDITATION_BACKEND_PERMISSION_COUNT}`} helper="tables / routes / permissions" />
            <QualityAccreditationMetricCard label="fake_metrics" value={String(dashboard.data.fake_metrics)} helper="Must remain false" />
            <QualityAccreditationMetricCard label="Data source" value={dashboard.data.data_source} helper={`API prefix ${API_PREFIX}`} />
            <QualityAccreditationMetricCard label="Human review required" value={String(HUMAN_REVIEW_REQUIRED)} helper={`Runtime mode ${RUNTIME_MODE}`} />
          </section>
          <section className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
            <QualityAccreditationMetricCard label="Backend tables" value={health.data.table_count} />
            <QualityAccreditationMetricCard label="Backend routes" value={health.data.route_count} />
            <QualityAccreditationMetricCard label="Product map commit" value={dashboard.data.source_product_map_commit} />
            <QualityAccreditationMetricCard label="Vertical selection commit" value={dashboard.data.source_vertical_selection_commit} />
          </section>
          <SummaryPanel title="Framework summary" summary={dashboard.data.frameworks_summary} testId="quality-accreditation-frameworks-summary" />
          <SummaryPanel title="Standards gap summary" summary={dashboard.data.standards_summary} testId="quality-accreditation-standards-summary" />
          <SummaryPanel title="Evidence completeness summary" summary={dashboard.data.evidence_summary} testId="quality-accreditation-evidence-summary" />
          <SummaryPanel title="Readiness summary" summary={dashboard.data.readiness_summary} testId="quality-accreditation-readiness-summary" />
          <SummaryPanel title="Self-assessment summary" summary={dashboard.data.self_assessment_summary} testId="quality-accreditation-self-assessment-summary" />
          <SummaryPanel title="Improvement plan summary" summary={dashboard.data.improvement_summary} testId="quality-accreditation-improvement-summary" />
          <SummaryPanel title="Audit findings summary" summary={dashboard.data.audit_summary} testId="quality-accreditation-audit-summary" />
          <SummaryPanel title="Program review summary" summary={dashboard.data.program_review_summary} testId="quality-accreditation-program-review-summary" />
          <SummaryPanel title="Bridge coverage summary" summary={dashboard.data.bridge_summary} testId="quality-accreditation-bridge-summary" />
          <SummaryPanel title="Brain readiness signals" summary={dashboard.data.brain_signal_summary} testId="quality-accreditation-brain-summary" />
          <QualityAccreditationLimitationsPanel limitations={[...limitations.data, ...QUALITY_ACCREDITATION_LIMITATIONS]} />
        </section>
      </ModuleShell>
    </RequirePermission>
  );
}

function renderRegistryPage<T extends QualityAccreditationMetadataEntity>(params: {
  permission: Permission;
  title: string;
  description: string;
  route: string;
  boundaryPage: QualityAccreditationPageKey;
  sections: Array<{ title: string; description: string; items: T[]; emptyMessage: string; testId: string }>;
  extra?: ReactNode;
}) {
  return (
    <RequirePermission permission={params.permission}>
      <ModuleShell title={params.title} description={params.description} currentPath={params.route} boundaryPage={params.boundaryPage}>
        <section className="grid gap-6">
          {params.sections.map((section) => (
            <QualityAccreditationRegistryPanel
              key={section.testId}
              title={section.title}
              description={section.description}
              items={section.items}
              emptyMessage={section.emptyMessage}
              testId={section.testId}
              renderItem={(item: T) => recordCard(item)}
            />
          ))}
          {params.extra}
        </section>
      </ModuleShell>
    </RequirePermission>
  );
}

export function QualityAccreditationStandardsPage() {
  const frameworks = useQualityFrameworks();
  const standards = useAccreditationStandards();
  const criteria = useStandardCriteria();
  const requirements = useStandardsEvidenceRequirements();
  const state = usePageLoaders(frameworks, standards, criteria, requirements);
  if (state.loading) return <LoadingState title="Loading standards" />;
  if (state.error) return PageError('Failed to load standards.', state.error);
  return renderRegistryPage<QualityFramework | AccreditationStandard | StandardCriterion | StandardsEvidenceRequirement>({
    permission: QUALITY_ACCREDITATION_PERMISSIONS.standardsRead,
    title: QUALITY_ACCREDITATION_PAGE_TITLES.standards,
    description: 'Quality frameworks, accreditation standards, criteria, and evidence requirements for internal readiness only.',
    route: QUALITY_ACCREDITATION_ROUTES.standards,
    boundaryPage: 'standards',
    sections: [
      { title: 'Quality framework metadata', description: 'Internal framework registry only.', items: frameworks.data ?? [], emptyMessage: 'No frameworks recorded.', testId: 'quality-frameworks-panel' },
      { title: 'Accreditation standards', description: 'Standards metadata for readiness mapping only.', items: standards.data ?? [], emptyMessage: 'No standards recorded.', testId: 'accreditation-standards-panel' },
      { title: 'Standard criteria', description: 'Criteria used for internal readiness gap visibility.', items: criteria.data ?? [], emptyMessage: 'No criteria recorded.', testId: 'standard-criteria-panel' },
      { title: 'Evidence requirements', description: 'Required evidence metadata. No official compliance approval claim.', items: requirements.data ?? [], emptyMessage: 'No evidence requirements recorded.', testId: 'standards-evidence-requirements-panel' },
    ],
  });
}

export function QualityAccreditationEvidencePage() {
  const evidence = useQualityEvidence();
  const evidenceLimitations = useEvidenceLimitations();
  const state = usePageLoaders(evidence, evidenceLimitations);
  if (state.loading) return <LoadingState title="Loading evidence" />;
  if (state.error) return PageError('Failed to load evidence.', state.error);
  return renderRegistryPage<QualityEvidence | EvidenceLimitation>({
    permission: QUALITY_ACCREDITATION_PERMISSIONS.evidenceRead,
    title: QUALITY_ACCREDITATION_PAGE_TITLES.evidence,
    description: 'Evidence metadata, review notes, and limitations only. No external verification or official submission claim.',
    route: QUALITY_ACCREDITATION_ROUTES.evidence,
    boundaryPage: 'evidence',
    sections: [
      { title: 'Quality evidence registry', description: 'Evidence records remain metadata-only unless reviewed by humans.', items: evidence.data ?? [], emptyMessage: 'No evidence recorded.', testId: 'quality-evidence-registry-panel' },
      { title: 'Evidence limitations', description: 'Tracks incomplete or deferred evidence safely.', items: evidenceLimitations.data ?? [], emptyMessage: 'No evidence limitations recorded.', testId: 'evidence-limitations-panel' },
    ],
  });
}

export function QualityAccreditationProgramReadinessPage() {
  const programReadiness = useProgramReadinessItems();
  if (programReadiness.isPending) return <LoadingState title="Loading program readiness" />;
  if (programReadiness.error) return PageError('Failed to load program readiness.', programReadiness.error);
  return renderRegistryPage<ProgramReadiness>({
    permission: QUALITY_ACCREDITATION_PERMISSIONS.programReadinessRead,
    title: QUALITY_ACCREDITATION_PAGE_TITLES.programReadiness,
    description: 'Program readiness metadata, standards mapping, missing evidence, and gap bands without hidden scoring.',
    route: QUALITY_ACCREDITATION_ROUTES.programReadiness,
    boundaryPage: 'programReadiness',
    sections: [{ title: 'Program readiness metadata', description: 'Internal readiness signals only.', items: programReadiness.data ?? [], emptyMessage: 'No program readiness items recorded.', testId: 'program-readiness-panel' }],
  });
}

export function QualityAccreditationInstitutionalReadinessPage() {
  const institutionalReadiness = useInstitutionalReadinessItems();
  if (institutionalReadiness.isPending) return <LoadingState title="Loading institutional readiness" />;
  if (institutionalReadiness.error) return PageError('Failed to load institutional readiness.', institutionalReadiness.error);
  return renderRegistryPage<InstitutionalReadiness>({
    permission: QUALITY_ACCREDITATION_PERMISSIONS.institutionalReadinessRead,
    title: QUALITY_ACCREDITATION_PAGE_TITLES.institutionalReadiness,
    description: 'Governance, student, academic, research, and document evidence summaries without official ministry submission.',
    route: QUALITY_ACCREDITATION_ROUTES.institutionalReadiness,
    boundaryPage: 'institutionalReadiness',
    sections: [{ title: 'Institutional readiness metadata', description: 'Evidence-backed readiness only.', items: institutionalReadiness.data ?? [], emptyMessage: 'No institutional readiness items recorded.', testId: 'institutional-readiness-panel' }],
  });
}

export function QualityAccreditationSelfAssessmentPage() {
  const reports = useSelfAssessmentReports();
  const sections = useSelfAssessmentSections();
  const state = usePageLoaders(reports, sections);
  if (state.loading) return <LoadingState title="Loading self-assessment" />;
  if (state.error) return PageError('Failed to load self-assessment.', state.error);
  return renderRegistryPage<SelfAssessmentReport | SelfAssessmentSection>({
    permission: QUALITY_ACCREDITATION_PERMISSIONS.selfAssessmentRead,
    title: QUALITY_ACCREDITATION_PAGE_TITLES.selfAssessment,
    description: 'Draft self-assessment reports and sections for internal review only.',
    route: QUALITY_ACCREDITATION_ROUTES.selfAssessment,
    boundaryPage: 'selfAssessment',
    sections: [
      { title: 'Self-assessment reports', description: 'Draft and internal review artifacts only.', items: reports.data ?? [], emptyMessage: 'No self-assessment reports recorded.', testId: 'self-assessment-report-panel' },
      { title: 'Self-assessment sections', description: 'Section ownership, statuses, and limitations.', items: sections.data ?? [], emptyMessage: 'No self-assessment sections recorded.', testId: 'self-assessment-sections-panel' },
    ],
  });
}

export function QualityAccreditationImprovementPlansPage() {
  const plans = useImprovementPlans();
  const actions = useImprovementActions();
  const state = usePageLoaders(plans, actions);
  if (state.loading) return <LoadingState title="Loading improvement plans" />;
  if (state.error) return PageError('Failed to load improvement plans.', state.error);
  return renderRegistryPage<QualityImprovementPlan | QualityImprovementAction>({
    permission: QUALITY_ACCREDITATION_PERMISSIONS.improvementPlansRead,
    title: QUALITY_ACCREDITATION_PAGE_TITLES.improvementPlans,
    description: 'Improvement plans and actions remain human-owned. No autonomous sanctions or automatic program closure.',
    route: QUALITY_ACCREDITATION_ROUTES.improvementPlans,
    boundaryPage: 'improvementPlans',
    sections: [
      { title: 'Improvement plans', description: 'Owner, deadline, and status tracking only.', items: plans.data ?? [], emptyMessage: 'No improvement plans recorded.', testId: 'quality-improvement-plans-panel' },
      { title: 'Improvement actions', description: 'Human-owned actions only.', items: actions.data ?? [], emptyMessage: 'No improvement actions recorded.', testId: 'quality-improvement-actions-panel' },
    ],
  });
}

export function QualityAccreditationInternalAuditsPage() {
  const audits = useInternalAudits();
  const findings = useAuditFindings();
  const auditEvents = useAuditEvents();
  const statusHistory = useStatusHistoryItems();
  const state = usePageLoaders(audits, findings, auditEvents, statusHistory);
  if (state.loading) return <LoadingState title="Loading internal audits" />;
  if (state.error) return PageError('Failed to load internal audits.', state.error);
  return (
    <RequirePermission permission={QUALITY_ACCREDITATION_PERMISSIONS.internalAuditsRead}>
      <ModuleShell
        title={QUALITY_ACCREDITATION_PAGE_TITLES.internalAudits}
        description="Internal audits, findings, audit events, and status history without automatic penalties or hidden scores."
        currentPath={QUALITY_ACCREDITATION_ROUTES.internalAudits}
        boundaryPage="internalAudits"
      >
        <section className="grid gap-6">
          <QualityAccreditationRegistryPanel title="Internal quality audits" description="Audit plans and internal review metadata only." items={audits.data ?? []} emptyMessage="No internal audits recorded." renderItem={(item: InternalQualityAudit) => recordCard(item)} testId="internal-quality-audits-panel" />
          <QualityAccreditationRegistryPanel title="Audit findings" description="Findings and corrective action metadata only." items={findings.data ?? []} emptyMessage="No audit findings recorded." renderItem={(item: QualityAuditFinding) => recordCard(item)} testId="quality-audit-findings-panel" />
          <QualityAccreditationRegistryPanel title="Audit events" description="Append-only audit event stream." items={auditEvents.data ?? []} emptyMessage="No audit events recorded." renderItem={(item: QualityAuditEvent) => auditEventCard(item)} testId="quality-audit-panel" />
          <QualityAccreditationRegistryPanel title="Status history" description="Append-only status transitions for human review." items={statusHistory.data ?? []} emptyMessage="No status history recorded." renderItem={(item: QualityStatusHistory) => statusHistoryCard(item)} testId="quality-status-history-panel" />
        </section>
      </ModuleShell>
    </RequirePermission>
  );
}

export function QualityAccreditationProgramReviewPage() {
  const cycles = useProgramReviewCycles();
  if (cycles.isPending) return <LoadingState title="Loading program review" />;
  if (cycles.error) return PageError('Failed to load program review.', cycles.error);
  return renderRegistryPage<ProgramReviewCycle>({
    permission: QUALITY_ACCREDITATION_PERMISSIONS.programReviewRead,
    title: QUALITY_ACCREDITATION_PAGE_TITLES.programReview,
    description: 'Periodic program review metadata only. No automatic closure or official accreditation approval.',
    route: QUALITY_ACCREDITATION_ROUTES.programReview,
    boundaryPage: 'programReview',
    sections: [{ title: 'Program review cycles', description: 'Curriculum, outcomes, and feedback evidence linkage only.', items: cycles.data ?? [], emptyMessage: 'No program review cycles recorded.', testId: 'program-review-cycle-panel' }],
  });
}

export function QualityAccreditationLearningOutcomesPage() {
  const assessments = useLearningOutcomesAssessments();
  if (assessments.isPending) return <LoadingState title="Loading learning outcomes" />;
  if (assessments.error) return PageError('Failed to load learning outcomes.', assessments.error);
  return renderRegistryPage<LearningOutcomesAssessment>({
    permission: QUALITY_ACCREDITATION_PERMISSIONS.learningOutcomesRead,
    title: QUALITY_ACCREDITATION_PAGE_TITLES.learningOutcomes,
    description: 'Learning outcomes evidence and assessment cycle metadata without automatic grading.',
    route: QUALITY_ACCREDITATION_ROUTES.learningOutcomes,
    boundaryPage: 'learningOutcomes',
    sections: [{ title: 'Learning outcomes assessments', description: 'Assessment cycle metadata only.', items: assessments.data ?? [], emptyMessage: 'No learning outcomes assessments recorded.', testId: 'learning-outcomes-assessment-panel' }],
  });
}

export function QualityAccreditationStakeholderFeedbackPage() {
  const feedback = useStakeholderFeedbackItems();
  const surveys = useSurveyQualityMetadataItems();
  const state = usePageLoaders(feedback, surveys);
  if (state.loading) return <LoadingState title="Loading stakeholder feedback" />;
  if (state.error) return PageError('Failed to load stakeholder feedback.', state.error);
  return renderRegistryPage<StakeholderFeedbackMetadata | SurveyQualityMetadata>({
    permission: QUALITY_ACCREDITATION_PERMISSIONS.feedbackRead,
    title: QUALITY_ACCREDITATION_PAGE_TITLES.stakeholderFeedback,
    description: 'Student, employer, alumni, and faculty feedback metadata without fake survey results or hidden scores.',
    route: QUALITY_ACCREDITATION_ROUTES.stakeholderFeedback,
    boundaryPage: 'stakeholderFeedback',
    sections: [
      { title: 'Stakeholder feedback metadata', description: 'Feedback metadata only.', items: feedback.data ?? [], emptyMessage: 'No stakeholder feedback metadata recorded.', testId: 'stakeholder-feedback-panel' },
      { title: 'Survey quality metadata', description: 'Survey metadata only. No fake survey results.', items: surveys.data ?? [], emptyMessage: 'No survey quality metadata recorded.', testId: 'survey-quality-metadata-panel' },
    ],
  });
}

export function QualityAccreditationCommitteePage() {
  const workflows = useCommitteeWorkflows();
  if (workflows.isPending) return <LoadingState title="Loading committee workflow" />;
  if (workflows.error) return PageError('Failed to load committee workflow.', workflows.error);
  return renderRegistryPage<AccreditationCommitteeWorkflow>({
    permission: QUALITY_ACCREDITATION_PERMISSIONS.committeeRead,
    title: QUALITY_ACCREDITATION_PAGE_TITLES.committee,
    description: 'Committee agenda, decision, and minutes linkage for human decisions only.',
    route: QUALITY_ACCREDITATION_ROUTES.committee,
    boundaryPage: 'committee',
    sections: [{ title: 'Committee workflow metadata', description: 'Human decision records only.', items: workflows.data ?? [], emptyMessage: 'No committee workflows recorded.', testId: 'accreditation-committee-workflow-panel' }],
  });
}

export function QualityAccreditationExternalReviewPage() {
  const reviews = useExternalExpertReviews();
  const responsePlans = useExpertResponsePlans();
  const state = usePageLoaders(reviews, responsePlans);
  if (state.loading) return <LoadingState title="Loading external review" />;
  if (state.error) return PageError('Failed to load external review.', state.error);
  return renderRegistryPage<ExternalExpertReview | ExpertRecommendationResponsePlan>({
    permission: QUALITY_ACCREDITATION_PERMISSIONS.externalReviewRead,
    title: QUALITY_ACCREDITATION_PAGE_TITLES.externalReview,
    description: 'External expert metadata, recommendations, and response plans without fake expert approval claims.',
    route: QUALITY_ACCREDITATION_ROUTES.externalReview,
    boundaryPage: 'externalReview',
    sections: [
      { title: 'External expert reviews', description: 'Review metadata only.', items: reviews.data ?? [], emptyMessage: 'No external expert reviews recorded.', testId: 'external-expert-review-panel' },
      { title: 'Expert response plans', description: 'Response planning metadata only.', items: responsePlans.data ?? [], emptyMessage: 'No expert response plans recorded.', testId: 'expert-response-plan-panel' },
    ],
  });
}

export function QualityAccreditationGapAnalysisPage() {
  const gaps = useGapAnalysisItems();
  if (gaps.isPending) return <LoadingState title="Loading gap analysis" />;
  if (gaps.error) return PageError('Failed to load gap analysis.', gaps.error);
  return renderRegistryPage<ComplianceGapAnalysis>({
    permission: QUALITY_ACCREDITATION_PERMISSIONS.gapAnalysisRead,
    title: QUALITY_ACCREDITATION_PAGE_TITLES.gapAnalysis,
    description: 'Deterministic standards gap metadata for human review only.',
    route: QUALITY_ACCREDITATION_ROUTES.gapAnalysis,
    boundaryPage: 'gapAnalysis',
    sections: [{ title: 'Compliance gap analysis', description: 'Missing evidence, risk band, and recommended next steps only.', items: gaps.data ?? [], emptyMessage: 'No gap analysis items recorded.', testId: 'compliance-gap-analysis-panel' }],
  });
}

export function QualityAccreditationCalendarPage() {
  const calendarItems = useCalendarItems();
  if (calendarItems.isPending) return <LoadingState title="Loading accreditation calendar" />;
  if (calendarItems.error) return PageError('Failed to load accreditation calendar.', calendarItems.error);
  return renderRegistryPage<AccreditationCalendarItem>({
    permission: QUALITY_ACCREDITATION_PERMISSIONS.calendarRead,
    title: QUALITY_ACCREDITATION_PAGE_TITLES.calendar,
    description: 'Accreditation timeline, milestones, and responsible units without official deadline submission claims.',
    route: QUALITY_ACCREDITATION_ROUTES.calendar,
    boundaryPage: 'calendar',
    sections: [{ title: 'Accreditation calendar', description: 'Internal milestone tracking only.', items: calendarItems.data ?? [], emptyMessage: 'No calendar items recorded.', testId: 'accreditation-calendar-panel' }],
  });
}

export function QualityAccreditationRiskRegisterPage() {
  const risks = useRiskRegisterItems();
  if (risks.isPending) return <LoadingState title="Loading risk register" />;
  if (risks.error) return PageError('Failed to load risk register.', risks.error);
  return renderRegistryPage<QualityRisk>({
    permission: QUALITY_ACCREDITATION_PERMISSIONS.riskRegisterRead,
    title: QUALITY_ACCREDITATION_PAGE_TITLES.riskRegister,
    description: 'Quality and accreditation risks, mitigations, and ownership without automated sanctions.',
    route: QUALITY_ACCREDITATION_ROUTES.riskRegister,
    boundaryPage: 'riskRegister',
    sections: [{ title: 'Quality risk register', description: 'Mitigation plans and owners only.', items: risks.data ?? [], emptyMessage: 'No quality risks recorded.', testId: 'quality-risk-register-panel' }],
  });
}

export function QualityAccreditationBridgesPage() {
  const bridges = useBridgeItems();
  const brainSignals = useBrainSignals();
  const state = usePageLoaders(bridges, brainSignals);
  if (state.loading) return <LoadingState title="Loading bridges" />;
  if (state.error) return PageError('Failed to load bridges.', state.error);
  return (
    <RequirePermission permission={QUALITY_ACCREDITATION_PERMISSIONS.bridgesRead}>
      <ModuleShell
        title={QUALITY_ACCREDITATION_PAGE_TITLES.bridges}
        description="Read-only-first bridges and brain-signal metadata without cross-suite mutation or provider sync."
        currentPath={QUALITY_ACCREDITATION_ROUTES.bridges}
        boundaryPage="bridges"
      >
        <section className="grid gap-6">
          <section className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
            {QUALITY_ACCREDITATION_BRIDGE_TARGETS.map((target) => (
              <QualityAccreditationBridgeCard key={target.key} title={target.title} description={target.description} />
            ))}
          </section>
          <QualityAccreditationRegistryPanel title="Quality bridge metadata" description="Bridge records remain read-only-first by default." items={bridges.data ?? []} emptyMessage="No bridge records recorded." renderItem={(item: QualityBridge) => recordCard(item)} testId="quality-bridge-panel" />
          <QualityAccreditationRegistryPanel title="Quality brain signals" description="Brain-signal metadata only. Human review required." items={brainSignals.data ?? []} emptyMessage="No brain signals recorded." renderItem={(item: QualityBrainSignal) => recordCard(item)} testId="quality-brain-signals-panel" />
        </section>
      </ModuleShell>
    </RequirePermission>
  );
}

export function QualityAccreditationLimitationsPage() {
  const limitations = useQualityAccreditationLimitations();
  if (limitations.isPending) return <LoadingState title="Loading limitations" />;
  if (limitations.error) return PageError('Failed to load limitations.', limitations.error);
  return (
    <RequirePermission permission={QUALITY_ACCREDITATION_PERMISSIONS.limitationsRead}>
      <ModuleShell
        title={QUALITY_ACCREDITATION_PAGE_TITLES.limitations}
        description="Explicit safety boundaries, limitations, and forbidden-action posture for the current frontend runtime."
        currentPath={QUALITY_ACCREDITATION_ROUTES.limitations}
        boundaryPage="limitations"
      >
        <section className="grid gap-6">
          <QualityAccreditationLimitationsPanel limitations={[...QUALITY_ACCREDITATION_LIMITATIONS, ...(limitations.data ?? [])]} />
          <section className="rounded-lg border p-4">
            <h2 className="text-lg font-semibold">Forbidden actions</h2>
            <ul className="mt-3 space-y-2 text-sm text-muted-foreground">
              {QUALITY_ACCREDITATION_FORBIDDEN_ACTIONS.map((item) => (
                <li key={item}>- {item}</li>
              ))}
            </ul>
          </section>
          <section className="rounded-lg border p-4">
            <h2 className="text-lg font-semibold">Runtime safety anchors</h2>
            <div className="mt-3 grid gap-3 md:grid-cols-2 xl:grid-cols-4">
              <QualityAccreditationMetricCard label="Backend baseline" value={`${QUALITY_ACCREDITATION_BACKEND_TABLE_COUNT}/${QUALITY_ACCREDITATION_BACKEND_ROUTE_COUNT}/${QUALITY_ACCREDITATION_BACKEND_PERMISSION_COUNT}`} helper="tables / routes / permissions" />
              <QualityAccreditationMetricCard label="Human review required" value={String(HUMAN_REVIEW_REQUIRED)} />
              <QualityAccreditationMetricCard label="fake_metrics" value={String(FAKE_METRICS)} />
              <QualityAccreditationMetricCard label="fake_evidence" value={String(FAKE_EVIDENCE)} />
            </div>
            <div className="mt-4 flex flex-wrap gap-2">
              {QUALITY_ACCREDITATION_BOUNDARY_COPY.map((label) => (
                <BoundaryBadge key={label} label={label} />
              ))}
            </div>
          </section>
        </section>
      </ModuleShell>
    </RequirePermission>
  );
}