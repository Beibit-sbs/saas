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
  },
}));

vi.mock('@/modules/reporting-runtime/api', () => ({ reportingRuntimeApi: mockApi }));
vi.mock('@/shared/ui/permission-gate', () => ({ RequirePermission: ({ children }: { children: React.ReactNode }) => <>{children}</> }));

import { ReportingRuntimeShellPage } from '@/modules/reporting-runtime/page';

function renderWithClient(ui: React.ReactNode) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(<QueryClientProvider client={client}>{ui}</QueryClientProvider>);
}

describe('Reporting Runtime Shell', () => {
  beforeEach(() => {
    mockApi.getRuntimeShell.mockResolvedValue({
      tenant_id: 1,
      reporting_center_name: 'Reporting Brain Runtime Shell',
      active_reporting_cycles: 6,
      active_submissions: 8,
      active_deadlines: 9,
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
      compliance_score: 78,
      generated_at: '2026-06-10T00:00:00Z',
      read_only: true,
      auditability_preserved: true,
      overview: {
        reporting_center_name: 'Reporting Brain Runtime Shell',
        owner_module: 'reporting_runtime',
        active_reporting_cycles: 6,
        active_submissions: 8,
        active_deadlines: 9,
        source_modules: ['reporting_runtime', 'analytics', 'executive_governance'],
        read_only: true,
      },
      compliance: {
        owner_module: 'reporting_runtime',
        compliance_score: 78,
        risk_band: 'MEDIUM',
        source_modules: ['reporting_runtime', 'brain_core', 'executive_governance'],
        read_only: true,
      },
      deadlines: {
        owner_module: 'reporting_runtime',
        active_deadlines: 9,
        overdue_deadlines: 2,
        upcoming_deadlines: 7,
        deadline_signals: ['report_overdue', 'ministry_deadline_risk', 'submission_risk'],
        source_modules: ['reporting_runtime', 'brain_core', 'executive_governance'],
        read_only: true,
      },
      reporting_status: {
        open_items: 4,
        in_review_items: 3,
        blocked_items: 2,
        read_only: true,
      },
      widgets: [
        'Reporting Overview',
        'Provider Readiness',
        'Compliance Summary',
        'Reporting Deadlines',
        'Reporting Status',
      ],
      rbac_roles: ['reporting_admin', 'vice_rector', 'quality_manager', 'auditor', 'analyst'],
    });

    const baseEntry = {
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
      entries: [baseEntry],
      requirements: [{ ...baseEntry, id: 'requirement-1-1', requirement_code: 'REQ-MINISTRY-01', requirement_status: 'MET' }],
      statuses: [{ ...baseEntry, id: 'status-1-1', risk_signal: 'stable' }],
    });
    mockApi.getTemplates.mockResolvedValue({
      tenant_id: 1,
      generated_at: '2026-06-10T00:00:00Z',
      read_only: true,
      templates: [{ ...baseEntry, id: 'template-1-1', template_version: 'v1.0', section_count: 6 }],
    });
    mockApi.getCycles.mockResolvedValue({
      tenant_id: 1,
      generated_at: '2026-06-10T00:00:00Z',
      read_only: true,
      cycles: [{ ...baseEntry, id: 'cycle-1-1', cycle_stage: 'ACTIVE', active_days_remaining: 12 }],
    });
    mockApi.getSubmissions.mockResolvedValue({
      tenant_id: 1,
      generated_at: '2026-06-10T00:00:00Z',
      read_only: true,
      submissions: [{ ...baseEntry, id: 'submission-1-1', submission_id: 'SUB-MINISTRY-01-1', reviewer_required: true }],
    });
    mockApi.getEvidence.mockResolvedValue({
      tenant_id: 1,
      generated_at: '2026-06-10T00:00:00Z',
      read_only: true,
      evidence: [{ ...baseEntry, id: 'evidence-1-1', evidence_count: 5, evidence_completeness: 80 }],
    });
    mockApi.getProviders.mockResolvedValue({
      tenant_id: 1,
      generated_at: '2026-06-10T00:00:00Z',
      read_only: true,
      providers: [{ ...baseEntry, id: 'provider-1-1', provider_key: 'MINISTRY_PROVIDER_PROFILE', live_integrations_enabled: false, submission_execution_enabled: false }],
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

    mockApi.getMinistry.mockResolvedValue({
      tenant_id: 1,
      generated_at: '2026-06-10T00:00:00Z',
      read_only: true,
      reports: [ministryEntry],
      signal_inventory: ['ministry_deadline_risk', 'report_overdue', 'missing_required_data', 'reporting_incomplete', 'reporting_readiness_low'],
    });
    mockApi.getMinistryCycles.mockResolvedValue({
      tenant_id: 1,
      generated_at: '2026-06-10T00:00:00Z',
      read_only: true,
      cycles: [{ ...ministryEntry, cycle_status: 'ACTIVE' }],
    });
    mockApi.getMinistryDeadlines.mockResolvedValue({
      tenant_id: 1,
      generated_at: '2026-06-10T00:00:00Z',
      read_only: true,
      deadlines: [{ ...ministryEntry, deadline_status: 'UPCOMING', overdue: false }],
    });
    mockApi.getMinistryReadiness.mockResolvedValue({
      tenant_id: 1,
      generated_at: '2026-06-10T00:00:00Z',
      read_only: true,
      readiness: [{ ...ministryEntry, readiness_score: 82 }],
    });
    mockApi.getMinistryCompleteness.mockResolvedValue({
      tenant_id: 1,
      generated_at: '2026-06-10T00:00:00Z',
      read_only: true,
      completeness: [{ ...ministryEntry, required_data_points: 10, completed_data_points: 8 }],
    });
    mockApi.getMinistryRisks.mockResolvedValue({
      tenant_id: 1,
      generated_at: '2026-06-10T00:00:00Z',
      read_only: true,
      risks: [{ ...ministryEntry, signal_name: 'reporting_readiness_low', signal_owner_module: 'brain_core' }],
    });

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

    mockApi.getAccreditation.mockResolvedValue({
      tenant_id: 1,
      generated_at: '2026-06-10T00:00:00Z',
      read_only: true,
      reports: [accreditationEntry],
      signal_inventory: ['accreditation_deadline_risk', 'accreditation_gap', 'missing_evidence', 'accreditation_compliance_risk', 'accreditation_readiness_low'],
    });
    mockApi.getAccreditationCycles.mockResolvedValue({
      tenant_id: 1,
      generated_at: '2026-06-10T00:00:00Z',
      read_only: true,
      cycles: [{ ...accreditationEntry, cycle_status: 'ACTIVE' }],
    });
    mockApi.getAccreditationReadiness.mockResolvedValue({
      tenant_id: 1,
      generated_at: '2026-06-10T00:00:00Z',
      read_only: true,
      readiness: [{ ...accreditationEntry, readiness_score: 84 }],
    });
    mockApi.getAccreditationCompliance.mockResolvedValue({
      tenant_id: 1,
      generated_at: '2026-06-10T00:00:00Z',
      read_only: true,
      compliance: [{ ...accreditationEntry, compliance_score: 82 }],
    });
    mockApi.getAccreditationDeadlines.mockResolvedValue({
      tenant_id: 1,
      generated_at: '2026-06-10T00:00:00Z',
      read_only: true,
      deadlines: [{ ...accreditationEntry, deadline_status: 'UPCOMING', overdue: false }],
    });
    mockApi.getAccreditationRisks.mockResolvedValue({
      tenant_id: 1,
      generated_at: '2026-06-10T00:00:00Z',
      read_only: true,
      risks: [{ ...accreditationEntry, signal_name: 'accreditation_gap', signal_owner_module: 'brain_core' }],
    });

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

    mockApi.getRegulatory.mockResolvedValue({
      tenant_id: 1,
      generated_at: '2026-06-10T00:00:00Z',
      read_only: true,
      reports: [regulatoryEntry],
      signal_inventory: ['regulatory_deadline_risk', 'compliance_violation_risk', 'missing_required_document', 'licensing_gap', 'regulatory_readiness_low'],
    });
    mockApi.getRegulatoryRequirements.mockResolvedValue({
      tenant_id: 1,
      generated_at: '2026-06-10T00:00:00Z',
      read_only: true,
      requirements: [{ ...regulatoryEntry, requirement_status: 'OPEN' }],
    });
    mockApi.getRegulatoryCompliance.mockResolvedValue({
      tenant_id: 1,
      generated_at: '2026-06-10T00:00:00Z',
      read_only: true,
      compliance: [{ ...regulatoryEntry, compliance_score: 78 }],
    });
    mockApi.getRegulatoryDeadlines.mockResolvedValue({
      tenant_id: 1,
      generated_at: '2026-06-10T00:00:00Z',
      read_only: true,
      deadlines: [{ ...regulatoryEntry, deadline_status: 'UPCOMING', overdue: false }],
    });
    mockApi.getRegulatoryDocuments.mockResolvedValue({
      tenant_id: 1,
      generated_at: '2026-06-10T00:00:00Z',
      read_only: true,
      documents: [{ ...regulatoryEntry, document_name: 'REG-LIC-01-PRIMARY-DOC', document_completeness: 78 }],
    });
    mockApi.getRegulatoryRisks.mockResolvedValue({
      tenant_id: 1,
      generated_at: '2026-06-10T00:00:00Z',
      read_only: true,
      risks: [{ ...regulatoryEntry, signal_name: 'regulatory_deadline_risk', signal_owner_module: 'brain_core' }],
    });

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
  });

  it('renders runtime shell sections', async () => {
    renderWithClient(<ReportingRuntimeShellPage />);

    expect(await screen.findByTestId('reporting-runtime-shell')).toBeInTheDocument();
    expect(screen.getByTestId('reporting-overview-section')).toBeInTheDocument();
    expect(screen.getByTestId('provider-readiness-section')).toBeInTheDocument();
    expect(screen.getByTestId('compliance-summary-section')).toBeInTheDocument();
    expect(screen.getByTestId('reporting-deadlines-section')).toBeInTheDocument();
    expect(screen.getByTestId('reporting-status-section')).toBeInTheDocument();
  });

  it('renders read-only runtime values', async () => {
    renderWithClient(<ReportingRuntimeShellPage />);
    const complianceSection = await screen.findByTestId('compliance-summary-section');
    const complianceScoped = within(complianceSection);

    expect(await screen.findByText('Reporting Runtime Shell')).toBeInTheDocument();
    expect(complianceScoped.getByText(/Risk band: MEDIUM/i)).toBeInTheDocument();
    expect(complianceScoped.getByText(/Compliance score: 78/i)).toBeInTheDocument();
    expect(screen.getByText(/NOT_CONNECTED=1, READY=3, PENDING=1/i)).toBeInTheDocument();
    expect(screen.getByText(/read_only=true/i)).toBeInTheDocument();
  });
});
