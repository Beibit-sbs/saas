import React from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, screen } from '@testing-library/react';
import { within } from '@testing-library/dom';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const { mockApi } = vi.hoisted(() => ({
  mockApi: {
    getRuntimeShell: vi.fn(),
    getRegistry: vi.fn(),
    getTemplates: vi.fn(),
    getCycles: vi.fn(),
    getSubmissions: vi.fn(),
    getEvidence: vi.fn(),
    getProviders: vi.fn(),
    getMinistry: vi.fn(),
    getMinistryCycles: vi.fn(),
    getMinistryDeadlines: vi.fn(),
    getMinistryReadiness: vi.fn(),
    getMinistryCompleteness: vi.fn(),
    getMinistryRisks: vi.fn(),
    getAccreditation: vi.fn(),
    getAccreditationCycles: vi.fn(),
    getAccreditationReadiness: vi.fn(),
    getAccreditationCompliance: vi.fn(),
    getAccreditationDeadlines: vi.fn(),
    getAccreditationRisks: vi.fn(),
    getRegulatory: vi.fn(),
    getRegulatoryRequirements: vi.fn(),
    getRegulatoryCompliance: vi.fn(),
    getRegulatoryDeadlines: vi.fn(),
    getRegulatoryDocuments: vi.fn(),
    getRegulatoryRisks: vi.fn(),
    getRanking: vi.fn(),
    getRankingIndicators: vi.fn(),
    getRankingReadiness: vi.fn(),
    getRankingBenchmarks: vi.fn(),
    getRankingTrends: vi.fn(),
    getRankingRisks: vi.fn(),
    getNobd: vi.fn(),
    getNobdDatasets: vi.fn(),
    getNobdCompleteness: vi.fn(),
    getNobdQuality: vi.fn(),
    getNobdSyncStatus: vi.fn(),
    getNobdRisks: vi.fn(),
    getCompliance: vi.fn(),
    getComplianceControls: vi.fn(),
    getComplianceReadiness: vi.fn(),
    getComplianceGaps: vi.fn(),
    getComplianceRisks: vi.fn(),
  },
}));

vi.mock('@/modules/reporting-runtime/api', () => ({ reportingRuntimeApi: mockApi }));
vi.mock('@/shared/ui/permission-gate', () => ({ RequirePermission: ({ children }: { children: React.ReactNode }) => <>{children}</> }));

import { ReportingRuntimeShellPage } from '@/modules/reporting-runtime/page';

function renderWithClient(ui: React.ReactNode) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(<QueryClientProvider client={client}>{ui}</QueryClientProvider>);
}

