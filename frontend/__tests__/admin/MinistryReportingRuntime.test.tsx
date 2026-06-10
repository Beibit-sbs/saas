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

describe('Ministry Reporting Runtime', () => {
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
      rbac_roles: ['reporting_admin', 'vice_rector', 'quality_manager', 'auditor', 'analyst'],
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

    const ministryReports = [
      ['MIN-STAT-01', 'Statistical reporting', 'analytics'],
      ['MIN-ACAD-01', 'Academic reporting', 'ministry_reporting_dashboard'],
      ['MIN-SCI-01', 'Scientific reporting', 'research_science'],
      ['MIN-FIN-01', 'Financial reporting', 'finance_procurement_asset'],
      ['MIN-INFRA-01', 'Infrastructure reporting', 'campus_facilities_housing_transport'],
      ['MIN-HR-01', 'Human resource reporting', 'hr_staff_governance'],
      ['MIN-DIGI-01', 'Digitalization reporting', 'platform'],
    ].map(([code, name, owner], index) => ({
      id: `ministry-1-${index + 1}`,
      report_code: code,
      report_name: name,
      reporting_period: '2026-Q2',
      deadline: '2026-06-30T00:00:00Z',
      completion_percentage: 75 + index,
      readiness_status: index < 2 ? 'READY' : 'PARTIAL',
      submission_status: index < 3 ? 'IN_REVIEW' : 'DRAFT',
      risk_level: index < 2 ? 'LOW' : 'MEDIUM',
      days_remaining: 10 - index,
      owner_module: owner,
      generated_at: '2026-06-10T00:00:00Z',
      read_only: true,
    }));

    mockApi.getMinistry.mockResolvedValue({
      tenant_id: 1,
      generated_at: '2026-06-10T00:00:00Z',
      read_only: true,
      reports: ministryReports,
      signal_inventory: ['ministry_deadline_risk', 'report_overdue', 'missing_required_data', 'reporting_incomplete', 'reporting_readiness_low'],
    });
    mockApi.getMinistryCycles.mockResolvedValue({
      tenant_id: 1,
      generated_at: '2026-06-10T00:00:00Z',
      read_only: true,
      cycles: ministryReports.map((item, index) => ({ ...item, cycle_status: index < 4 ? 'ACTIVE' : 'PLANNED' })),
    });
    mockApi.getMinistryDeadlines.mockResolvedValue({
      tenant_id: 1,
      generated_at: '2026-06-10T00:00:00Z',
      read_only: true,
      deadlines: ministryReports.map((item, index) => ({ ...item, deadline_status: index < 5 ? 'UPCOMING' : 'OVERDUE', overdue: index >= 5 })),
    });
    mockApi.getMinistryReadiness.mockResolvedValue({
      tenant_id: 1,
      generated_at: '2026-06-10T00:00:00Z',
      read_only: true,
      readiness: ministryReports.map((item) => ({ ...item, readiness_score: item.completion_percentage })),
    });
    mockApi.getMinistryCompleteness.mockResolvedValue({
      tenant_id: 1,
      generated_at: '2026-06-10T00:00:00Z',
      read_only: true,
      completeness: ministryReports.map((item, index) => ({ ...item, required_data_points: 10 + index, completed_data_points: 8 + index })),
    });
    mockApi.getMinistryRisks.mockResolvedValue({
      tenant_id: 1,
      generated_at: '2026-06-10T00:00:00Z',
      read_only: true,
      risks: ministryReports.map((item, index) => ({
        ...item,
        signal_name: ['ministry_deadline_risk', 'report_overdue', 'missing_required_data', 'reporting_incomplete', 'reporting_readiness_low'][index % 5],
        signal_owner_module: 'brain_core',
      })),
    });

    const accreditationReports = [
      ['ACC-INST-01', 'Institutional Accreditation', 'INSTITUTIONAL', 'National Accreditation Council'],
      ['ACC-SPEC-01', 'Specialized Accreditation', 'SPECIALIZED', 'Sector Accreditation Board'],
      ['ACC-PROG-01', 'Program Accreditation', 'PROGRAM', 'Program Accreditation Agency'],
      ['ACC-INTL-01', 'International Accreditation', 'INTERNATIONAL', 'International Quality Alliance'],
      ['ACC-IQR-01', 'Internal Quality Reviews', 'INTERNAL_REVIEW', 'Internal QA Committee'],
      ['ACC-EVID-01', 'Accreditation Evidence Packages', 'EVIDENCE_PACKAGE', 'Accreditation Documentation Unit'],
    ].map(([code, name, type, agency], index) => ({
      id: `accreditation-1-${index + 1}`,
      accreditation_code: code,
      accreditation_name: name,
      accreditation_type: type,
      agency_name: agency,
      deadline: '2026-06-30T00:00:00Z',
      completion_percentage: 78 + index,
      evidence_readiness: index < 2 ? 'READY' : 'PARTIAL',
      compliance_status: index < 2 ? 'COMPLIANT' : 'WATCH',
      risk_level: index < 2 ? 'LOW' : 'MEDIUM',
      days_remaining: 12 - index,
      owner_module: 'quality_accreditation',
      generated_at: '2026-06-10T00:00:00Z',
      read_only: true,
    }));

    mockApi.getAccreditation.mockResolvedValue({
      tenant_id: 1,
      generated_at: '2026-06-10T00:00:00Z',
      read_only: true,
      reports: accreditationReports,
      signal_inventory: ['accreditation_deadline_risk', 'accreditation_gap', 'missing_evidence', 'accreditation_compliance_risk', 'accreditation_readiness_low'],
    });
    mockApi.getAccreditationCycles.mockResolvedValue({
      tenant_id: 1,
      generated_at: '2026-06-10T00:00:00Z',
      read_only: true,
      cycles: accreditationReports.map((item, index) => ({ ...item, cycle_status: index < 4 ? 'ACTIVE' : 'PLANNED' })),
    });
    mockApi.getAccreditationReadiness.mockResolvedValue({
      tenant_id: 1,
      generated_at: '2026-06-10T00:00:00Z',
      read_only: true,
      readiness: accreditationReports.map((item) => ({ ...item, readiness_score: item.completion_percentage })),
    });
    mockApi.getAccreditationCompliance.mockResolvedValue({
      tenant_id: 1,
      generated_at: '2026-06-10T00:00:00Z',
      read_only: true,
      compliance: accreditationReports.map((item) => ({ ...item, compliance_score: item.completion_percentage })),
    });
    mockApi.getAccreditationDeadlines.mockResolvedValue({
      tenant_id: 1,
      generated_at: '2026-06-10T00:00:00Z',
      read_only: true,
      deadlines: accreditationReports.map((item, index) => ({ ...item, deadline_status: index < 5 ? 'UPCOMING' : 'OVERDUE', overdue: index >= 5 })),
    });
    mockApi.getAccreditationRisks.mockResolvedValue({
      tenant_id: 1,
      generated_at: '2026-06-10T00:00:00Z',
      read_only: true,
      risks: accreditationReports.map((item, index) => ({
        ...item,
        signal_name: ['accreditation_deadline_risk', 'accreditation_gap', 'missing_evidence', 'accreditation_compliance_risk', 'accreditation_readiness_low'][index % 5],
        signal_owner_module: 'brain_core',
      })),
    });

    const regulatoryReports = [
      'Licensing Requirements',
      'Educational Activity Requirements',
      'Scientific Activity Requirements',
      'Information Security Requirements',
      'Personal Data Requirements',
      'Labor Requirements',
      'Financial Requirements',
      'Internal Regulatory Requirements',
    ].map((name, index) => ({
      id: `regulatory-1-${index + 1}`,
      requirement_code: `REG-${index + 1}`,
      requirement_name: name,
      regulator_name: 'Regulatory Authority',
      compliance_status: index < 2 ? 'COMPLIANT' : 'WATCH',
      deadline: '2026-06-30T00:00:00Z',
      days_remaining: 10 - index,
      risk_level: index < 2 ? 'LOW' : 'MEDIUM',
      document_status: index < 2 ? 'COMPLETE' : 'PARTIAL',
      owner_module: 'regulatory_reporting_integration',
      generated_at: '2026-06-10T00:00:00Z',
      read_only: true,
    }));

    mockApi.getRegulatory.mockResolvedValue({ tenant_id: 1, generated_at: '2026-06-10T00:00:00Z', read_only: true, reports: regulatoryReports, signal_inventory: ['regulatory_deadline_risk', 'compliance_violation_risk', 'missing_required_document', 'licensing_gap', 'regulatory_readiness_low'] });
    mockApi.getRegulatoryRequirements.mockResolvedValue({ tenant_id: 1, generated_at: '2026-06-10T00:00:00Z', read_only: true, requirements: regulatoryReports.map((item) => ({ ...item, requirement_status: item.compliance_status === 'COMPLIANT' ? 'SATISFIED' : 'OPEN' })) });
    mockApi.getRegulatoryCompliance.mockResolvedValue({ tenant_id: 1, generated_at: '2026-06-10T00:00:00Z', read_only: true, compliance: regulatoryReports.map((item, index) => ({ ...item, compliance_score: 90 - index })) });
    mockApi.getRegulatoryDeadlines.mockResolvedValue({ tenant_id: 1, generated_at: '2026-06-10T00:00:00Z', read_only: true, deadlines: regulatoryReports.map((item, index) => ({ ...item, deadline_status: index < 6 ? 'UPCOMING' : 'OVERDUE', overdue: index >= 6 })) });
    mockApi.getRegulatoryDocuments.mockResolvedValue({ tenant_id: 1, generated_at: '2026-06-10T00:00:00Z', read_only: true, documents: regulatoryReports.map((item, index) => ({ ...item, document_name: `${item.requirement_code}-PRIMARY-DOC`, document_completeness: 88 - index })) });
    mockApi.getRegulatoryRisks.mockResolvedValue({ tenant_id: 1, generated_at: '2026-06-10T00:00:00Z', read_only: true, risks: regulatoryReports.map((item, index) => ({ ...item, signal_name: ['regulatory_deadline_risk', 'compliance_violation_risk', 'missing_required_document', 'licensing_gap', 'regulatory_readiness_low'][index % 5], signal_owner_module: 'brain_core' })) });

    const rankingEntry = {
      id: 'ranking-1-1',
      ranking_system: 'QS',
      indicator_name: 'Academic Reputation',
      indicator_score: 80,
      benchmark_score: 86,
      trend_direction: 'DOWN',
      readiness_level: 'PARTIAL',
      risk_level: 'MEDIUM',
      owner_module: 'research_science',
      generated_at: '2026-06-10T00:00:00Z',
      read_only: true,
    };

    mockApi.getRanking.mockResolvedValue({ tenant_id: 1, generated_at: '2026-06-10T00:00:00Z', read_only: true, reports: [rankingEntry], signal_inventory: ['ranking_readiness_low', 'qs_indicator_decline', 'the_indicator_decline', 'ranking_risk_high', 'benchmark_gap_high'] });
    mockApi.getRankingIndicators.mockResolvedValue({ tenant_id: 1, generated_at: '2026-06-10T00:00:00Z', read_only: true, indicators: [{ ...rankingEntry, indicator_weight: 16 }] });
    mockApi.getRankingReadiness.mockResolvedValue({ tenant_id: 1, generated_at: '2026-06-10T00:00:00Z', read_only: true, readiness: [{ ...rankingEntry, readiness_score: 80 }] });
    mockApi.getRankingBenchmarks.mockResolvedValue({ tenant_id: 1, generated_at: '2026-06-10T00:00:00Z', read_only: true, benchmarks: [{ ...rankingEntry, benchmark_gap: 6 }] });
    mockApi.getRankingTrends.mockResolvedValue({ tenant_id: 1, generated_at: '2026-06-10T00:00:00Z', read_only: true, trends: [{ ...rankingEntry, trend_delta: -2 }] });
    mockApi.getRankingRisks.mockResolvedValue({ tenant_id: 1, generated_at: '2026-06-10T00:00:00Z', read_only: true, risks: [{ ...rankingEntry, signal_name: 'ranking_risk_high', signal_owner_module: 'brain_core' }] });

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

  it('renders ministry reporting sections', async () => {
    renderWithClient(<ReportingRuntimeShellPage />);

    expect(await screen.findByTestId('ministry-reporting-center-section')).toBeInTheDocument();
    expect(screen.getByTestId('ministry-reporting-cycles-section')).toBeInTheDocument();
    expect(screen.getByTestId('ministry-reporting-deadlines-section')).toBeInTheDocument();
    expect(screen.getByTestId('ministry-reporting-readiness-section')).toBeInTheDocument();
    expect(screen.getByTestId('ministry-reporting-completeness-section')).toBeInTheDocument();
    expect(screen.getByTestId('ministry-reporting-risks-section')).toBeInTheDocument();
  });

  it('renders required ministry reporting coverage and read-only risk signals', async () => {
    renderWithClient(<ReportingRuntimeShellPage />);
    const ministryCenter = await screen.findByTestId('ministry-reporting-center-section');
    const scoped = within(ministryCenter);
    const riskSection = await screen.findByTestId('ministry-reporting-risks-section');
    const riskScoped = within(riskSection);

    expect(scoped.getByText('Statistical reporting')).toBeInTheDocument();
    expect(scoped.getByText('Academic reporting')).toBeInTheDocument();
    expect(scoped.getByText('Scientific reporting')).toBeInTheDocument();
    expect(scoped.getByText('Financial reporting')).toBeInTheDocument();
    expect(scoped.getByText('Infrastructure reporting')).toBeInTheDocument();
    expect(scoped.getByText('Human resource reporting')).toBeInTheDocument();
    expect(scoped.getByText('Digitalization reporting')).toBeInTheDocument();
    expect(riskScoped.getAllByText(/owner=brain_core/i).length).toBeGreaterThan(0);
  });
});
