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
  },
}));

vi.mock('@/modules/reporting-runtime/api', () => ({ reportingRuntimeApi: mockApi }));
vi.mock('@/shared/ui/permission-gate', () => ({ RequirePermission: ({ children }: { children: React.ReactNode }) => <>{children}</> }));

import { ReportingRuntimeShellPage } from '@/modules/reporting-runtime/page';

function renderWithClient(ui: React.ReactNode) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(<QueryClientProvider client={client}>{ui}</QueryClientProvider>);
}

describe('Accreditation Reporting Runtime', () => {
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
  });

  it('renders accreditation reporting sections', async () => {
    renderWithClient(<ReportingRuntimeShellPage />);

    expect(await screen.findByTestId('accreditation-reporting-center-section')).toBeInTheDocument();
    expect(screen.getByTestId('accreditation-cycles-section')).toBeInTheDocument();
    expect(screen.getByTestId('accreditation-readiness-section')).toBeInTheDocument();
    expect(screen.getByTestId('accreditation-compliance-section')).toBeInTheDocument();
    expect(screen.getByTestId('accreditation-deadlines-section')).toBeInTheDocument();
    expect(screen.getByTestId('accreditation-risks-section')).toBeInTheDocument();
  });

  it('renders required accreditation coverage and risk owner surface', async () => {
    renderWithClient(<ReportingRuntimeShellPage />);
    const accreditationCenter = await screen.findByTestId('accreditation-reporting-center-section');
    const scoped = within(accreditationCenter);
    const riskSection = await screen.findByTestId('accreditation-risks-section');
    const riskScoped = within(riskSection);

    expect(scoped.getByText('Institutional Accreditation')).toBeInTheDocument();
    expect(scoped.getByText('Specialized Accreditation')).toBeInTheDocument();
    expect(scoped.getByText('Program Accreditation')).toBeInTheDocument();
    expect(scoped.getByText('International Accreditation')).toBeInTheDocument();
    expect(scoped.getByText('Internal Quality Reviews')).toBeInTheDocument();
    expect(scoped.getByText('Accreditation Evidence Packages')).toBeInTheDocument();
    expect(riskScoped.getAllByText(/owner=brain_core/i).length).toBeGreaterThan(0);
  });
});
