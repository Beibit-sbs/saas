import React from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, screen } from '@testing-library/react';
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

describe('Reporting Registry Runtime', () => {
  beforeEach(() => {
    mockApi.getRuntimeShell.mockResolvedValue({
      tenant_id: 1,
      reporting_center_name: 'Reporting Brain Runtime Shell',
      active_reporting_cycles: 4,
      active_submissions: 6,
      active_deadlines: 7,
      provider_readiness: {
        owner_module: 'regulatory_reporting_integration',
        provider_status_counts: { NOT_CONNECTED: 1, READY: 3, PENDING: 1 },
        provider_readiness: 'NON_LIVE_PROFILE_ONLY',
        blocker_count: 1,
        warning_count: 1,
        live_integrations_enabled: false,
        sync_enabled: false,
        submission_execution_enabled: false,
        source_modules: ['regulatory_reporting_integration', 'provider_readiness'],
        read_only: true,
      },
      compliance_score: 81,
      generated_at: '2026-06-10T00:00:00Z',
      read_only: true,
      auditability_preserved: true,
      overview: {
        reporting_center_name: 'Reporting Brain Runtime Shell',
        owner_module: 'reporting_runtime',
        active_reporting_cycles: 4,
        active_submissions: 6,
        active_deadlines: 7,
        source_modules: ['reporting_runtime', 'analytics', 'executive_governance'],
        read_only: true,
      },
      compliance: {
        owner_module: 'reporting_runtime',
        compliance_score: 81,
        risk_band: 'LOW',
        source_modules: ['reporting_runtime', 'brain_core', 'executive_governance'],
        read_only: true,
      },
      deadlines: {
        owner_module: 'reporting_runtime',
        active_deadlines: 7,
        overdue_deadlines: 2,
        upcoming_deadlines: 5,
        deadline_signals: ['report_overdue', 'submission_risk'],
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

    const registryEntries = [
      ['MINISTRY', 'MINISTRY-01'],
      ['ACCREDITATION', 'ACCREDITATION-01'],
      ['REGULATORY', 'REGULATORY-01'],
      ['QS', 'QS-01'],
      ['THE', 'THE-01'],
      ['NOBD', 'NOBD-01'],
      ['RECTOR', 'RECTOR-01'],
      ['STATISTICAL', 'STATISTICAL-01'],
    ].map(([type, code], index) => ({
      id: `registry-1-${index + 1}`,
      report_code: code,
      report_name: `${type} Reporting`,
      report_type: type,
      owner_module: 'analytics',
      reporting_period: '2026-Q2',
      submission_deadline: '2026-06-30T00:00:00Z',
      submission_status: 'IN_REVIEW',
      compliance_status: 'WATCH',
      provider_status: 'PENDING',
      generated_at: '2026-06-10T00:00:00Z',
      read_only: true,
    }));

    mockApi.getRegistry.mockResolvedValue({
      tenant_id: 1,
      generated_at: '2026-06-10T00:00:00Z',
      read_only: true,
      entries: registryEntries,
      requirements: registryEntries.map((entry, index) => ({
        ...entry,
        id: `requirement-1-${index + 1}`,
        requirement_code: `REQ-${entry.report_code}`,
        requirement_status: 'MET',
      })),
      statuses: registryEntries.map((entry, index) => ({
        ...entry,
        id: `status-1-${index + 1}`,
        risk_signal: 'stable',
      })),
    });

    mockApi.getTemplates.mockResolvedValue({
      tenant_id: 1,
      generated_at: '2026-06-10T00:00:00Z',
      read_only: true,
      templates: [{ ...registryEntries[0], id: 'template-1-1', template_version: 'v1.0', section_count: 6 }],
    });
    mockApi.getCycles.mockResolvedValue({
      tenant_id: 1,
      generated_at: '2026-06-10T00:00:00Z',
      read_only: true,
      cycles: [{ ...registryEntries[0], id: 'cycle-1-1', cycle_stage: 'ACTIVE', active_days_remaining: 12 }],
    });
    mockApi.getSubmissions.mockResolvedValue({
      tenant_id: 1,
      generated_at: '2026-06-10T00:00:00Z',
      read_only: true,
      submissions: [{ ...registryEntries[0], id: 'submission-1-1', submission_id: 'SUB-MINISTRY-01-1', reviewer_required: true }],
    });
    mockApi.getEvidence.mockResolvedValue({
      tenant_id: 1,
      generated_at: '2026-06-10T00:00:00Z',
      read_only: true,
      evidence: [{ ...registryEntries[0], id: 'evidence-1-1', evidence_count: 5, evidence_completeness: 80 }],
    });
    mockApi.getProviders.mockResolvedValue({
      tenant_id: 1,
      generated_at: '2026-06-10T00:00:00Z',
      read_only: true,
      providers: [{ ...registryEntries[0], id: 'provider-1-1', provider_key: 'MINISTRY_PROVIDER_PROFILE', live_integrations_enabled: false, submission_execution_enabled: false }],
    });

    const ministryEntry = {
      id: 'ministry-1-1',
      report_code: 'MIN-STAT-01',
      report_name: 'Statistical reporting',
      reporting_period: '2026-Q2',
      deadline: '2026-06-30T00:00:00Z',
      completion_percentage: 84,
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
      readiness: [{ ...ministryEntry, readiness_score: 84 }],
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
      completion_percentage: 86,
      evidence_readiness: 'READY',
      compliance_status: 'COMPLIANT',
      risk_level: 'LOW',
      days_remaining: 14,
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
      readiness: [{ ...accreditationEntry, readiness_score: 86 }],
    });
    mockApi.getAccreditationCompliance.mockResolvedValue({
      tenant_id: 1,
      generated_at: '2026-06-10T00:00:00Z',
      read_only: true,
      compliance: [{ ...accreditationEntry, compliance_score: 88 }],
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
      risks: [{ ...accreditationEntry, signal_name: 'accreditation_deadline_risk', signal_owner_module: 'brain_core' }],
    });

    const regulatoryEntry = {
      id: 'regulatory-1-1',
      requirement_code: 'REG-LIC-01',
      requirement_name: 'Licensing Requirements',
      regulator_name: 'National Licensing Authority',
      compliance_status: 'WATCH',
      deadline: '2026-06-30T00:00:00Z',
      days_remaining: 10,
      risk_level: 'MEDIUM',
      document_status: 'PARTIAL',
      owner_module: 'regulatory_reporting_integration',
      generated_at: '2026-06-10T00:00:00Z',
      read_only: true,
    };

    mockApi.getRegulatory.mockResolvedValue({ tenant_id: 1, generated_at: '2026-06-10T00:00:00Z', read_only: true, reports: [regulatoryEntry], signal_inventory: ['regulatory_deadline_risk', 'compliance_violation_risk', 'missing_required_document', 'licensing_gap', 'regulatory_readiness_low'] });
    mockApi.getRegulatoryRequirements.mockResolvedValue({ tenant_id: 1, generated_at: '2026-06-10T00:00:00Z', read_only: true, requirements: [{ ...regulatoryEntry, requirement_status: 'OPEN' }] });
    mockApi.getRegulatoryCompliance.mockResolvedValue({ tenant_id: 1, generated_at: '2026-06-10T00:00:00Z', read_only: true, compliance: [{ ...regulatoryEntry, compliance_score: 79 }] });
    mockApi.getRegulatoryDeadlines.mockResolvedValue({ tenant_id: 1, generated_at: '2026-06-10T00:00:00Z', read_only: true, deadlines: [{ ...regulatoryEntry, deadline_status: 'UPCOMING', overdue: false }] });
    mockApi.getRegulatoryDocuments.mockResolvedValue({ tenant_id: 1, generated_at: '2026-06-10T00:00:00Z', read_only: true, documents: [{ ...regulatoryEntry, document_name: 'REG-LIC-01-PRIMARY-DOC', document_completeness: 79 }] });
    mockApi.getRegulatoryRisks.mockResolvedValue({ tenant_id: 1, generated_at: '2026-06-10T00:00:00Z', read_only: true, risks: [{ ...regulatoryEntry, signal_name: 'regulatory_deadline_risk', signal_owner_module: 'brain_core' }] });
  });

  it('renders reporting registry runtime sections', async () => {
    renderWithClient(<ReportingRuntimeShellPage />);

    expect(await screen.findByTestId('reporting-registry-section')).toBeInTheDocument();
    expect(screen.getByTestId('reporting-templates-section')).toBeInTheDocument();
    expect(screen.getByTestId('reporting-cycles-section')).toBeInTheDocument();
    expect(screen.getByTestId('reporting-submissions-section')).toBeInTheDocument();
    expect(screen.getByTestId('reporting-evidence-section')).toBeInTheDocument();
    expect(screen.getByTestId('provider-registry-section')).toBeInTheDocument();
  });

  it('renders all required report type coverage entries', async () => {
    renderWithClient(<ReportingRuntimeShellPage />);

    expect(await screen.findByText('MINISTRY')).toBeInTheDocument();
    expect(screen.getByText('ACCREDITATION')).toBeInTheDocument();
    expect(screen.getByText('REGULATORY')).toBeInTheDocument();
    expect(screen.getByText('QS')).toBeInTheDocument();
    expect(screen.getByText('THE')).toBeInTheDocument();
    expect(screen.getByText('NOBD')).toBeInTheDocument();
    expect(screen.getByText('RECTOR')).toBeInTheDocument();
    expect(screen.getByText('STATISTICAL')).toBeInTheDocument();
  });
});
