'use client';

import { useQuery } from '@tanstack/react-query';

import { reportingRuntimeApi } from './api';
import { PERMISSIONS } from '@/shared/config/permissions';
import { RequirePermission } from '@/shared/ui/permission-gate';
import { ErrorState, LoadingState } from '@/shared/ui/page-states';

function MetricCard({ label, value, helper }: { label: string; value: string | number; helper?: string }) {
  return (
    <div className="rounded-lg border p-4">
      <p className="text-sm text-muted-foreground">{label}</p>
      <p className="mt-2 text-2xl font-semibold">{value}</p>
      {helper ? <p className="mt-1 text-xs text-muted-foreground">{helper}</p> : null}
    </div>
  );
}

export function ReportingRuntimeShellPage() {
  const runtime = useQuery({
    queryKey: ['reporting-runtime:shell'],
    queryFn: reportingRuntimeApi.getRuntimeShell,
    staleTime: 30000,
  });
  const registry = useQuery({ queryKey: ['reporting-runtime:registry'], queryFn: reportingRuntimeApi.getRegistry, staleTime: 30000 });
  const templates = useQuery({ queryKey: ['reporting-runtime:templates'], queryFn: reportingRuntimeApi.getTemplates, staleTime: 30000 });
  const cycles = useQuery({ queryKey: ['reporting-runtime:cycles'], queryFn: reportingRuntimeApi.getCycles, staleTime: 30000 });
  const submissions = useQuery({ queryKey: ['reporting-runtime:submissions'], queryFn: reportingRuntimeApi.getSubmissions, staleTime: 30000 });
  const evidence = useQuery({ queryKey: ['reporting-runtime:evidence'], queryFn: reportingRuntimeApi.getEvidence, staleTime: 30000 });
  const providers = useQuery({ queryKey: ['reporting-runtime:providers'], queryFn: reportingRuntimeApi.getProviders, staleTime: 30000 });
  const ministry = useQuery({ queryKey: ['reporting-runtime:ministry'], queryFn: reportingRuntimeApi.getMinistry, staleTime: 30000 });
  const ministryCycles = useQuery({ queryKey: ['reporting-runtime:ministry:cycles'], queryFn: reportingRuntimeApi.getMinistryCycles, staleTime: 30000 });
  const ministryDeadlines = useQuery({ queryKey: ['reporting-runtime:ministry:deadlines'], queryFn: reportingRuntimeApi.getMinistryDeadlines, staleTime: 30000 });
  const ministryReadiness = useQuery({ queryKey: ['reporting-runtime:ministry:readiness'], queryFn: reportingRuntimeApi.getMinistryReadiness, staleTime: 30000 });
  const ministryCompleteness = useQuery({ queryKey: ['reporting-runtime:ministry:completeness'], queryFn: reportingRuntimeApi.getMinistryCompleteness, staleTime: 30000 });
  const ministryRisks = useQuery({ queryKey: ['reporting-runtime:ministry:risks'], queryFn: reportingRuntimeApi.getMinistryRisks, staleTime: 30000 });
  const accreditation = useQuery({ queryKey: ['reporting-runtime:accreditation'], queryFn: reportingRuntimeApi.getAccreditation, staleTime: 30000 });
  const accreditationCycles = useQuery({ queryKey: ['reporting-runtime:accreditation:cycles'], queryFn: reportingRuntimeApi.getAccreditationCycles, staleTime: 30000 });
  const accreditationReadiness = useQuery({ queryKey: ['reporting-runtime:accreditation:readiness'], queryFn: reportingRuntimeApi.getAccreditationReadiness, staleTime: 30000 });
  const accreditationCompliance = useQuery({ queryKey: ['reporting-runtime:accreditation:compliance'], queryFn: reportingRuntimeApi.getAccreditationCompliance, staleTime: 30000 });
  const accreditationDeadlines = useQuery({ queryKey: ['reporting-runtime:accreditation:deadlines'], queryFn: reportingRuntimeApi.getAccreditationDeadlines, staleTime: 30000 });
  const accreditationRisks = useQuery({ queryKey: ['reporting-runtime:accreditation:risks'], queryFn: reportingRuntimeApi.getAccreditationRisks, staleTime: 30000 });
  const regulatory = useQuery({ queryKey: ['reporting-runtime:regulatory'], queryFn: reportingRuntimeApi.getRegulatory, staleTime: 30000 });
  const regulatoryRequirements = useQuery({ queryKey: ['reporting-runtime:regulatory:requirements'], queryFn: reportingRuntimeApi.getRegulatoryRequirements, staleTime: 30000 });
  const regulatoryCompliance = useQuery({ queryKey: ['reporting-runtime:regulatory:compliance'], queryFn: reportingRuntimeApi.getRegulatoryCompliance, staleTime: 30000 });
  const regulatoryDeadlines = useQuery({ queryKey: ['reporting-runtime:regulatory:deadlines'], queryFn: reportingRuntimeApi.getRegulatoryDeadlines, staleTime: 30000 });
  const regulatoryDocuments = useQuery({ queryKey: ['reporting-runtime:regulatory:documents'], queryFn: reportingRuntimeApi.getRegulatoryDocuments, staleTime: 30000 });
  const regulatoryRisks = useQuery({ queryKey: ['reporting-runtime:regulatory:risks'], queryFn: reportingRuntimeApi.getRegulatoryRisks, staleTime: 30000 });
  const ranking = useQuery({ queryKey: ['reporting-runtime:ranking'], queryFn: reportingRuntimeApi.getRanking, staleTime: 30000 });
  const rankingIndicators = useQuery({ queryKey: ['reporting-runtime:ranking:indicators'], queryFn: reportingRuntimeApi.getRankingIndicators, staleTime: 30000 });
  const rankingReadiness = useQuery({ queryKey: ['reporting-runtime:ranking:readiness'], queryFn: reportingRuntimeApi.getRankingReadiness, staleTime: 30000 });
  const rankingBenchmarks = useQuery({ queryKey: ['reporting-runtime:ranking:benchmarks'], queryFn: reportingRuntimeApi.getRankingBenchmarks, staleTime: 30000 });
  const rankingTrends = useQuery({ queryKey: ['reporting-runtime:ranking:trends'], queryFn: reportingRuntimeApi.getRankingTrends, staleTime: 30000 });
  const rankingRisks = useQuery({ queryKey: ['reporting-runtime:ranking:risks'], queryFn: reportingRuntimeApi.getRankingRisks, staleTime: 30000 });
  const nobd = useQuery({ queryKey: ['reporting-runtime:nobd'], queryFn: reportingRuntimeApi.getNobd, staleTime: 30000 });
  const nobdDatasets = useQuery({ queryKey: ['reporting-runtime:nobd:datasets'], queryFn: reportingRuntimeApi.getNobdDatasets, staleTime: 30000 });
  const nobdCompleteness = useQuery({ queryKey: ['reporting-runtime:nobd:completeness'], queryFn: reportingRuntimeApi.getNobdCompleteness, staleTime: 30000 });
  const nobdQuality = useQuery({ queryKey: ['reporting-runtime:nobd:quality'], queryFn: reportingRuntimeApi.getNobdQuality, staleTime: 30000 });
  const nobdSyncStatus = useQuery({ queryKey: ['reporting-runtime:nobd:sync-status'], queryFn: reportingRuntimeApi.getNobdSyncStatus, staleTime: 30000 });
  const nobdRisks = useQuery({ queryKey: ['reporting-runtime:nobd:risks'], queryFn: reportingRuntimeApi.getNobdRisks, staleTime: 30000 });
  const compliance = useQuery({ queryKey: ['reporting-runtime:compliance'], queryFn: reportingRuntimeApi.getCompliance, staleTime: 30000 });
  const complianceControls = useQuery({ queryKey: ['reporting-runtime:compliance:controls'], queryFn: reportingRuntimeApi.getComplianceControls, staleTime: 30000 });
  const complianceReadiness = useQuery({ queryKey: ['reporting-runtime:compliance:readiness'], queryFn: reportingRuntimeApi.getComplianceReadiness, staleTime: 30000 });
  const complianceGaps = useQuery({ queryKey: ['reporting-runtime:compliance:gaps'], queryFn: reportingRuntimeApi.getComplianceGaps, staleTime: 30000 });
  const complianceRisks = useQuery({ queryKey: ['reporting-runtime:compliance:risks'], queryFn: reportingRuntimeApi.getComplianceRisks, staleTime: 30000 });

  if (
    runtime.isPending ||
    registry.isPending ||
    templates.isPending ||
    cycles.isPending ||
    submissions.isPending ||
    evidence.isPending ||
    providers.isPending ||
    ministry.isPending ||
    ministryCycles.isPending ||
    ministryDeadlines.isPending ||
    ministryReadiness.isPending ||
    ministryCompleteness.isPending ||
    ministryRisks.isPending ||
    accreditation.isPending ||
    accreditationCycles.isPending ||
    accreditationReadiness.isPending ||
    accreditationCompliance.isPending ||
    accreditationDeadlines.isPending ||
    accreditationRisks.isPending ||
    regulatory.isPending ||
    regulatoryRequirements.isPending ||
    regulatoryCompliance.isPending ||
    regulatoryDeadlines.isPending ||
    regulatoryDocuments.isPending ||
    regulatoryRisks.isPending ||
    ranking.isPending ||
    rankingIndicators.isPending ||
    rankingReadiness.isPending ||
    rankingBenchmarks.isPending ||
    rankingTrends.isPending ||
    rankingRisks.isPending ||
    nobd.isPending ||
    nobdDatasets.isPending ||
    nobdCompleteness.isPending ||
    nobdQuality.isPending ||
    nobdSyncStatus.isPending ||
    nobdRisks.isPending ||
    compliance.isPending ||
    complianceControls.isPending ||
    complianceReadiness.isPending ||
    complianceGaps.isPending ||
    complianceRisks.isPending
  ) {
    return <LoadingState title="Loading Reporting Runtime shell" />;
  }

  if (
    runtime.error ||
    registry.error ||
    templates.error ||
    cycles.error ||
    submissions.error ||
    evidence.error ||
    providers.error ||
    ministry.error ||
    ministryCycles.error ||
    ministryDeadlines.error ||
    ministryReadiness.error ||
    ministryCompleteness.error ||
    ministryRisks.error ||
    accreditation.error ||
    accreditationCycles.error ||
    accreditationReadiness.error ||
    accreditationCompliance.error ||
    accreditationDeadlines.error ||
    accreditationRisks.error ||
    regulatory.error ||
    regulatoryRequirements.error ||
    regulatoryCompliance.error ||
    regulatoryDeadlines.error ||
    regulatoryDocuments.error ||
    regulatoryRisks.error ||
    ranking.error ||
    rankingIndicators.error ||
    rankingReadiness.error ||
    rankingBenchmarks.error ||
    rankingTrends.error ||
    rankingRisks.error ||
    nobd.error ||
    nobdDatasets.error ||
    nobdCompleteness.error ||
    nobdQuality.error ||
    nobdSyncStatus.error ||
    nobdRisks.error ||
    compliance.error ||
    complianceControls.error ||
    complianceReadiness.error ||
    complianceGaps.error ||
    complianceRisks.error
  ) {
    return (
      <ErrorState
        message="Failed to load Reporting Runtime shell."
        error={
          runtime.error ??
          registry.error ??
          templates.error ??
          cycles.error ??
          submissions.error ??
          evidence.error ??
          providers.error ??
          ministry.error ??
          ministryCycles.error ??
          ministryDeadlines.error ??
          ministryReadiness.error ??
          ministryCompleteness.error ??
          ministryRisks.error ??
          accreditation.error ??
          accreditationCycles.error ??
          accreditationReadiness.error ??
          accreditationCompliance.error ??
          accreditationDeadlines.error ??
          accreditationRisks.error ??
          regulatory.error ??
          regulatoryRequirements.error ??
          regulatoryCompliance.error ??
          regulatoryDeadlines.error ??
          regulatoryDocuments.error ??
          regulatoryRisks.error ??
          ranking.error ??
          rankingIndicators.error ??
          rankingReadiness.error ??
          rankingBenchmarks.error ??
          rankingTrends.error ??
          rankingRisks.error ??
          nobd.error ??
          nobdDatasets.error ??
          nobdCompleteness.error ??
          nobdQuality.error ??
          nobdSyncStatus.error ??
          nobdRisks.error ??
          compliance.error ??
          complianceControls.error ??
          complianceReadiness.error ??
          complianceGaps.error ??
          complianceRisks.error
        }
      />
    );
  }

  if (
    !runtime.data ||
    !registry.data ||
    !templates.data ||
    !cycles.data ||
    !submissions.data ||
    !evidence.data ||
    !providers.data ||
    !ministry.data ||
    !ministryCycles.data ||
    !ministryDeadlines.data ||
    !ministryReadiness.data ||
    !ministryCompleteness.data ||
    !ministryRisks.data ||
    !accreditation.data ||
    !accreditationCycles.data ||
    !accreditationReadiness.data ||
    !accreditationCompliance.data ||
    !accreditationDeadlines.data ||
    !accreditationRisks.data ||
    !regulatory.data ||
    !regulatoryRequirements.data ||
    !regulatoryCompliance.data ||
    !regulatoryDeadlines.data ||
    !regulatoryDocuments.data ||
    !regulatoryRisks.data ||
    !ranking.data ||
    !rankingIndicators.data ||
    !rankingReadiness.data ||
    !rankingBenchmarks.data ||
    !rankingTrends.data ||
    !rankingRisks.data ||
    !nobd.data ||
    !nobdDatasets.data ||
    !nobdCompleteness.data ||
    !nobdQuality.data ||
    !nobdSyncStatus.data ||
    !nobdRisks.data ||
    !compliance.data ||
    !complianceControls.data ||
    !complianceReadiness.data ||
    !complianceGaps.data ||
    !complianceRisks.data
  ) {
    return <ErrorState message="Reporting Runtime shell is unavailable." />;
  }

  return (
    <RequirePermission permission={PERMISSIONS.REPORTING_RUNTIME_SUMMARY_READ}>
      <div className="space-y-6" data-testid="reporting-runtime-shell">
        <header className="space-y-2">
          <h1 className="text-2xl font-semibold">Reporting Runtime Shell</h1>
          <p className="text-sm text-muted-foreground">
            Read-only runtime shell for Ministry and Regulatory Reporting Brain. No provider synchronization and no submission execution.
          </p>
        </header>

        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          <MetricCard label="Reporting Cycles" value={runtime.data.active_reporting_cycles} helper="Reporting lifecycle overview" />
          <MetricCard label="Active Submissions" value={runtime.data.active_submissions} helper="Read-only submission state" />
          <MetricCard label="Active Deadlines" value={runtime.data.active_deadlines} helper="Deadline monitoring" />
          <MetricCard label="Compliance Score" value={runtime.data.compliance_score} helper={`Risk band: ${runtime.data.compliance.risk_band}`} />
        </div>

        <section className="rounded-lg border p-4" data-testid="reporting-overview-section">
          <h2 className="text-lg font-semibold">Reporting Overview</h2>
          <p className="mt-1 text-sm text-muted-foreground">
            {runtime.data.overview.reporting_center_name} owned by {runtime.data.overview.owner_module}
          </p>
        </section>

        <section className="rounded-lg border p-4" data-testid="provider-readiness-section">
          <h2 className="text-lg font-semibold">Provider Readiness</h2>
          <p className="mt-1 text-sm text-muted-foreground">
            Owner: {runtime.data.provider_readiness.owner_module} | Status: {runtime.data.provider_readiness.provider_readiness}
          </p>
          <p className="mt-1 text-sm">
            NOT_CONNECTED={runtime.data.provider_readiness.provider_status_counts.NOT_CONNECTED ?? 0}, READY={runtime.data.provider_readiness.provider_status_counts.READY ?? 0}, PENDING={runtime.data.provider_readiness.provider_status_counts.PENDING ?? 0}
          </p>
        </section>

        <section className="rounded-lg border p-4" data-testid="compliance-summary-section">
          <h2 className="text-lg font-semibold">Compliance Summary</h2>
          <p className="mt-1 text-sm text-muted-foreground">Risk band: {runtime.data.compliance.risk_band}</p>
          <p className="mt-1 text-sm">Compliance score: {runtime.data.compliance.compliance_score}</p>
        </section>

        <section className="rounded-lg border p-4" data-testid="reporting-deadlines-section">
          <h2 className="text-lg font-semibold">Reporting Deadlines</h2>
          <p className="mt-1 text-sm">Overdue: {runtime.data.deadlines.overdue_deadlines} | Upcoming: {runtime.data.deadlines.upcoming_deadlines}</p>
        </section>

        <section className="rounded-lg border p-4" data-testid="reporting-status-section">
          <h2 className="text-lg font-semibold">Reporting Status</h2>
          <p className="mt-1 text-sm">Open: {runtime.data.reporting_status.open_items}</p>
          <p className="text-sm">In review: {runtime.data.reporting_status.in_review_items}</p>
          <p className="text-sm">Blocked: {runtime.data.reporting_status.blocked_items}</p>
          <p className="mt-2 text-xs text-muted-foreground">
            read_only={String(runtime.data.read_only)} | auditability_preserved={String(runtime.data.auditability_preserved)}
          </p>
        </section>

        <section className="rounded-lg border p-4" data-testid="reporting-registry-section">
          <h2 className="text-lg font-semibold">Reporting Registry</h2>
          <div className="mt-3 grid gap-2 md:grid-cols-2">
            {registry.data.entries.map((entry) => (
              <div key={entry.id} className="rounded border p-3 text-sm">
                <p className="font-medium">{entry.report_type}</p>
                <p>{entry.report_name}</p>
                <p className="text-xs text-muted-foreground">owner={entry.owner_module} | period={entry.reporting_period}</p>
              </div>
            ))}
          </div>
        </section>

        <section className="rounded-lg border p-4" data-testid="reporting-templates-section">
          <h2 className="text-lg font-semibold">Reporting Templates</h2>
          <div className="mt-3 space-y-1 text-sm">
            {templates.data.templates.map((item) => (
              <p key={item.id}>{item.report_code}: {item.template_version} ({item.section_count} sections)</p>
            ))}
          </div>
        </section>

        <section className="rounded-lg border p-4" data-testid="reporting-cycles-section">
          <h2 className="text-lg font-semibold">Reporting Cycles</h2>
          <div className="mt-3 space-y-1 text-sm">
            {cycles.data.cycles.map((item) => (
              <p key={item.id}>{item.report_code}: {item.cycle_stage} ({item.active_days_remaining} days remaining)</p>
            ))}
          </div>
        </section>

        <section className="rounded-lg border p-4" data-testid="reporting-submissions-section">
          <h2 className="text-lg font-semibold">Reporting Submissions</h2>
          <div className="mt-3 space-y-1 text-sm">
            {submissions.data.submissions.map((item) => (
              <p key={item.id}>{item.submission_id}: {item.submission_status}</p>
            ))}
          </div>
        </section>

        <section className="rounded-lg border p-4" data-testid="reporting-evidence-section">
          <h2 className="text-lg font-semibold">Reporting Evidence</h2>
          <div className="mt-3 space-y-1 text-sm">
            {evidence.data.evidence.map((item) => (
              <p key={item.id}>{item.report_code}: evidence={item.evidence_count}, completeness={item.evidence_completeness}%</p>
            ))}
          </div>
        </section>

        <section className="rounded-lg border p-4" data-testid="provider-registry-section">
          <h2 className="text-lg font-semibold">Provider Registry</h2>
          <div className="mt-3 space-y-1 text-sm">
            {providers.data.providers.map((item) => (
              <p key={item.id}>{item.provider_key}: provider_status={item.provider_status}, live_integrations_enabled={String(item.live_integrations_enabled)}</p>
            ))}
          </div>
        </section>

        <section className="rounded-lg border p-4" data-testid="ministry-reporting-center-section">
          <h2 className="text-lg font-semibold">Ministry Reporting Center</h2>
          <p className="mt-1 text-sm text-muted-foreground">
            Read-only runtime visibility for canonical Ministry reporting workflows. No submissions are executed and no external synchronization is enabled.
          </p>
          <div className="mt-3 grid gap-2 md:grid-cols-2">
            {ministry.data.reports.map((item) => (
              <div key={item.id} className="rounded border p-3 text-sm">
                <p className="font-medium">{item.report_name}</p>
                <p>{item.report_code} | owner={item.owner_module}</p>
                <p className="text-xs text-muted-foreground">period={item.reporting_period} | readiness={item.readiness_status} | risk={item.risk_level}</p>
              </div>
            ))}
          </div>
        </section>

        <section className="rounded-lg border p-4" data-testid="ministry-reporting-cycles-section">
          <h2 className="text-lg font-semibold">Reporting Cycles</h2>
          <div className="mt-3 space-y-1 text-sm">
            {ministryCycles.data.cycles.map((item) => (
              <p key={item.id}>{item.report_name}: cycle={item.cycle_status}, days_remaining={item.days_remaining}</p>
            ))}
          </div>
        </section>

        <section className="rounded-lg border p-4" data-testid="ministry-reporting-deadlines-section">
          <h2 className="text-lg font-semibold">Reporting Deadlines</h2>
          <div className="mt-3 space-y-1 text-sm">
            {ministryDeadlines.data.deadlines.map((item) => (
              <p key={item.id}>{item.report_name}: deadline_status={item.deadline_status}, days_remaining={item.days_remaining}</p>
            ))}
          </div>
        </section>

        <section className="rounded-lg border p-4" data-testid="ministry-reporting-readiness-section">
          <h2 className="text-lg font-semibold">Reporting Readiness</h2>
          <div className="mt-3 space-y-1 text-sm">
            {ministryReadiness.data.readiness.map((item) => (
              <p key={item.id}>{item.report_name}: readiness_score={item.readiness_score}, status={item.readiness_status}</p>
            ))}
          </div>
        </section>

        <section className="rounded-lg border p-4" data-testid="ministry-reporting-completeness-section">
          <h2 className="text-lg font-semibold">Reporting Completeness</h2>
          <div className="mt-3 space-y-1 text-sm">
            {ministryCompleteness.data.completeness.map((item) => (
              <p key={item.id}>{item.report_name}: completion={item.completion_percentage}% ({item.completed_data_points}/{item.required_data_points})</p>
            ))}
          </div>
        </section>

        <section className="rounded-lg border p-4" data-testid="ministry-reporting-risks-section">
          <h2 className="text-lg font-semibold">Reporting Risks</h2>
          <div className="mt-3 space-y-1 text-sm">
            {ministryRisks.data.risks.map((item) => (
              <p key={item.id}>{item.report_name}: signal={item.signal_name}, owner={item.signal_owner_module}, risk={item.risk_level}</p>
            ))}
          </div>
        </section>

        <section className="rounded-lg border p-4" data-testid="accreditation-reporting-center-section">
          <h2 className="text-lg font-semibold">Accreditation Reporting Center</h2>
          <p className="mt-1 text-sm text-muted-foreground">
            Read-only accreditation monitoring for institutional and quality assurance reporting domains. No agency submission execution and no provider synchronization.
          </p>
          <div className="mt-3 grid gap-2 md:grid-cols-2">
            {accreditation.data.reports.map((item) => (
              <div key={item.id} className="rounded border p-3 text-sm">
                <p className="font-medium">{item.accreditation_name}</p>
                <p>{item.accreditation_code} | agency={item.agency_name}</p>
                <p className="text-xs text-muted-foreground">type={item.accreditation_type} | evidence={item.evidence_readiness} | risk={item.risk_level}</p>
              </div>
            ))}
          </div>
        </section>

        <section className="rounded-lg border p-4" data-testid="accreditation-cycles-section">
          <h2 className="text-lg font-semibold">Accreditation Cycles</h2>
          <div className="mt-3 space-y-1 text-sm">
            {accreditationCycles.data.cycles.map((item) => (
              <p key={item.id}>{item.accreditation_name}: cycle={item.cycle_status}, days_remaining={item.days_remaining}</p>
            ))}
          </div>
        </section>

        <section className="rounded-lg border p-4" data-testid="accreditation-readiness-section">
          <h2 className="text-lg font-semibold">Evidence Readiness</h2>
          <div className="mt-3 space-y-1 text-sm">
            {accreditationReadiness.data.readiness.map((item) => (
              <p key={item.id}>{item.accreditation_name}: readiness_score={item.readiness_score}, evidence={item.evidence_readiness}</p>
            ))}
          </div>
        </section>

        <section className="rounded-lg border p-4" data-testid="accreditation-compliance-section">
          <h2 className="text-lg font-semibold">Compliance Status</h2>
          <div className="mt-3 space-y-1 text-sm">
            {accreditationCompliance.data.compliance.map((item) => (
              <p key={item.id}>{item.accreditation_name}: compliance_score={item.compliance_score}, status={item.compliance_status}</p>
            ))}
          </div>
        </section>

        <section className="rounded-lg border p-4" data-testid="accreditation-deadlines-section">
          <h2 className="text-lg font-semibold">Accreditation Deadlines</h2>
          <div className="mt-3 space-y-1 text-sm">
            {accreditationDeadlines.data.deadlines.map((item) => (
              <p key={item.id}>{item.accreditation_name}: deadline_status={item.deadline_status}, days_remaining={item.days_remaining}</p>
            ))}
          </div>
        </section>

        <section className="rounded-lg border p-4" data-testid="accreditation-risks-section">
          <h2 className="text-lg font-semibold">Accreditation Risks</h2>
          <div className="mt-3 space-y-1 text-sm">
            {accreditationRisks.data.risks.map((item) => (
              <p key={item.id}>{item.accreditation_name}: signal={item.signal_name}, owner={item.signal_owner_module}, risk={item.risk_level}</p>
            ))}
          </div>
        </section>

        <section className="rounded-lg border p-4" data-testid="regulatory-reporting-center-section">
          <h2 className="text-lg font-semibold">Regulatory Reporting Center</h2>
          <p className="mt-1 text-sm text-muted-foreground">
            Runtime monitoring only for regulatory obligations. No regulatory submission execution, no external regulator integrations, and no provider synchronization.
          </p>
          <div className="mt-3 grid gap-2 md:grid-cols-2">
            {regulatory.data.reports.map((item) => (
              <div key={item.id} className="rounded border p-3 text-sm">
                <p className="font-medium">{item.requirement_name}</p>
                <p>{item.requirement_code} | regulator={item.regulator_name}</p>
                <p className="text-xs text-muted-foreground">compliance={item.compliance_status} | documents={item.document_status} | risk={item.risk_level}</p>
              </div>
            ))}
          </div>
        </section>

        <section className="rounded-lg border p-4" data-testid="regulatory-requirements-section">
          <h2 className="text-lg font-semibold">Regulatory Requirements</h2>
          <div className="mt-3 space-y-1 text-sm">
            {regulatoryRequirements.data.requirements.map((item) => (
              <p key={item.id}>{item.requirement_name}: status={item.requirement_status}, compliance={item.compliance_status}</p>
            ))}
          </div>
        </section>

        <section className="rounded-lg border p-4" data-testid="regulatory-compliance-section">
          <h2 className="text-lg font-semibold">Compliance Status</h2>
          <div className="mt-3 space-y-1 text-sm">
            {regulatoryCompliance.data.compliance.map((item) => (
              <p key={item.id}>{item.requirement_name}: compliance_score={item.compliance_score}, status={item.compliance_status}</p>
            ))}
          </div>
        </section>

        <section className="rounded-lg border p-4" data-testid="regulatory-deadlines-section">
          <h2 className="text-lg font-semibold">Regulatory Deadlines</h2>
          <div className="mt-3 space-y-1 text-sm">
            {regulatoryDeadlines.data.deadlines.map((item) => (
              <p key={item.id}>{item.requirement_name}: deadline_status={item.deadline_status}, days_remaining={item.days_remaining}</p>
            ))}
          </div>
        </section>

        <section className="rounded-lg border p-4" data-testid="regulatory-documents-section">
          <h2 className="text-lg font-semibold">Document Readiness</h2>
          <div className="mt-3 space-y-1 text-sm">
            {regulatoryDocuments.data.documents.map((item) => (
              <p key={item.id}>{item.requirement_name}: document={item.document_name}, completeness={item.document_completeness}%, status={item.document_status}</p>
            ))}
          </div>
        </section>

        <section className="rounded-lg border p-4" data-testid="regulatory-risks-section">
          <h2 className="text-lg font-semibold">Regulatory Risks</h2>
          <div className="mt-3 space-y-1 text-sm">
            {regulatoryRisks.data.risks.map((item) => (
              <p key={item.id}>{item.requirement_name}: signal={item.signal_name}, owner={item.signal_owner_module}, risk={item.risk_level}</p>
            ))}
          </div>
        </section>

        <section className="rounded-lg border p-4" data-testid="ranking-reporting-center-section">
          <h2 className="text-lg font-semibold">Ranking Reporting Center</h2>
          <p className="mt-1 text-sm text-muted-foreground">
            Read-only runtime monitoring for QS and THE ranking analytics visibility. No live QS integration, no live THE integration, and no ranking submission execution.
          </p>
          <div className="mt-3 grid gap-2 md:grid-cols-2">
            {ranking.data.reports.map((item) => (
              <div key={item.id} className="rounded border p-3 text-sm">
                <p className="font-medium">{item.indicator_name}</p>
                <p>{item.ranking_system} | owner={item.owner_module}</p>
                <p className="text-xs text-muted-foreground">score={item.indicator_score} | benchmark={item.benchmark_score} | trend={item.trend_direction} | risk={item.risk_level}</p>
              </div>
            ))}
          </div>
        </section>

        <section className="rounded-lg border p-4" data-testid="ranking-qs-readiness-section">
          <h2 className="text-lg font-semibold">QS Readiness</h2>
          <div className="mt-3 space-y-1 text-sm">
            {rankingReadiness.data.readiness
              .filter((item) => item.ranking_system === 'QS')
              .map((item) => (
                <p key={item.id}>{item.indicator_name}: readiness_score={item.readiness_score}, readiness_level={item.readiness_level}</p>
              ))}
          </div>
        </section>

        <section className="rounded-lg border p-4" data-testid="ranking-the-readiness-section">
          <h2 className="text-lg font-semibold">THE Readiness</h2>
          <div className="mt-3 space-y-1 text-sm">
            {rankingReadiness.data.readiness
              .filter((item) => item.ranking_system === 'THE')
              .map((item) => (
                <p key={item.id}>{item.indicator_name}: readiness_score={item.readiness_score}, readiness_level={item.readiness_level}</p>
              ))}
          </div>
        </section>

        <section className="rounded-lg border p-4" data-testid="ranking-benchmarks-section">
          <h2 className="text-lg font-semibold">Ranking Benchmarks</h2>
          <div className="mt-3 space-y-1 text-sm">
            {rankingBenchmarks.data.benchmarks.map((item) => (
              <p key={item.id}>{item.ranking_system} {item.indicator_name}: indicator={item.indicator_score}, benchmark={item.benchmark_score}, gap={item.benchmark_gap}</p>
            ))}
          </div>
        </section>

        <section className="rounded-lg border p-4" data-testid="ranking-trends-section">
          <h2 className="text-lg font-semibold">Ranking Trends</h2>
          <div className="mt-3 space-y-1 text-sm">
            {rankingTrends.data.trends.map((item) => (
              <p key={item.id}>{item.ranking_system} {item.indicator_name}: trend_direction={item.trend_direction}, trend_delta={item.trend_delta}</p>
            ))}
          </div>
        </section>

        <section className="rounded-lg border p-4" data-testid="ranking-risks-section">
          <h2 className="text-lg font-semibold">Ranking Risks</h2>
          <div className="mt-3 space-y-1 text-sm">
            {rankingRisks.data.risks.map((item) => (
              <p key={item.id}>{item.ranking_system} {item.indicator_name}: signal={item.signal_name}, owner={item.signal_owner_module}, risk={item.risk_level}</p>
            ))}
          </div>
        </section>

        <section className="rounded-lg border p-4" data-testid="nobd-reporting-center-section">
          <h2 className="text-lg font-semibold">NOBD Reporting Center</h2>
          <p className="mt-1 text-sm text-muted-foreground">
            Read-only runtime monitoring for NOBD visibility, readiness, and risk posture. No NOBD synchronization execution, no write operations, and no external API calls.
          </p>
          <div className="mt-3 grid gap-2 md:grid-cols-2">
            {nobd.data.reports.map((item) => (
              <div key={item.id} className="rounded border p-3 text-sm">
                <p className="font-medium">{item.dataset_name}</p>
                <p>{item.dataset_code} | owner={item.owner_module}</p>
                <p className="text-xs text-muted-foreground">records={item.records_complete}/{item.records_total} | completeness={item.completeness_percentage}% | quality={item.quality_score} | sync={item.sync_status}</p>
              </div>
            ))}
          </div>
        </section>

        <section className="rounded-lg border p-4" data-testid="nobd-dataset-coverage-section">
          <h2 className="text-lg font-semibold">Dataset Coverage</h2>
          <div className="mt-3 space-y-1 text-sm">
            {nobdDatasets.data.datasets.map((item) => (
              <p key={item.id}>{item.dataset_name}: code={item.dataset_code}, priority={item.dataset_priority}, owner={item.owner_module}</p>
            ))}
          </div>
        </section>

        <section className="rounded-lg border p-4" data-testid="nobd-completeness-monitoring-section">
          <h2 className="text-lg font-semibold">Completeness Monitoring</h2>
          <div className="mt-3 space-y-1 text-sm">
            {nobdCompleteness.data.completeness.map((item) => (
              <p key={item.id}>{item.dataset_name}: completeness={item.completeness_percentage}% (gap={item.completeness_gap})</p>
            ))}
          </div>
        </section>

        <section className="rounded-lg border p-4" data-testid="nobd-quality-monitoring-section">
          <h2 className="text-lg font-semibold">Data Quality Monitoring</h2>
          <div className="mt-3 space-y-1 text-sm">
            {nobdQuality.data.quality.map((item) => (
              <p key={item.id}>{item.dataset_name}: quality_score={item.quality_score}, quality_band={item.quality_band}</p>
            ))}
          </div>
        </section>

        <section className="rounded-lg border p-4" data-testid="nobd-sync-status-section">
          <h2 className="text-lg font-semibold">Sync Status</h2>
          <div className="mt-3 space-y-1 text-sm">
            {nobdSyncStatus.data.sync_status.map((item) => (
              <p key={item.id}>{item.dataset_name}: sync_status={item.sync_status}, lag_hours={item.sync_lag_hours}</p>
            ))}
          </div>
        </section>

        <section className="rounded-lg border p-4" data-testid="nobd-risks-section">
          <h2 className="text-lg font-semibold">NOBD Risks</h2>
          <div className="mt-3 space-y-1 text-sm">
            {nobdRisks.data.risks.map((item) => (
              <p key={item.id}>{item.dataset_name}: signal={item.signal_name}, owner={item.signal_owner_module}, risk={item.risk_level}</p>
            ))}
          </div>
        </section>

        <section className="rounded-lg border p-4" data-testid="compliance-monitoring-center-section">
          <h2 className="text-lg font-semibold">Compliance Monitoring Center</h2>
          <p className="mt-1 text-sm text-muted-foreground">
            Runtime monitoring only for Ministry and Regulatory compliance posture. No compliance workflow execution, no corrective action execution, no external submissions, and no provider calls.
          </p>
          <div className="mt-3 grid gap-2 md:grid-cols-2">
            {compliance.data.reports.map((item) => (
              <div key={item.id} className="rounded border p-3 text-sm">
                <p className="font-medium">{item.control_name}</p>
                <p>{item.control_code} | owner={item.owner_module}</p>
                <p className="text-xs text-muted-foreground">status={item.compliance_status} | readiness={item.readiness_score} | gaps={item.gap_count} | risk={item.risk_level}</p>
              </div>
            ))}
          </div>
        </section>

        <section className="rounded-lg border p-4" data-testid="compliance-controls-section">
          <h2 className="text-lg font-semibold">Compliance Controls</h2>
          <div className="mt-3 space-y-1 text-sm">
            {complianceControls.data.controls.map((item) => (
              <p key={item.id}>{item.control_name}: type={item.control_type}, status={item.compliance_status}, gaps={item.gap_count}</p>
            ))}
          </div>
        </section>

        <section className="rounded-lg border p-4" data-testid="compliance-readiness-section">
          <h2 className="text-lg font-semibold">Readiness Monitoring</h2>
          <div className="mt-3 space-y-1 text-sm">
            {complianceReadiness.data.readiness.map((item) => (
              <p key={item.id}>{item.control_name}: readiness_level={item.readiness_level}, readiness_score={item.readiness_score}</p>
            ))}
          </div>
        </section>

        <section className="rounded-lg border p-4" data-testid="compliance-risks-section">
          <h2 className="text-lg font-semibold">Compliance Risks</h2>
          <div className="mt-3 space-y-1 text-sm">
            {complianceRisks.data.risks.map((item) => (
              <p key={item.id}>{item.control_name}: signal={item.signal_name}, owner={item.signal_owner_module}, risk={item.risk_level}</p>
            ))}
          </div>
        </section>

        <section className="rounded-lg border p-4" data-testid="compliance-gaps-section">
          <h2 className="text-lg font-semibold">Compliance Gaps</h2>
          <div className="mt-3 space-y-1 text-sm">
            {complianceGaps.data.gaps.map((item) => (
              <p key={item.id}>{item.control_name}: gap_count={item.gap_count}, gap_severity={item.gap_severity}</p>
            ))}
          </div>
        </section>
      </div>
    </RequirePermission>
  );
}
