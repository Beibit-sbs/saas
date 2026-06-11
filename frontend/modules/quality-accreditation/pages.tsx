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
  AccreditationEvidenceItem,
  AccreditationEvidenceRuntimeResponse,
  AccreditationProviderSummary,
  AccreditationReadinessSummary,
  AccreditationRegistryItem,
  AccreditationRiskSummary,
  AccreditationStatusSummary,
  AccreditationCalendarItem,
  AccreditationCommitteeWorkflow,
  AccreditationStandard,
  ComplianceGapAnalysis,
  CorrectiveActionItem,
  CorrectiveActionOverdueSummary,
  CorrectiveActionReadinessSummary,
  CorrectiveActionRiskSummary,
  CorrectiveActionRuntimeResponse,
  CorrectiveActionSummary,
  EvidenceLimitation,
  EvidenceCategorySummary,
  EvidenceCoverageSummary,
  EvidenceReadinessSummary,
  EvidenceRiskSummary,
  ExpertRecommendationResponsePlan,
  ExternalExpertReview,
  InstitutionalReadiness,
  InternalQualityAudit,
  LearningOutcomesAssessment,
  ImprovementForecast,
  ImprovementInitiative,
  ImprovementKpiTarget,
  ImprovementMilestone,
  ImprovementPlanRuntime,
  ImprovementPlanRuntimeResponse,
  ImprovementRoadmap,
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
  SelfAssessmentRuntimeResponse,
  SelfAssessmentCoverageSummary,
  SelfAssessmentReadinessSummary,
  SelfAssessmentRiskSummary,
  SelfAssessmentScorecard,
  SelfAssessmentSection,
  SelfAssessmentStandard,
  StakeholderFeedbackMetadata,
  StandardCriterion,
  StandardsEvidenceRequirement,
  SurveyQualityMetadata,
} from './types';