describe('Ranking Reporting Runtime', () => {
  beforeEach(() => {
    mockApi.getRuntimeShell.mockResolvedValue({
      tenant_id: 1,
      reporting_center_name: 'Reporting Brain Runtime Shell',
      active_reporting_cycles: 5,
      active_submissions: 7,
      active_deadlines: 8,
      provider_readiness: {
        owner_module: 'regulatory_reporting_integration',
        provider_status_counts: { NOT_CONNECTED: 1, READY: 3, PENDING: 1 },
        provider_readiness: 'NON_LIVE_PROFILE_ONLY',
        blocker_count: 2,
        warning_count: 1,
        live_integrations_enabled: false,
        sync_enabled: false,
        submission_execution_enabled: false,
        source_modules: ['regulatory_reporting_integration', 'provider_readiness'],
        read_only: true,
      },
      compliance_score: 80,
      generated_at: '2026-06-10T00:00:00Z',
      read_only: true,
      auditability_preserved: true,
      overview: {
        reporting_center_name: 'Reporting Brain Runtime Shell',
        owner_module: 'reporting_runtime',
        active_reporting_cycles: 5,
        active_submissions: 7,
        active_deadlines: 8,
        source_modules: ['reporting_runtime', 'analytics', 'executive_governance'],
        read_only: true,
      },
      compliance: {
        owner_module: 'reporting_runtime',
        compliance_score: 80,
        risk_band: 'MEDIUM',
        source_modules: ['reporting_runtime', 'brain_core', 'executive_governance'],
        read_only: true,
      },
      deadlines: {
        owner_module: 'reporting_runtime',
        active_deadlines: 8,
        overdue_deadlines: 2,
        upcoming_deadlines: 6,
        deadline_signals: ['report_overdue', 'ministry_deadline_risk', 'submission_risk'],
        source_modules: ['reporting_runtime', 'brain_core', 'executive_governance'],
        read_only: true,
      },
      reporting_status: {
        open_items: 3,
        in_review_items: 2,
        blocked_items: 1,
        read_only: true,
      },
      widgets: ['Reporting Overview', 'Provider Readiness', 'Compliance Summary', 'Reporting Deadlines', 'Reporting Status'],
      rbac_roles: ['reporting_admin', 'vice_rector', 'quality_manager', 'auditor', 'analyst', 'research_manager'],
    });

    const registryEntry = {
      id: 'registry-1-1',
      report_code: 'MINISTRY-01',
      report_name: 'Ministry Reporting',
      report_type: 'MINISTRY',
      owner_module: 'ministry_reporting_dashboard',
      reporting_period: '2026-Q2',
      submission_deadline: '2026-06-30T00:00:00Z',
      submission_status: 'IN_REVIEW',
      compliance_status: 'WATCH',
      provider_status: 'PENDING',
      generated_at: '2026-06-10T00:00:00Z',
      read_only: true,
    };

    mockApi.getRegistry.mockResolvedValue({
      tenant_id: 1,
      generated_at: '2026-06-10T00:00:00Z',
      read_only: true,
      entries: [registryEntry],
      requirements: [{ ...registryEntry, id: 'requirement-1-1', requirement_code: 'REQ-MINISTRY-01', requirement_status: 'MET' }],
      statuses: [{ ...registryEntry, id: 'status-1-1', risk_signal: 'stable' }],
    });
    mockApi.getTemplates.mockResolvedValue({
      tenant_id: 1,
      generated_at: '2026-06-10T00:00:00Z',
      read_only: true,
      templates: [{ ...registryEntry, id: 'template-1-1', template_version: 'v1.0', section_count: 6 }],
    });
    mockApi.getCycles.mockResolvedValue({
      tenant_id: 1,
      generated_at: '2026-06-10T00:00:00Z',
      read_only: true,
      cycles: [{ ...registryEntry, id: 'cycle-1-1', cycle_stage: 'ACTIVE', active_days_remaining: 12 }],
    });
    mockApi.getSubmissions.mockResolvedValue({
      tenant_id: 1,
      generated_at: '2026-06-10T00:00:00Z',
      read_only: true,
      submissions: [{ ...registryEntry, id: 'submission-1-1', submission_id: 'SUB-MINISTRY-01-1', reviewer_required: true }],
    });
    mockApi.getEvidence.mockResolvedValue({
      tenant_id: 1,
      generated_at: '2026-06-10T00:00:00Z',
      read_only: true,
      evidence: [{ ...registryEntry, id: 'evidence-1-1', evidence_count: 5, evidence_completeness: 80 }],
    });
    mockApi.getProviders.mockResolvedValue({
      tenant_id: 1,
      generated_at: '2026-06-10T00:00:00Z',
      read_only: true,
      providers: [{ ...registryEntry, id: 'provider-1-1', provider_key: 'MINISTRY_PROVIDER_PROFILE', live_integrations_enabled: false, submission_execution_enabled: false }],
    });

    const ministryEntry = {
      id: 'ministry-1-1',
      report_code: 'MIN-STAT-01',
      report_name: 'Statistical reporting',
      reporting_period: '2026-Q2',
      deadline: '2026-06-30T00:00:00Z',
      completion_percentage: 82,
      readiness_status: 'PARTIAL',
      submission_status: 'IN_REVIEW',
      risk_level: 'MEDIUM',
      days_remaining: 10,
      owner_module: 'analytics',
      generated_at: '2026-06-10T00:00:00Z',
      read_only: true,
    };

    mockApi.getMinistry.mockResolvedValue({ tenant_id: 1, generated_at: '2026-06-10T00:00:00Z', read_only: true, reports: [ministryEntry], signal_inventory: ['ministry_deadline_risk', 'report_overdue', 'missing_required_data', 'reporting_incomplete', 'reporting_readiness_low'] });
    mockApi.getMinistryCycles.mockResolvedValue({ tenant_id: 1, generated_at: '2026-06-10T00:00:00Z', read_only: true, cycles: [{ ...ministryEntry, cycle_status: 'ACTIVE' }] });
    mockApi.getMinistryDeadlines.mockResolvedValue({ tenant_id: 1, generated_at: '2026-06-10T00:00:00Z', read_only: true, deadlines: [{ ...ministryEntry, deadline_status: 'UPCOMING', overdue: false }] });
    mockApi.getMinistryReadiness.mockResolvedValue({ tenant_id: 1, generated_at: '2026-06-10T00:00:00Z', read_only: true, readiness: [{ ...ministryEntry, readiness_score: 82 }] });
    mockApi.getMinistryCompleteness.mockResolvedValue({ tenant_id: 1, generated_at: '2026-06-10T00:00:00Z', read_only: true, completeness: [{ ...ministryEntry, required_data_points: 10, completed_data_points: 8 }] });
    mockApi.getMinistryRisks.mockResolvedValue({ tenant_id: 1, generated_at: '2026-06-10T00:00:00Z', read_only: true, risks: [{ ...ministryEntry, signal_name: 'reporting_readiness_low', signal_owner_module: 'brain_core' }] });

    const accreditationEntry = {
      id: 'accreditation-1-1',
      accreditation_code: 'ACC-INST-01',
      accreditation_name: 'Institutional Accreditation',
      accreditation_type: 'INSTITUTIONAL',
      agency_name: 'National Accreditation Council',
      deadline: '2026-06-30T00:00:00Z',
      completion_percentage: 84,
      evidence_readiness: 'PARTIAL',
      compliance_status: 'WATCH',
      risk_level: 'MEDIUM',
      days_remaining: 12,
      owner_module: 'quality_accreditation',
      generated_at: '2026-06-10T00:00:00Z',
      read_only: true,
    };

    mockApi.getAccreditation.mockResolvedValue({ tenant_id: 1, generated_at: '2026-06-10T00:00:00Z', read_only: true, reports: [accreditationEntry], signal_inventory: ['accreditation_deadline_risk', 'accreditation_gap', 'missing_evidence', 'accreditation_compliance_risk', 'accreditation_readiness_low'] });
    mockApi.getAccreditationCycles.mockResolvedValue({ tenant_id: 1, generated_at: '2026-06-10T00:00:00Z', read_only: true, cycles: [{ ...accreditationEntry, cycle_status: 'ACTIVE' }] });
    mockApi.getAccreditationReadiness.mockResolvedValue({ tenant_id: 1, generated_at: '2026-06-10T00:00:00Z', read_only: true, readiness: [{ ...accreditationEntry, readiness_score: 84 }] });
    mockApi.getAccreditationCompliance.mockResolvedValue({ tenant_id: 1, generated_at: '2026-06-10T00:00:00Z', read_only: true, compliance: [{ ...accreditationEntry, compliance_score: 82 }] });
    mockApi.getAccreditationDeadlines.mockResolvedValue({ tenant_id: 1, generated_at: '2026-06-10T00:00:00Z', read_only: true, deadlines: [{ ...accreditationEntry, deadline_status: 'UPCOMING', overdue: false }] });
    mockApi.getAccreditationRisks.mockResolvedValue({ tenant_id: 1, generated_at: '2026-06-10T00:00:00Z', read_only: true, risks: [{ ...accreditationEntry, signal_name: 'accreditation_gap', signal_owner_module: 'brain_core' }] });

    const regulatoryEntry = {
      id: 'regulatory-1-1',
      requirement_code: 'REG-LIC-01',
      requirement_name: 'Licensing Requirements',
      regulator_name: 'National Licensing Authority',
      compliance_status: 'WATCH',
      deadline: '2026-06-30T00:00:00Z',
      days_remaining: 11,
      risk_level: 'MEDIUM',
      document_status: 'PARTIAL',
      owner_module: 'regulatory_reporting_integration',
      generated_at: '2026-06-10T00:00:00Z',
      read_only: true,
    };

    mockApi.getRegulatory.mockResolvedValue({ tenant_id: 1, generated_at: '2026-06-10T00:00:00Z', read_only: true, reports: [regulatoryEntry], signal_inventory: ['regulatory_deadline_risk', 'compliance_violation_risk', 'missing_required_document', 'licensing_gap', 'regulatory_readiness_low'] });
    mockApi.getRegulatoryRequirements.mockResolvedValue({ tenant_id: 1, generated_at: '2026-06-10T00:00:00Z', read_only: true, requirements: [{ ...regulatoryEntry, requirement_status: 'OPEN' }] });
    mockApi.getRegulatoryCompliance.mockResolvedValue({ tenant_id: 1, generated_at: '2026-06-10T00:00:00Z', read_only: true, compliance: [{ ...regulatoryEntry, compliance_score: 78 }] });
    mockApi.getRegulatoryDeadlines.mockResolvedValue({ tenant_id: 1, generated_at: '2026-06-10T00:00:00Z', read_only: true, deadlines: [{ ...regulatoryEntry, deadline_status: 'UPCOMING', overdue: false }] });
    mockApi.getRegulatoryDocuments.mockResolvedValue({ tenant_id: 1, generated_at: '2026-06-10T00:00:00Z', read_only: true, documents: [{ ...regulatoryEntry, document_name: 'REG-LIC-01-PRIMARY-DOC', document_completeness: 78 }] });
    mockApi.getRegulatoryRisks.mockResolvedValue({ tenant_id: 1, generated_at: '2026-06-10T00:00:00Z', read_only: true, risks: [{ ...regulatoryEntry, signal_name: 'regulatory_deadline_risk', signal_owner_module: 'brain_core' }] });

    const rankingRows = [
      ['QS', 'Academic Reputation', 'research_science'],
      ['QS', 'Employer Reputation', 'analytics'],
      ['QS', 'Faculty Student Ratio', 'quality_accreditation'],
      ['QS', 'Citations Per Faculty', 'research_science'],
      ['QS', 'International Faculty', 'analytics'],
      ['QS', 'International Students', 'analytics'],
      ['THE', 'Teaching', 'quality_accreditation'],
      ['THE', 'Research Environment', 'research_science'],
      ['THE', 'Research Quality', 'research_science'],
      ['THE', 'International Outlook', 'analytics'],
      ['THE', 'Industry Engagement', 'analytics'],
    ].map(([system, indicator, owner], index) => ({
      id: `ranking-1-${index + 1}`,
      ranking_system: system,
      indicator_name: indicator,
      indicator_score: 82 - (index % 4),
      benchmark_score: 86 - (index % 3),
      trend_direction: index % 3 === 0 ? 'DOWN' : index % 2 === 0 ? 'UP' : 'STABLE',
      readiness_level: index < 4 ? 'READY' : 'PARTIAL',
      risk_level: index % 4 === 0 ? 'HIGH' : 'MEDIUM',
      owner_module: owner,
      generated_at: '2026-06-10T00:00:00Z',
      read_only: true,
    }));

    mockApi.getRanking.mockResolvedValue({
      tenant_id: 1,
      generated_at: '2026-06-10T00:00:00Z',
      read_only: true,
      reports: rankingRows,
      signal_inventory: ['ranking_readiness_low', 'qs_indicator_decline', 'the_indicator_decline', 'ranking_risk_high', 'benchmark_gap_high'],
    });
    mockApi.getRankingIndicators.mockResolvedValue({ tenant_id: 1, generated_at: '2026-06-10T00:00:00Z', read_only: true, indicators: rankingRows.map((item, index) => ({ ...item, indicator_weight: 16 - (index % 5) })) });
    mockApi.getRankingReadiness.mockResolvedValue({ tenant_id: 1, generated_at: '2026-06-10T00:00:00Z', read_only: true, readiness: rankingRows.map((item) => ({ ...item, readiness_score: item.indicator_score })) });
    mockApi.getRankingBenchmarks.mockResolvedValue({ tenant_id: 1, generated_at: '2026-06-10T00:00:00Z', read_only: true, benchmarks: rankingRows.map((item) => ({ ...item, benchmark_gap: Math.max(0, item.benchmark_score - item.indicator_score) })) });
    mockApi.getRankingTrends.mockResolvedValue({ tenant_id: 1, generated_at: '2026-06-10T00:00:00Z', read_only: true, trends: rankingRows.map((item, index) => ({ ...item, trend_delta: (index % 5) - 2 })) });
    mockApi.getRankingRisks.mockResolvedValue({ tenant_id: 1, generated_at: '2026-06-10T00:00:00Z', read_only: true, risks: rankingRows.map((item, index) => ({ ...item, signal_name: ['ranking_readiness_low', 'qs_indicator_decline', 'the_indicator_decline', 'ranking_risk_high', 'benchmark_gap_high'][index % 5], signal_owner_module: 'brain_core' })) });

    const nobdRows = [
      ['NOBD-STUDENT', 'Student Data', 'student_lifecycle'],
      ['NOBD-STAFF', 'Staff Data', 'hr'],
      ['NOBD-ACADEMIC', 'Academic Data', 'academic_operations'],
      ['NOBD-PROGRAM', 'Educational Programs', 'admissions'],
      ['NOBD-RESEARCH', 'Research Data', 'research_science'],
      ['NOBD-GRADUATE', 'Graduate Data', 'analytics'],
      ['NOBD-INFRA', 'Infrastructure Data', 'finance'],
    ].map(([code, name, owner], index) => ({
      id: 'nobd-1-' + (index + 1),
      dataset_code: code,
      dataset_name: name,
      records_total: 1800 + index * 200,
      records_complete: 1500 + index * 160,
      completeness_percentage: 82 - (index % 5),
      quality_score: 84 - (index % 4),
      sync_status: index % 3 === 0 ? 'DELAYED' : 'SCHEDULED',
      risk_level: index % 4 === 0 ? 'HIGH' : 'MEDIUM',
      owner_module: owner,
      generated_at: '2026-06-10T00:00:00Z',
      read_only: true,
    }));

    mockApi.getNobd.mockResolvedValue({
      tenant_id: 1,
      generated_at: '2026-06-10T00:00:00Z',
      read_only: true,
      reports: nobdRows,
      signal_inventory: ['nobd_completeness_low', 'nobd_quality_risk', 'nobd_sync_delay', 'missing_required_dataset', 'nobd_readiness_low'],
    });
    mockApi.getNobdDatasets.mockResolvedValue({ tenant_id: 1, generated_at: '2026-06-10T00:00:00Z', read_only: true, datasets: nobdRows.map((item, index) => ({ ...item, dataset_priority: index < 3 ? 'HIGH' : 'MEDIUM' })) });
    mockApi.getNobdCompleteness.mockResolvedValue({ tenant_id: 1, generated_at: '2026-06-10T00:00:00Z', read_only: true, completeness: nobdRows.map((item) => ({ ...item, completeness_gap: item.records_total - item.records_complete })) });
    mockApi.getNobdQuality.mockResolvedValue({ tenant_id: 1, generated_at: '2026-06-10T00:00:00Z', read_only: true, quality: nobdRows.map((item) => ({ ...item, quality_band: item.quality_score >= 85 ? 'HIGH' : 'MEDIUM' })) });
    mockApi.getNobdSyncStatus.mockResolvedValue({ tenant_id: 1, generated_at: '2026-06-10T00:00:00Z', read_only: true, sync_status: nobdRows.map((item, index) => ({ ...item, sync_lag_hours: 4 + index })) });
    mockApi.getNobdRisks.mockResolvedValue({ tenant_id: 1, generated_at: '2026-06-10T00:00:00Z', read_only: true, risks: nobdRows.map((item, index) => ({ ...item, signal_name: ['nobd_completeness_low', 'nobd_quality_risk', 'nobd_sync_delay', 'missing_required_dataset', 'nobd_readiness_low'][index % 5], signal_owner_module: 'brain_core' })) });

    const complianceRows = [
      ['CMP-MINISTRY', 'Ministry Compliance', 'quality_accreditation'],
      ['CMP-ACCREDITATION', 'Accreditation Compliance', 'quality_accreditation'],
      ['CMP-NOBD', 'NOBD Compliance', 'student_lifecycle'],
      ['CMP-REGULATORY', 'Regulatory Compliance', 'executive_governance'],
      ['CMP-RANKING', 'Ranking Compliance', 'research_science'],
      ['CMP-POLICY', 'Internal Policy Compliance', 'hr'],
    ].map(([code, name, owner], index) => ({
      id: 'compliance-1-' + (index + 1),
      control_code: code,
      control_name: name,
      compliance_status: index < 2 ? 'COMPLIANT' : 'WATCH',
      readiness_score: 88 - index * 3,
      risk_level: index < 2 ? 'LOW' : 'MEDIUM',
      gap_count: index % 3,
      owner_module: owner,
      generated_at: '2026-06-10T00:00:00Z',
      read_only: true,
    }));

    mockApi.getCompliance.mockResolvedValue({
      tenant_id: 1,
      generated_at: '2026-06-10T00:00:00Z',
      read_only: true,
      reports: complianceRows,
      signal_inventory: ['compliance_gap_high', 'compliance_readiness_low', 'compliance_risk_high', 'control_failure_detected', 'mandatory_submission_missing'],
    });
    mockApi.getComplianceControls.mockResolvedValue({ tenant_id: 1, generated_at: '2026-06-10T00:00:00Z', read_only: true, controls: complianceRows.map((item, index) => ({ ...item, control_type: index < 4 ? 'MANDATORY' : 'INTERNAL' })) });
    mockApi.getComplianceReadiness.mockResolvedValue({ tenant_id: 1, generated_at: '2026-06-10T00:00:00Z', read_only: true, readiness: complianceRows.map((item) => ({ ...item, readiness_level: item.readiness_score >= 85 ? 'READY' : 'PARTIAL' })) });
    mockApi.getComplianceGaps.mockResolvedValue({ tenant_id: 1, generated_at: '2026-06-10T00:00:00Z', read_only: true, gaps: complianceRows.map((item) => ({ ...item, gap_severity: item.gap_count >= 2 ? 'MEDIUM' : 'LOW' })) });
    mockApi.getComplianceRisks.mockResolvedValue({ tenant_id: 1, generated_at: '2026-06-10T00:00:00Z', read_only: true, risks: complianceRows.map((item, index) => ({ ...item, signal_name: ['compliance_gap_high', 'compliance_readiness_low', 'compliance_risk_high', 'control_failure_detected', 'mandatory_submission_missing'][index % 5], signal_owner_module: 'brain_core' })) });
  });

  it('renders ranking reporting sections', async () => {
    renderWithClient(<ReportingRuntimeShellPage />);

    expect(await screen.findByTestId('ranking-reporting-center-section')).toBeInTheDocument();
    expect(screen.getByTestId('ranking-qs-readiness-section')).toBeInTheDocument();
    expect(screen.getByTestId('ranking-the-readiness-section')).toBeInTheDocument();
    expect(screen.getByTestId('ranking-benchmarks-section')).toBeInTheDocument();
    expect(screen.getByTestId('ranking-trends-section')).toBeInTheDocument();
    expect(screen.getByTestId('ranking-risks-section')).toBeInTheDocument();
  });

  it('renders QS/THE coverage and risk owner surface', async () => {
    renderWithClient(<ReportingRuntimeShellPage />);

    const center = await screen.findByTestId('ranking-reporting-center-section');
    const scoped = within(center);
    const risks = await screen.findByTestId('ranking-risks-section');
    const riskScoped = within(risks);

    expect(scoped.getByText('Academic Reputation')).toBeInTheDocument();
    expect(scoped.getByText('Employer Reputation')).toBeInTheDocument();
    expect(scoped.getByText('Faculty Student Ratio')).toBeInTheDocument();
    expect(scoped.getByText('Citations Per Faculty')).toBeInTheDocument();
    expect(scoped.getByText('International Faculty')).toBeInTheDocument();
    expect(scoped.getByText('International Students')).toBeInTheDocument();
    expect(scoped.getByText('Teaching')).toBeInTheDocument();
    expect(scoped.getByText('Research Environment')).toBeInTheDocument();
    expect(scoped.getByText('Research Quality')).toBeInTheDocument();
    expect(scoped.getByText('International Outlook')).toBeInTheDocument();
    expect(scoped.getByText('Industry Engagement')).toBeInTheDocument();
    expect(riskScoped.getAllByText(/owner=brain_core/i).length).toBeGreaterThan(0);
  });
});
