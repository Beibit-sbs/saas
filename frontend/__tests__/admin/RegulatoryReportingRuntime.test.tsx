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
  },
}));

vi.mock('@/modules/reporting-runtime/api', () => ({ reportingRuntimeApi: mockApi }));
vi.mock('@/shared/ui/permission-gate', () => ({ RequirePermission: ({ children }: { children: React.ReactNode }) => <>{children}</> }));

import { ReportingRuntimeShellPage } from '@/modules/reporting-runtime/page';

function renderWithClient(ui: React.ReactNode) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(<QueryClientProvider client={client}>{ui}</QueryClientProvider>);
}

describe('Regulatory Reporting Runtime', () => {
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
      rbac_roles: ['reporting_admin', 'vice_rector', 'quality_manager', 'auditor', 'analyst', 'compliance_manager'],
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

    mockApi.getRegulatory.mockResolvedValue({
      tenant_id: 1,
      generated_at: '2026-06-10T00:00:00Z',
      read_only: true,
      reports: regulatoryReports,
      signal_inventory: ['regulatory_deadline_risk', 'compliance_violation_risk', 'missing_required_document', 'licensing_gap', 'regulatory_readiness_low'],
    });
    mockApi.getRegulatoryRequirements.mockResolvedValue({
      tenant_id: 1,
      generated_at: '2026-06-10T00:00:00Z',
      read_only: true,
      requirements: regulatoryReports.map((item) => ({ ...item, requirement_status: item.compliance_status === 'COMPLIANT' ? 'SATISFIED' : 'OPEN' })),
    });
    mockApi.getRegulatoryCompliance.mockResolvedValue({
      tenant_id: 1,
      generated_at: '2026-06-10T00:00:00Z',
      read_only: true,
      compliance: regulatoryReports.map((item, index) => ({ ...item, compliance_score: 90 - index })),
    });
    mockApi.getRegulatoryDeadlines.mockResolvedValue({
      tenant_id: 1,
      generated_at: '2026-06-10T00:00:00Z',
      read_only: true,
      deadlines: regulatoryReports.map((item, index) => ({ ...item, deadline_status: index < 6 ? 'UPCOMING' : 'OVERDUE', overdue: index >= 6 })),
    });
    mockApi.getRegulatoryDocuments.mockResolvedValue({
      tenant_id: 1,
      generated_at: '2026-06-10T00:00:00Z',
      read_only: true,
      documents: regulatoryReports.map((item, index) => ({ ...item, document_name: `${item.requirement_code}-PRIMARY-DOC`, document_completeness: 88 - index })),
    });
    mockApi.getRegulatoryRisks.mockResolvedValue({
      tenant_id: 1,
      generated_at: '2026-06-10T00:00:00Z',
      read_only: true,
      risks: regulatoryReports.map((item, index) => ({
        ...item,
        signal_name: ['regulatory_deadline_risk', 'compliance_violation_risk', 'missing_required_document', 'licensing_gap', 'regulatory_readiness_low'][index % 5],
        signal_owner_module: 'brain_core',
      })),
    });
  });

  it('renders regulatory reporting sections', async () => {
    renderWithClient(<ReportingRuntimeShellPage />);

    expect(await screen.findByTestId('regulatory-reporting-center-section')).toBeInTheDocument();
    expect(screen.getByTestId('regulatory-requirements-section')).toBeInTheDocument();
    expect(screen.getByTestId('regulatory-compliance-section')).toBeInTheDocument();
    expect(screen.getByTestId('regulatory-deadlines-section')).toBeInTheDocument();
    expect(screen.getByTestId('regulatory-documents-section')).toBeInTheDocument();
    expect(screen.getByTestId('regulatory-risks-section')).toBeInTheDocument();
  });

  it('renders required regulatory coverage and risk owner surface', async () => {
    renderWithClient(<ReportingRuntimeShellPage />);

    const center = await screen.findByTestId('regulatory-reporting-center-section');
    const centerScoped = within(center);
    const risks = await screen.findByTestId('regulatory-risks-section');
    const riskScoped = within(risks);

    expect(centerScoped.getByText('Licensing Requirements')).toBeInTheDocument();
    expect(centerScoped.getByText('Educational Activity Requirements')).toBeInTheDocument();
    expect(centerScoped.getByText('Scientific Activity Requirements')).toBeInTheDocument();
    expect(centerScoped.getByText('Information Security Requirements')).toBeInTheDocument();
    expect(centerScoped.getByText('Personal Data Requirements')).toBeInTheDocument();
    expect(centerScoped.getByText('Labor Requirements')).toBeInTheDocument();
    expect(centerScoped.getByText('Financial Requirements')).toBeInTheDocument();
    expect(centerScoped.getByText('Internal Regulatory Requirements')).toBeInTheDocument();
    expect(riskScoped.getAllByText(/owner=brain_core/i).length).toBeGreaterThan(0);
  });
});