const CACHE_KEYS = {
  health: ['quality-accreditation:health'] as const,
  overview: ['quality-accreditation:overview'] as const,
  accreditationEvidence: ['quality-accreditation:accreditation-evidence'] as const,
  selfAssessmentRuntime: ['quality-accreditation:self-assessment-runtime'] as const,
  correctiveActionRuntime: ['quality-accreditation:corrective-action-runtime'] as const,
  improvementPlanRuntime: ['quality-accreditation:improvement-plan-runtime'] as const,
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

function useAccreditationRegistry() {
  return useQuery({
    queryKey: ['quality-accreditation:accreditation-registry'],
    queryFn: qualityAccreditationApi.getAccreditationRegistry,
    staleTime: 30000,
  });
}

function useAccreditationEvidenceRuntime() {
  return useQuery({
    queryKey: CACHE_KEYS.accreditationEvidence,
    queryFn: qualityAccreditationApi.getAccreditationEvidenceRuntime,
    staleTime: 30000,
  });
}

function useSelfAssessmentRuntime() {
  return useQuery({
    queryKey: CACHE_KEYS.selfAssessmentRuntime,
    queryFn: qualityAccreditationApi.getSelfAssessmentRuntime,
    staleTime: 30000,
  });
}

function useCorrectiveActionRuntime() {
  return useQuery({
    queryKey: CACHE_KEYS.correctiveActionRuntime,
    queryFn: qualityAccreditationApi.getCorrectiveActionRuntime,
    staleTime: 30000,
  });
}

function useImprovementPlanRuntimeQuery() {
  return useQuery({
    queryKey: CACHE_KEYS.improvementPlanRuntime,
    queryFn: qualityAccreditationApi.useImprovementPlanRuntime,
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

function formatRegistryDate(value: string) {
  return new Intl.DateTimeFormat('en-GB', { year: 'numeric', month: 'short', day: '2-digit' }).format(new Date(value));
}

function AccreditationRegistryRowCard({ item }: { item: AccreditationRegistryItem }) {
  return (
    <div className="rounded-lg border p-4" data-testid={`accreditation-registry-item-${slugify(item.accreditation_id)}`}>
      <p className="text-sm font-semibold">{item.accreditation_name}</p>
      <p className="mt-1 text-xs text-muted-foreground">{item.accreditation_id}</p>
      <div className="mt-3 grid gap-2 text-sm text-muted-foreground">
        <p>Type: {item.accreditation_type}</p>
        <p>Scope: {item.accreditation_scope}</p>
        <p>Provider: {item.provider}</p>
        <p>Status: {item.status}</p>
        <p>Issued: {formatRegistryDate(item.issued_date)}</p>
        <p>Expiry: {formatRegistryDate(item.expiry_date)}</p>
        <p>Readiness: {item.readiness_score}</p>
        <p>Risk: {item.risk_level}</p>
      </div>
    </div>
  );
}

function AccreditationProviderSummaryCard({ item }: { item: AccreditationProviderSummary }) {
  return (
    <div className="rounded-lg border p-4" data-testid={`accreditation-provider-${slugify(item.provider)}`}>
      <p className="text-sm font-semibold">{item.provider}</p>
      <div className="mt-3 grid gap-2 text-sm text-muted-foreground">
        <p>Accreditations: {item.accreditation_count}</p>
        <p>Active: {item.active_count}</p>
        <p>Expiring: {item.expiring_count}</p>
      </div>
    </div>
  );
}

function AccreditationStatusSummaryCard({ item }: { item: AccreditationStatusSummary }) {
  return (
    <div className="rounded-lg border p-4" data-testid={`accreditation-status-${slugify(item.status)}`}>
      <p className="text-sm font-semibold">{item.status}</p>
      <p className="mt-3 text-sm text-muted-foreground">Accreditations: {item.accreditation_count}</p>
    </div>
  );
}

function AccreditationReadinessSummaryCard({ item }: { item: AccreditationReadinessSummary }) {
  return (
    <div className="rounded-lg border p-4" data-testid={`accreditation-readiness-${slugify(item.readiness_band)}`}>
      <p className="text-sm font-semibold">{item.readiness_band}</p>
      <div className="mt-3 grid gap-2 text-sm text-muted-foreground">
        <p>Accreditations: {item.accreditation_count}</p>
        <p>Average readiness: {item.average_readiness_score.toFixed(1)}</p>
      </div>
    </div>
  );
}

function AccreditationRiskSummaryCard({ item }: { item: AccreditationRiskSummary }) {
  return (
    <div className="rounded-lg border p-4" data-testid={`accreditation-risk-${slugify(item.risk_level)}`}>
      <p className="text-sm font-semibold">{item.risk_level}</p>
      <p className="mt-3 text-sm text-muted-foreground">Accreditations: {item.accreditation_count}</p>
    </div>
  );
}

function AccreditationRegistryTable({ items }: { items: AccreditationRegistryItem[] }) {
  return (
    <section className="rounded-lg border p-4" data-testid="accreditation-registry-table">
      <div className="space-y-1">
        <h2 className="text-lg font-semibold">Accreditation registry</h2>
        <p className="text-sm text-muted-foreground">Read-only registry of active accreditation metadata, expiry timing, readiness, and risk.</p>
      </div>
      <div className="mt-4 overflow-x-auto">
        <table className="min-w-full divide-y divide-border text-left text-sm">
          <thead>
            <tr className="text-xs uppercase tracking-wide text-muted-foreground">
              <th className="px-3 py-2">Accreditation</th>
              <th className="px-3 py-2">Provider</th>
              <th className="px-3 py-2">Status</th>
              <th className="px-3 py-2">Expiry</th>
              <th className="px-3 py-2">Readiness</th>
              <th className="px-3 py-2">Risk</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border">
            {items.length === 0 ? (
              <tr>
                <td className="px-3 py-4 text-muted-foreground" colSpan={6}>No accreditations recorded.</td>
              </tr>
            ) : (
              items.map((item) => (
                <tr key={item.accreditation_id}>
                  <td className="px-3 py-3">
                    <div className="space-y-1">
                      <p className="font-medium">{item.accreditation_name}</p>
                      <p className="text-xs text-muted-foreground">{item.accreditation_id}</p>
                      <p className="text-xs text-muted-foreground">{item.accreditation_type} / {item.accreditation_scope}</p>
                    </div>
                  </td>
                  <td className="px-3 py-3">{item.provider}</td>
                  <td className="px-3 py-3">{item.status}</td>
                  <td className="px-3 py-3">{formatRegistryDate(item.expiry_date)}</td>
                  <td className="px-3 py-3">{item.readiness_score}</td>
                  <td className="px-3 py-3">{item.risk_level}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
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

export function QualityAccreditationAccreditationRegistryPage() {
  const registry = useAccreditationRegistry();

  if (registry.isPending) return <LoadingState title="Loading accreditation registry" />;
  if (registry.error) return PageError('Failed to load accreditation registry.', registry.error);
  if (!registry.data) return <ErrorState message="Accreditation registry is unavailable." />;

  return (
    <RequirePermission permission={QUALITY_ACCREDITATION_PERMISSIONS.summaryRead}>
      <ModuleShell
        title={QUALITY_ACCREDITATION_PAGE_TITLES.accreditationRegistry}
        description="Read-only accreditation registry runtime with active and expiring accreditation visibility, provider summaries, and risk/readiness aggregation."
        currentPath={QUALITY_ACCREDITATION_ROUTES.accreditationRegistry}
        boundaryPage="accreditationRegistry"
      >
        <section className="grid gap-6" data-testid="accreditation-registry-runtime">
          <section className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
            <QualityAccreditationMetricCard label="Active accreditations" value={registry.data.active_accreditations.length} helper="Read-only registry entries." />
            <QualityAccreditationMetricCard label="Expiring accreditations" value={registry.data.expiring_accreditations.length} helper="Within the registry expiry window." />
            <QualityAccreditationMetricCard label="Read-only" value={String(registry.data.read_only)} helper="Aggregator-only runtime." />
            <QualityAccreditationMetricCard label="Aggregator-only" value={String(registry.data.aggregator_only)} helper="No write operations." />
          </section>

          <QualityAccreditationRegistryPanel
            title="Provider summary"
            description="Internal provider labels and activation counts derived from registry metadata."
            items={registry.data.accreditation_provider}
            emptyMessage="No provider summary available."
            renderItem={(item: AccreditationProviderSummary) => <AccreditationProviderSummaryCard item={item} />}
            testId="accreditation-provider-summary"
          />

          <QualityAccreditationRegistryPanel
            title="Status summary"
            description="Registry status distribution for active accreditation metadata."
            items={registry.data.accreditation_status}
            emptyMessage="No status summary available."
            renderItem={(item: AccreditationStatusSummary) => <AccreditationStatusSummaryCard item={item} />}
            testId="accreditation-status-summary"
          />

          <QualityAccreditationRegistryPanel
            title="Readiness summary"
            description="Readiness bands and average scores for accreditation metadata."
            items={registry.data.accreditation_readiness}
            emptyMessage="No readiness summary available."
            renderItem={(item: AccreditationReadinessSummary) => <AccreditationReadinessSummaryCard item={item} />}
            testId="accreditation-readiness-summary"
          />

          <QualityAccreditationRegistryPanel
            title="Risk summary"
            description="Risk bands derived from the registry's read-only aggregation layer."
            items={registry.data.accreditation_risk}
            emptyMessage="No risk summary available."
            renderItem={(item: AccreditationRiskSummary) => <AccreditationRiskSummaryCard item={item} />}
            testId="accreditation-risk-summary"
          />

          <AccreditationRegistryTable items={registry.data.active_accreditations} />

          <QualityAccreditationRegistryPanel
            title="Expiring accreditation watchlist"
            description="Accreditations nearing expiry within the read-only aggregation window."
            items={registry.data.expiring_accreditations}
            emptyMessage="No accreditations are currently nearing expiry."
            renderItem={(item: AccreditationRegistryItem) => <AccreditationRegistryRowCard item={item} />}
            testId="accreditation-expiring-watchlist"
          />
        </section>
      </ModuleShell>
    </RequirePermission>
  );
}

function formatEvidenceDate(value: string) {
  return new Intl.DateTimeFormat('en-GB', { year: 'numeric', month: 'short', day: '2-digit' }).format(new Date(value));
}

function EvidenceCategorySummaryCard({ item }: { item: EvidenceCategorySummary }) {
  return (
    <div className="rounded-lg border p-4" data-testid={`evidence-category-${slugify(item.evidence_category)}`}>
      <p className="text-sm font-semibold">{item.evidence_category}</p>
      <div className="mt-3 grid gap-2 text-sm text-muted-foreground">
        <p>Evidence count: {item.evidence_count}</p>
        <p>Average completeness: {item.average_completeness_score.toFixed(1)}</p>
      </div>
    </div>
  );
}

function EvidenceReadinessSummaryCard({ item }: { item: EvidenceReadinessSummary }) {
  return (
    <div className="rounded-lg border p-4" data-testid={`evidence-readiness-${slugify(item.readiness_band)}`}>
      <p className="text-sm font-semibold">{item.readiness_band}</p>
      <p className="mt-3 text-sm text-muted-foreground">Evidence count: {item.evidence_count}</p>
    </div>
  );
}

function EvidenceCoverageSummaryCard({ item }: { item: EvidenceCoverageSummary }) {
  return (
    <div className="rounded-lg border p-4" data-testid={`evidence-coverage-${slugify(item.coverage_scope)}`}>
      <p className="text-sm font-semibold">{item.coverage_scope}</p>
      <div className="mt-3 grid gap-2 text-sm text-muted-foreground">
        <p>Evidence count: {item.evidence_count}</p>
        <p>Covered: {item.covered_count}</p>
        <p>Coverage %: {item.coverage_percent.toFixed(1)}</p>
      </div>
    </div>
  );
}

function EvidenceRiskSummaryCard({ item }: { item: EvidenceRiskSummary }) {
  return (
    <div className="rounded-lg border p-4" data-testid={`evidence-risk-${slugify(item.risk_level)}`}>
      <p className="text-sm font-semibold">{item.risk_level}</p>
      <p className="mt-3 text-sm text-muted-foreground">Evidence count: {item.evidence_count}</p>
    </div>
  );
}

function EvidenceInventoryTable({ items }: { items: AccreditationEvidenceItem[] }) {
  return (
    <section className="rounded-lg border p-4" data-testid="evidence-inventory-table">
      <div className="space-y-1">
        <h2 className="text-lg font-semibold">Evidence inventory</h2>
        <p className="text-sm text-muted-foreground">Read-only accreditation evidence inventory with category, standard, completeness, and risk visibility.</p>
      </div>
      <div className="mt-4 overflow-x-auto">
        <table className="min-w-full divide-y divide-border text-left text-sm">
          <thead>
            <tr className="text-xs uppercase tracking-wide text-muted-foreground">
              <th className="px-3 py-2">Evidence</th>
              <th className="px-3 py-2">Category</th>
              <th className="px-3 py-2">Standard</th>
              <th className="px-3 py-2">Owner Unit</th>
              <th className="px-3 py-2">Status</th>
              <th className="px-3 py-2">Completeness</th>
              <th className="px-3 py-2">Risk</th>
              <th className="px-3 py-2">Last Updated</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border">
            {items.length === 0 ? (
              <tr>
                <td className="px-3 py-4 text-muted-foreground" colSpan={8}>No evidence inventory recorded.</td>
              </tr>
            ) : (
              items.map((item) => (
                <tr key={item.evidence_id}>
                  <td className="px-3 py-3">
                    <div className="space-y-1">
                      <p className="font-medium">{item.evidence_name}</p>
                      <p className="text-xs text-muted-foreground">{item.evidence_id}</p>
                      <p className="text-xs text-muted-foreground">{item.accreditation_section}</p>
                    </div>
                  </td>
                  <td className="px-3 py-3">{item.evidence_category}</td>
                  <td className="px-3 py-3">{item.accreditation_standard}</td>
                  <td className="px-3 py-3">{item.owner_unit}</td>
                  <td className="px-3 py-3">{item.evidence_status}</td>
                  <td className="px-3 py-3">{item.completeness_score}</td>
                  <td className="px-3 py-3">{item.risk_level}</td>
                  <td className="px-3 py-3">{formatEvidenceDate(item.last_updated)}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </section>
  );
}

function EvidenceSummarySection({ data }: { data: AccreditationEvidenceRuntimeResponse }) {
  return (
    <>
      <QualityAccreditationRegistryPanel
        title="Evidence category summary"
        description="Evidence distribution and completeness by category."
        items={data.evidence_categories}
        emptyMessage="No evidence category summary available."
        renderItem={(item: EvidenceCategorySummary) => <EvidenceCategorySummaryCard item={item} />}
        testId="evidence-category-summary"
      />

      <QualityAccreditationRegistryPanel
        title="Evidence readiness summary"
        description="Readiness distribution based on evidence completeness bands."
        items={data.evidence_readiness}
        emptyMessage="No evidence readiness summary available."
        renderItem={(item: EvidenceReadinessSummary) => <EvidenceReadinessSummaryCard item={item} />}
        testId="evidence-readiness-summary"
      />

      <QualityAccreditationRegistryPanel
        title="Evidence coverage summary"
        description="Coverage of evidence by accreditation standard/category scope."
        items={data.evidence_coverage}
        emptyMessage="No evidence coverage summary available."
        renderItem={(item: EvidenceCoverageSummary) => <EvidenceCoverageSummaryCard item={item} />}
        testId="evidence-coverage-summary"
      />

      <QualityAccreditationRegistryPanel
        title="Evidence risk summary"
        description="Risk distribution derived from evidence status and limitation posture."
        items={data.evidence_risk}
        emptyMessage="No evidence risk summary available."
        renderItem={(item: EvidenceRiskSummary) => <EvidenceRiskSummaryCard item={item} />}
        testId="evidence-risk-summary"
      />
    </>
  );
}

export function QualityAccreditationAccreditationEvidenceRuntimePage() {
  const evidenceRuntime = useAccreditationEvidenceRuntime();

  if (evidenceRuntime.isPending) return <LoadingState title="Loading accreditation evidence runtime" />;
  if (evidenceRuntime.error) return PageError('Failed to load accreditation evidence runtime.', evidenceRuntime.error);
  if (!evidenceRuntime.data) return <ErrorState message="Accreditation evidence runtime is unavailable." />;

  return (
    <RequirePermission permission={QUALITY_ACCREDITATION_PERMISSIONS.summaryRead}>
      <ModuleShell
        title={QUALITY_ACCREDITATION_PAGE_TITLES.accreditationEvidence}
        description="Read-only accreditation evidence runtime with evidence inventory, readiness, coverage, and risk summaries."
        currentPath={QUALITY_ACCREDITATION_ROUTES.accreditationEvidence}
        boundaryPage="accreditationEvidence"
      >
        <section className="grid gap-6" data-testid="accreditation-evidence-runtime">
          <section className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
            <QualityAccreditationMetricCard label="Evidence items" value={evidenceRuntime.data.evidence_inventory.length} helper="Read-only evidence inventory records." />
            <QualityAccreditationMetricCard label="Category groups" value={evidenceRuntime.data.evidence_categories.length} helper="Aggregated evidence categories." />
            <QualityAccreditationMetricCard label="Read-only" value={String(evidenceRuntime.data.read_only)} helper="No write operations." />
            <QualityAccreditationMetricCard label="Aggregator-only" value={String(evidenceRuntime.data.aggregator_only)} helper="Visibility-only runtime." />
          </section>

          <EvidenceSummarySection data={evidenceRuntime.data} />
          <EvidenceInventoryTable items={evidenceRuntime.data.evidence_inventory} />
        </section>
      </ModuleShell>
    </RequirePermission>
  );
}

function SelfAssessmentScorecardSection({ scorecard }: { scorecard: SelfAssessmentScorecard }) {
  return (
    <section className="rounded-lg border p-4" data-testid="self-assessment-scorecard">
      <div className="space-y-1">
        <h2 className="text-lg font-semibold">Self-assessment scorecard</h2>
        <p className="text-sm text-muted-foreground">Aggregated scorecard for accreditation preparation visibility.</p>
      </div>
      <div className="mt-4 grid gap-3 md:grid-cols-2 xl:grid-cols-4">
        <QualityAccreditationMetricCard label="Standards total" value={scorecard.standards_total} />
        <QualityAccreditationMetricCard label="Ready standards" value={scorecard.ready_standards} />
        <QualityAccreditationMetricCard label="Avg readiness" value={scorecard.average_readiness_score.toFixed(1)} />
        <QualityAccreditationMetricCard label="Avg completion" value={scorecard.average_completion_percentage.toFixed(1)} />
        <QualityAccreditationMetricCard label="Avg evidence coverage" value={scorecard.average_evidence_coverage.toFixed(1)} />
        <QualityAccreditationMetricCard label="High risk standards" value={scorecard.high_risk_standards} />
        <QualityAccreditationMetricCard label="Gap total" value={scorecard.gap_total} />
        <QualityAccreditationMetricCard label="Read-only" value={String(scorecard.read_only)} />
      </div>
    </section>
  );
}

function SelfAssessmentReadinessCard({ item }: { item: SelfAssessmentReadinessSummary }) {
  return (
    <div className="rounded-lg border p-4" data-testid={`self-assessment-readiness-${slugify(item.readiness_band)}`}>
      <p className="text-sm font-semibold">{item.readiness_band}</p>
      <div className="mt-3 grid gap-2 text-sm text-muted-foreground">
        <p>Standards: {item.standard_count}</p>
        <p>Average score: {item.average_readiness_score.toFixed(1)}</p>
      </div>
    </div>
  );
}

function SelfAssessmentCoverageCard({ item }: { item: SelfAssessmentCoverageSummary }) {
  return (
    <div className="rounded-lg border p-4" data-testid={`self-assessment-coverage-${slugify(item.coverage_scope)}`}>
      <p className="text-sm font-semibold">{item.coverage_scope}</p>
      <div className="mt-3 grid gap-2 text-sm text-muted-foreground">
        <p>Standards: {item.standard_count}</p>
        <p>Avg coverage: {item.average_evidence_coverage.toFixed(1)}</p>
      </div>
    </div>
  );
}

function SelfAssessmentRiskCard({ item }: { item: SelfAssessmentRiskSummary }) {
  return (
    <div className="rounded-lg border p-4" data-testid={`self-assessment-risk-${slugify(item.risk_level)}`}>
      <p className="text-sm font-semibold">{item.risk_level}</p>
      <p className="mt-3 text-sm text-muted-foreground">Standards: {item.standard_count}</p>
    </div>
  );
}

function SelfAssessmentStandardsTable({ standards }: { standards: SelfAssessmentStandard[] }) {
  return (
    <section className="rounded-lg border p-4" data-testid="self-assessment-standards-table">
      <div className="space-y-1">
        <h2 className="text-lg font-semibold">Self-assessment standards</h2>
        <p className="text-sm text-muted-foreground">Read-only standards readiness table with completion, evidence coverage, gap, and risk signals.</p>
      </div>
      <div className="mt-4 overflow-x-auto">
        <table className="min-w-full divide-y divide-border text-left text-sm">
          <thead>
            <tr className="text-xs uppercase tracking-wide text-muted-foreground">
              <th className="px-3 py-2">Standard</th>
              <th className="px-3 py-2">Framework</th>
              <th className="px-3 py-2">Readiness</th>
              <th className="px-3 py-2">Completion %</th>
              <th className="px-3 py-2">Evidence Coverage</th>
              <th className="px-3 py-2">Gap Count</th>
              <th className="px-3 py-2">Risk</th>
              <th className="px-3 py-2">Owner</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border">
            {standards.length === 0 ? (
              <tr>
                <td className="px-3 py-4 text-muted-foreground" colSpan={8}>No standards available.</td>
              </tr>
            ) : (
              standards.map((item) => (
                <tr key={item.standard_id}>
                  <td className="px-3 py-3">
                    <div className="space-y-1">
                      <p className="font-medium">{item.standard_name}</p>
                      <p className="text-xs text-muted-foreground">{item.standard_id}</p>
                    </div>
                  </td>
                  <td className="px-3 py-3">{item.accreditation_framework}</td>
                  <td className="px-3 py-3">{item.readiness_score}</td>
                  <td className="px-3 py-3">{item.completion_percentage}</td>
                  <td className="px-3 py-3">{item.evidence_coverage}</td>
                  <td className="px-3 py-3">{item.gap_count}</td>
                  <td className="px-3 py-3">{item.risk_level}</td>
                  <td className="px-3 py-3">{item.owner_unit}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </section>
  );
}

function SelfAssessmentRuntimeSummary({ data }: { data: SelfAssessmentRuntimeResponse }) {
  return (
    <>
      <QualityAccreditationRegistryPanel
        title="Readiness summary"
        description="Readiness distribution and average readiness score across standards."
        items={data.readiness_summary}
        emptyMessage="No readiness summary available."
        renderItem={(item: SelfAssessmentReadinessSummary) => <SelfAssessmentReadinessCard item={item} />}
        testId="self-assessment-readiness-summary"
      />
      <QualityAccreditationRegistryPanel
        title="Coverage summary"
        description="Evidence coverage summary grouped by accreditation framework."
        items={data.coverage_summary}
        emptyMessage="No coverage summary available."
        renderItem={(item: SelfAssessmentCoverageSummary) => <SelfAssessmentCoverageCard item={item} />}
        testId="self-assessment-coverage-summary"
      />
      <QualityAccreditationRegistryPanel
        title="Risk summary"
        description="Risk distribution derived from standards readiness and gaps."
        items={data.risk_summary}
        emptyMessage="No risk summary available."
        renderItem={(item: SelfAssessmentRiskSummary) => <SelfAssessmentRiskCard item={item} />}
        testId="self-assessment-risk-summary"
      />
    </>
  );
}

export function QualityAccreditationSelfAssessmentRuntimePage() {
  const runtime = useSelfAssessmentRuntime();

  if (runtime.isPending) return <LoadingState title="Loading self assessment runtime" />;
  if (runtime.error) return PageError('Failed to load self assessment runtime.', runtime.error);
  if (!runtime.data) return <ErrorState message="Self assessment runtime is unavailable." />;

  return (
    <RequirePermission permission={QUALITY_ACCREDITATION_PERMISSIONS.summaryRead}>
      <ModuleShell
        title={QUALITY_ACCREDITATION_PAGE_TITLES.selfAssessment}
        description="Read-only self-assessment runtime with standards readiness, completion, coverage, and risk visibility."
        currentPath={QUALITY_ACCREDITATION_ROUTES.selfAssessment}
        boundaryPage="selfAssessment"
      >
        <section className="grid gap-6" data-testid="self-assessment-runtime">
          <section className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
            <QualityAccreditationMetricCard label="Standards" value={runtime.data.standards.length} helper="Read-only standards inventory." />
            <QualityAccreditationMetricCard label="Readiness groups" value={runtime.data.readiness_summary.length} helper="Readiness summary groups." />
            <QualityAccreditationMetricCard label="Read-only" value={String(runtime.data.read_only)} helper="No write operations." />
            <QualityAccreditationMetricCard label="Aggregator-only" value={String(runtime.data.aggregator_only)} helper="Visibility-only runtime." />
          </section>
          <SelfAssessmentScorecardSection scorecard={runtime.data.scorecard} />
          <SelfAssessmentRuntimeSummary data={runtime.data} />
          <SelfAssessmentStandardsTable standards={runtime.data.standards} />
        </section>
      </ModuleShell>
    </RequirePermission>
  );
}

function formatCorrectiveDate(value: string) {
  return new Intl.DateTimeFormat('en-GB', { year: 'numeric', month: 'short', day: '2-digit' }).format(new Date(value));
}

function CorrectiveActionSummaryPanel({ summary }: { summary: CorrectiveActionSummary }) {
  return (
    <section className="rounded-lg border p-4" data-testid="corrective-action-summary">
      <div className="space-y-1">
        <h2 className="text-lg font-semibold">Corrective action summary</h2>
        <p className="text-sm text-muted-foreground">Aggregated remediation progress and overdue posture.</p>
      </div>
      <div className="mt-4 grid gap-3 md:grid-cols-2 xl:grid-cols-5">
        <QualityAccreditationMetricCard label="Total actions" value={summary.total_actions} />
        <QualityAccreditationMetricCard label="Completed" value={summary.completed_actions} />
        <QualityAccreditationMetricCard label="In progress" value={summary.in_progress_actions} />
        <QualityAccreditationMetricCard label="Overdue" value={summary.overdue_actions} />
        <QualityAccreditationMetricCard label="Avg completion" value={summary.average_completion_percentage.toFixed(1)} />
      </div>
    </section>
  );
}

function CorrectiveReadinessCard({ item }: { item: CorrectiveActionReadinessSummary }) {
  return (
    <div className="rounded-lg border p-4" data-testid={`corrective-readiness-${slugify(item.readiness_band)}`}>
      <p className="text-sm font-semibold">{item.readiness_band}</p>
      <div className="mt-3 grid gap-2 text-sm text-muted-foreground">
        <p>Actions: {item.action_count}</p>
        <p>Average score: {item.average_readiness_score.toFixed(1)}</p>
      </div>
    </div>
  );
}

function CorrectiveRiskCard({ item }: { item: CorrectiveActionRiskSummary }) {
  return (
    <div className="rounded-lg border p-4" data-testid={`corrective-risk-${slugify(item.risk_level)}`}>
      <p className="text-sm font-semibold">{item.risk_level}</p>
      <p className="mt-3 text-sm text-muted-foreground">Actions: {item.action_count}</p>
    </div>
  );
}

function CorrectiveOverdueCard({ item }: { item: CorrectiveActionOverdueSummary }) {
  return (
    <div className="rounded-lg border p-4" data-testid={`corrective-overdue-${slugify(item.overdue_state)}`}>
      <p className="text-sm font-semibold">{item.overdue_state}</p>
      <p className="mt-3 text-sm text-muted-foreground">Actions: {item.action_count}</p>
    </div>
  );
}

function CorrectiveActionTable({ items }: { items: CorrectiveActionItem[] }) {
  return (
    <section className="rounded-lg border p-4" data-testid="corrective-action-table">
      <div className="space-y-1">
        <h2 className="text-lg font-semibold">Corrective actions</h2>
        <p className="text-sm text-muted-foreground">Read-only remediation table with readiness, risk, and overdue visibility.</p>
      </div>
      <div className="mt-4 overflow-x-auto">
        <table className="min-w-full divide-y divide-border text-left text-sm">
          <thead>
            <tr className="text-xs uppercase tracking-wide text-muted-foreground">
              <th className="px-3 py-2">Action</th>
              <th className="px-3 py-2">Standard</th>
              <th className="px-3 py-2">Finding</th>
              <th className="px-3 py-2">Owner</th>
              <th className="px-3 py-2">Due Date</th>
              <th className="px-3 py-2">Completion %</th>
              <th className="px-3 py-2">Status</th>
              <th className="px-3 py-2">Readiness</th>
              <th className="px-3 py-2">Risk</th>
              <th className="px-3 py-2">Overdue</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border">
            {items.length === 0 ? (
              <tr>
                <td className="px-3 py-4 text-muted-foreground" colSpan={10}>No corrective actions available.</td>
              </tr>
            ) : (
              items.map((item) => (
                <tr key={item.action_id}>
                  <td className="px-3 py-3">
                    <div className="space-y-1">
                      <p className="font-medium">{item.action_title}</p>
                      <p className="text-xs text-muted-foreground">{item.action_id}</p>
                    </div>
                  </td>
                  <td className="px-3 py-3">{item.accreditation_standard}</td>
                  <td className="px-3 py-3">{item.finding_reference}</td>
                  <td className="px-3 py-3">{item.owner_unit}</td>
                  <td className="px-3 py-3">{formatCorrectiveDate(item.due_date)}</td>
                  <td className="px-3 py-3">{item.completion_percentage}</td>
                  <td className="px-3 py-3">{item.status}</td>
                  <td className="px-3 py-3">{item.readiness_score}</td>
                  <td className="px-3 py-3">{item.risk_level}</td>
                  <td className="px-3 py-3">{String(item.overdue_flag)}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </section>
  );
}

function CorrectiveActionRuntimeSummary({ data }: { data: CorrectiveActionRuntimeResponse }) {
  return (
    <>
      <QualityAccreditationRegistryPanel
        title="Readiness summary"
        description="Corrective action readiness bands and average readiness scores."
        items={data.readiness_summary}
        emptyMessage="No readiness summary available."
        renderItem={(item: CorrectiveActionReadinessSummary) => <CorrectiveReadinessCard item={item} />}
        testId="corrective-action-readiness-summary"
      />
      <QualityAccreditationRegistryPanel
        title="Risk summary"
        description="Corrective action risk distribution."
        items={data.risk_summary}
        emptyMessage="No risk summary available."
        renderItem={(item: CorrectiveActionRiskSummary) => <CorrectiveRiskCard item={item} />}
        testId="corrective-action-risk-summary"
      />
      <QualityAccreditationRegistryPanel
        title="Overdue summary"
        description="Corrective action overdue state distribution."
        items={data.overdue_summary}
        emptyMessage="No overdue summary available."
        renderItem={(item: CorrectiveActionOverdueSummary) => <CorrectiveOverdueCard item={item} />}
        testId="corrective-action-overdue-summary"
      />
    </>
  );
}

export function QualityAccreditationCorrectiveActionRuntimePage() {
  const runtime = useCorrectiveActionRuntime();

  if (runtime.isPending) return <LoadingState title="Loading corrective action runtime" />;
  if (runtime.error) return PageError('Failed to load corrective action runtime.', runtime.error);
  if (!runtime.data) return <ErrorState message="Corrective action runtime is unavailable." />;

  return (
    <RequirePermission permission={QUALITY_ACCREDITATION_PERMISSIONS.summaryRead}>
      <ModuleShell
        title={QUALITY_ACCREDITATION_PAGE_TITLES.correctiveActions}
        description="Read-only corrective action runtime for remediation tracking, overdue monitoring, and gap closure readiness visibility."
        currentPath={QUALITY_ACCREDITATION_ROUTES.correctiveActions}
        boundaryPage="correctiveActions"
      >
        <section className="grid gap-6" data-testid="corrective-action-runtime">
          <section className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
            <QualityAccreditationMetricCard label="Actions" value={runtime.data.corrective_actions.length} helper="Read-only corrective actions inventory." />
            <QualityAccreditationMetricCard label="Readiness groups" value={runtime.data.readiness_summary.length} helper="Readiness summary groups." />
            <QualityAccreditationMetricCard label="Read-only" value={String(runtime.data.read_only)} helper="No write operations." />
            <QualityAccreditationMetricCard label="Aggregator-only" value={String(runtime.data.aggregator_only)} helper="Visibility-only runtime." />
          </section>
          <CorrectiveActionSummaryPanel summary={runtime.data.action_summary} />
          <CorrectiveActionRuntimeSummary data={runtime.data} />
          <CorrectiveActionTable items={runtime.data.corrective_actions} />
        </section>
      </ModuleShell>
    </RequirePermission>
  );
}

function ImprovementRoadmapPanel({ roadmaps }: { roadmaps: ImprovementRoadmap[] }) {
  return (
    <section className="rounded-lg border p-4" data-testid="improvement-roadmap-panel">
      <div className="space-y-1">
        <h2 className="text-lg font-semibold">Accreditation roadmaps</h2>
        <p className="text-sm text-muted-foreground">Roadmap coverage for strategic initiatives and completion readiness.</p>
      </div>
      <div className="mt-4 grid gap-3 md:grid-cols-2">
        {roadmaps.length === 0 ? (
          <p className="text-sm text-muted-foreground">No roadmap entries available.</p>
        ) : (
          roadmaps.map((item) => (
            <div key={item.roadmap_id} className="rounded-lg border p-3">
              <p className="font-medium">{item.roadmap_title}</p>
              <p className="text-sm text-muted-foreground">Cycle: {item.accreditation_cycle}</p>
              <p className="text-sm text-muted-foreground">Phase: {item.phase}</p>
              <p className="text-sm text-muted-foreground">Completion: {item.completion_percentage}</p>
            </div>
          ))
        )}
      </div>
    </section>
  );
}

function ImprovementMilestonesPanel({ initiatives }: { initiatives: ImprovementInitiative[] }) {
  const milestones: ImprovementMilestone[] = initiatives.flatMap((item) => item.milestones);
  return (
    <section className="rounded-lg border p-4" data-testid="improvement-milestones-panel">
      <div className="space-y-1">
        <h2 className="text-lg font-semibold">Improvement milestones</h2>
        <p className="text-sm text-muted-foreground">Milestone-level progress tracking for remediation execution.</p>
      </div>
      <div className="mt-4 grid gap-3 md:grid-cols-2">
        {milestones.length === 0 ? (
          <p className="text-sm text-muted-foreground">No milestones available.</p>
        ) : (
          milestones.map((item) => (
            <div key={item.milestone_id} className="rounded-lg border p-3">
              <p className="font-medium">{item.milestone_title}</p>
              <p className="text-sm text-muted-foreground">Due: {new Intl.DateTimeFormat('en-GB').format(new Date(item.due_date))}</p>
              <p className="text-sm text-muted-foreground">Status: {item.status}</p>
              <p className="text-sm text-muted-foreground">Completion: {item.completion_percentage}</p>
            </div>
          ))
        )}
      </div>
    </section>
  );
}

function ImprovementKpiTargetsPanel({ initiatives }: { initiatives: ImprovementInitiative[] }) {
  const targets: ImprovementKpiTarget[] = initiatives.flatMap((item) => item.kpi_targets);
  return (
    <section className="rounded-lg border p-4" data-testid="improvement-kpi-targets-panel">
      <div className="space-y-1">
        <h2 className="text-lg font-semibold">KPI targets</h2>
        <p className="text-sm text-muted-foreground">KPI baseline-to-target progression for accreditation improvement outcomes.</p>
      </div>
      <div className="mt-4 overflow-x-auto">
        <table className="min-w-full divide-y divide-border text-left text-sm">
          <thead>
            <tr className="text-xs uppercase tracking-wide text-muted-foreground">
              <th className="px-3 py-2">KPI</th>
              <th className="px-3 py-2">Baseline</th>
              <th className="px-3 py-2">Current</th>
              <th className="px-3 py-2">Target</th>
              <th className="px-3 py-2">Unit</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border">
            {targets.length === 0 ? (
              <tr>
                <td className="px-3 py-4 text-muted-foreground" colSpan={5}>No KPI targets available.</td>
              </tr>
            ) : (
              targets.map((item) => (
                <tr key={item.kpi_target_id}>
                  <td className="px-3 py-3">{item.kpi_name}</td>
                  <td className="px-3 py-3">{item.baseline_value}</td>
                  <td className="px-3 py-3">{item.current_value}</td>
                  <td className="px-3 py-3">{item.target_value}</td>
                  <td className="px-3 py-3">{item.unit}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </section>
  );
}

function ImprovementProgressPanel({ plans }: { plans: ImprovementPlanRuntime[] }) {
  return (
    <section className="rounded-lg border p-4" data-testid="improvement-progress-panel">
      <div className="space-y-1">
        <h2 className="text-lg font-semibold">Progress tracking</h2>
        <p className="text-sm text-muted-foreground">Operational status and completion posture for improvement plans and initiatives.</p>
      </div>
      <div className="mt-4 grid gap-3 md:grid-cols-2">
        {plans.map((plan) => (
          <div key={plan.plan_id} className="rounded-lg border p-3">
            <p className="font-medium">{plan.plan_title}</p>
            <p className="text-sm text-muted-foreground">Owner: {plan.owner_unit}</p>
            <p className="text-sm text-muted-foreground">Status: {plan.progress_tracking_status}</p>
            <p className="text-sm text-muted-foreground">Completion: {plan.completion_percentage}</p>
          </div>
        ))}
      </div>
    </section>
  );
}

function ImprovementForecastPanel({ forecasts }: { forecasts: ImprovementForecast[] }) {
  return (
    <section className="rounded-lg border p-4" data-testid="improvement-forecast-panel">
      <div className="space-y-1">
        <h2 className="text-lg font-semibold">Completion and readiness forecast</h2>
        <p className="text-sm text-muted-foreground">Forecast outlook for plan completion and accreditation readiness trajectory.</p>
      </div>
      <div className="mt-4 grid gap-3 md:grid-cols-2">
        {forecasts.length === 0 ? (
          <p className="text-sm text-muted-foreground">No forecast entries available.</p>
        ) : (
          forecasts.map((item) => (
            <div key={item.forecast_id} className="rounded-lg border p-3">
              <p className="font-medium">{item.forecast_type}</p>
              <p className="text-sm text-muted-foreground">Projected completion: {new Intl.DateTimeFormat('en-GB').format(new Date(item.projected_completion_date))}</p>
              <p className="text-sm text-muted-foreground">Readiness score: {item.readiness_forecast_score}</p>
              <p className="text-sm text-muted-foreground">Risk: {item.risk_level}</p>
              <p className="text-sm text-muted-foreground">Confidence: {item.confidence_level}</p>
            </div>
          ))
        )}
      </div>
    </section>
  );
}

export function QualityAccreditationImprovementPlanRuntimePage() {
  const runtime = useImprovementPlanRuntimeQuery();

  if (runtime.isPending) return <LoadingState title="Loading improvement plan runtime" />;
  if (runtime.error) return PageError('Failed to load improvement plan runtime.', runtime.error);
  if (!runtime.data) return <ErrorState message="Improvement plan runtime is unavailable." />;

  const plans = runtime.data.improvement_plans;
  const initiatives = plans.flatMap((item) => item.initiatives);
  const roadmaps = plans.flatMap((item) => item.roadmaps);
  const forecasts = plans.flatMap((item) => item.forecasts);

  return (
    <RequirePermission permission={QUALITY_ACCREDITATION_PERMISSIONS.summaryRead}>
      <ModuleShell
        title={QUALITY_ACCREDITATION_PAGE_TITLES.improvementPlanRuntime}
        description="Read-only improvement plan runtime with initiatives, milestones, KPI targets, progress tracking, and completion/readiness forecasts."
        currentPath={QUALITY_ACCREDITATION_ROUTES.improvementPlanRuntime}
        boundaryPage="improvementPlanRuntime"
      >
        <section className="grid gap-6" data-testid="improvement-plan-runtime">
          <ImprovementRoadmapPanel roadmaps={roadmaps} />
          <ImprovementMilestonesPanel initiatives={initiatives} />
          <ImprovementKpiTargetsPanel initiatives={initiatives} />
          <ImprovementProgressPanel plans={plans} />
          <ImprovementForecastPanel forecasts={forecasts} />
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