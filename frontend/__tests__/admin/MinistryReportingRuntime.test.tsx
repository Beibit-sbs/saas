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
