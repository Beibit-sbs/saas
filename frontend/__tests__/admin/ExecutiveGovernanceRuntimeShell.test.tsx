import React from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const { mockApi } = vi.hoisted(() => ({
  mockApi: {
    getOverview: vi.fn(),
    getSummary: vi.fn(),
    getSignals: vi.fn(),
    getDashboard: vi.fn(),
    getDecisions: vi.fn(),
    getDecisionSummary: vi.fn(),
    getDecisionExecution: vi.fn(),
    getMeetings: vi.fn(),
    getMeetingSummary: vi.fn(),
    getProtocols: vi.fn(),
    getProtocolSummary: vi.fn(),
    getProtocolExecution: vi.fn(),
  },
}));

vi.mock('@/modules/executive-governance/api', () => ({ executiveGovernanceApi: mockApi }));
vi.mock('@/shared/ui/permission-gate', () => ({ RequirePermission: ({ children }: { children: React.ReactNode }) => <>{children}</> }));

import { ExecutiveGovernanceRuntimeShellPage } from '@/modules/executive-governance/page';

function renderWithClient(ui: React.ReactNode) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(<QueryClientProvider client={client}>{ui}</QueryClientProvider>);
}

describe('Executive Governance runtime shell', () => {
  beforeEach(() => {
    mockApi.getOverview.mockResolvedValue({
      tenant_id: 1,
      owner_module: 'executive_control_tower',
      runtime_boundary: 'UNIFIED_READ_ONLY_RUNTIME_SHELL',
      navigation_entry: '/console/executive-governance',
      canonical_modules: [
        'executive_control_tower',
        'rector_assignment_workflow',
        'committee_decision_registry',
        'order_decree_registry',
        'analytics',
        'brain_core',
      ],
      read_only_runtime: true,
      provider_integrations_enabled: false,
      external_calls_enabled: false,
      executive_assignments: 21,
      executive_decisions: 13,
      executive_protocols: 8,
      executive_meetings: 5,
      overdue_items: 4,
      escalated_items: 2,
      strategic_items: 7,
      executive_signals: 10,
      generated_at: '2026-06-10T00:00:00Z',
    });

    mockApi.getSummary.mockResolvedValue({
      tenant_id: 1,
      read_only: true,
      owner_modules: ['executive_control_tower', 'rector_assignment_workflow', 'brain_core'],
      executive_assignments: 21,
      executive_decisions: 13,
      executive_protocols: 8,
      executive_meetings: 5,
      overdue_items: 4,
      escalated_items: 2,
      strategic_items: 7,
      executive_signals: 10,
      generated_at: '2026-06-10T00:00:00Z',
    });

    mockApi.getSignals.mockResolvedValue([
      { signal_family: 'overdue_assignment', owner_module: 'brain_core', source_module: 'rector_assignment_workflow', read_only: true, observed_items: 3, notes: 'n1' },
      { signal_family: 'decision_stagnation', owner_module: 'brain_core', source_module: 'committee_decision_registry', read_only: true, observed_items: 4, notes: 'n2' },
    ]);

    mockApi.getDashboard.mockResolvedValue({
      tenant_id: 1,
      dashboard_owner_module: 'executive_control_tower',
      dashboard_view: 'executive_control_tower',
      widgets: ['Executive Overview', 'Signal Summary'],
      executive_assignments: 21,
      executive_decisions: 13,
      executive_protocols: 8,
      executive_meetings: 5,
      overdue_items: 4,
      escalated_items: 2,
      strategic_items: 7,
      executive_signals: 10,
      signal_summaries: [],
      rbac_roles: ['rector', 'vice_rector', 'chief_of_staff', 'executive_manager', 'auditor', 'administrator'],
      read_only: true,
      auditability_preserved: true,
      generated_at: '2026-06-10T00:00:00Z',
    });

    mockApi.getDecisions.mockResolvedValue([
      {
        decision_id: 'EGD-01-001',
        decision_type: 'committee_decision',
        decision_source: 'committee_decision_registry',
        decision_title: 'Executive decision item 1',
        decision_status: 'ACTIVE',
        decision_date: '2026-06-10T00:00:00Z',
        execution_status: 'IN_PROGRESS',
        execution_progress: 40,
        assigned_units: ['rectorate'],
        overdue_flag: false,
        escalation_flag: false,
      },
    ]);

    mockApi.getDecisionSummary.mockResolvedValue({
      tenant_id: 1,
      entries: [],
      total_decisions: 7,
      decision_sources: { committee_decision_registry: 4, order_decree_registry: 3 },
      execution_status_counts: {
        NOT_STARTED: 1,
        IN_PROGRESS: 1,
        AT_RISK: 1,
        ESCALATED: 1,
        OVERDUE: 1,
        COMPLETED: 1,
        CLOSED: 1,
      },
      read_only: true,
      aggregator_only: true,
      owner_modules: ['committee_decision_registry', 'order_decree_registry', 'rector_assignment_workflow'],
      generated_at: '2026-06-10T00:00:00Z',
    });

    mockApi.getDecisionExecution.mockResolvedValue({
      tenant_id: 1,
      total_decisions: 7,
      execution_status_counts: {
        NOT_STARTED: 1,
        IN_PROGRESS: 1,
        AT_RISK: 1,
        ESCALATED: 1,
        OVERDUE: 1,
        COMPLETED: 1,
        CLOSED: 1,
      },
      overdue_items: 1,
      escalated_items: 1,
      signal_families: ['decision_stagnation', 'overdue_assignment', 'execution_delay', 'escalation_risk', 'protocol_non_execution'],
      read_only: true,
      aggregator_only: true,
      generated_at: '2026-06-10T00:00:00Z',
    });

    mockApi.getMeetings.mockResolvedValue([
      {
        meeting_id: 'MEET-01-001',
        meeting_type: 'executive_board',
        meeting_title: 'Executive governance meeting 1',
        meeting_date: '2026-06-10T00:00:00Z',
        meeting_status: 'SCHEDULED',
        chairperson: 'rector',
        participants_count: 10,
        protocol_count: 2,
        decision_count: 3,
        execution_status: 'IN_PROGRESS',
      },
    ]);

    mockApi.getMeetingSummary.mockResolvedValue({
      tenant_id: 1,
      entries: [],
      total_meetings: 4,
      meeting_status_counts: { SCHEDULED: 1, CONDUCTED: 1, APPROVED: 1, CLOSED: 1 },
      total_protocols: 6,
      total_decisions: 10,
      read_only: true,
      generated_at: '2026-06-10T00:00:00Z',
    });

    mockApi.getProtocols.mockResolvedValue([
      {
        protocol_id: 'PROT-01-001',
        protocol_number: 'PG-01-100',
        protocol_title: 'Executive protocol item 1',
        protocol_date: '2026-06-10T00:00:00Z',
        protocol_status: 'IN_EXECUTION',
        decision_count: 3,
        assignment_count: 4,
        execution_progress: 60,
        overdue_items: 1,
        escalated_items: 0,
      },
    ]);

    mockApi.getProtocolSummary.mockResolvedValue({
      tenant_id: 1,
      entries: [],
      total_protocols: 5,
      protocol_status_counts: { DRAFT: 1, APPROVED: 1, IN_EXECUTION: 1, COMPLETED: 1, CLOSED: 1 },
      total_decisions: 15,
      total_assignments: 20,
      average_execution_progress: 62,
      overdue_items: 2,
      escalated_items: 1,
      read_only: true,
      generated_at: '2026-06-10T00:00:00Z',
    });

    mockApi.getProtocolExecution.mockResolvedValue({
      tenant_id: 1,
      total_protocols: 5,
      average_execution_progress: 62,
      overdue_items: 2,
      escalated_items: 1,
      completion_status: { COMPLETED: 1, CLOSED: 1, IN_EXECUTION: 1 },
      linkage_inventory: {
        meeting_registry: 5,
        protocol_registry: 5,
        decision_registry: 15,
        rector_assignment_workflow: 20,
      },
      signal_families: ['protocol_non_execution', 'execution_delay', 'overdue_assignment', 'escalation_risk', 'decision_stagnation'],
      read_only: true,
      generated_at: '2026-06-10T00:00:00Z',
    });
  });

  it('renders runtime shell sections', async () => {
    renderWithClient(<ExecutiveGovernanceRuntimeShellPage />);

    expect(await screen.findByTestId('executive-governance-runtime-shell')).toBeInTheDocument();
    expect(screen.getByText('Executive Governance Runtime Shell')).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: 'Decision Summary' })).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: 'Assignment Summary' })).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: 'Protocol Summary' })).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: 'Signal Summary' })).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: 'Dashboard Summary' })).toBeInTheDocument();
  });

  it('renders overview cards and signal families', async () => {
    renderWithClient(<ExecutiveGovernanceRuntimeShellPage />);

    expect(await screen.findByText('Executive Assignments')).toBeInTheDocument();
    expect(screen.getByText('21')).toBeInTheDocument();
    expect(screen.getByText('overdue_assignment')).toBeInTheDocument();
    expect(screen.getByText('decision_stagnation')).toBeInTheDocument();
  });

  it('renders dashboard summary and rbac roles', async () => {
    renderWithClient(<ExecutiveGovernanceRuntimeShellPage />);

    expect(await screen.findByTestId('executive-governance-dashboard-summary')).toBeInTheDocument();
    expect(screen.getByText(/Dashboard owner: executive_control_tower/i)).toBeInTheDocument();
    expect(screen.getByText(/RBAC roles: rector, vice_rector, chief_of_staff, executive_manager, auditor, administrator/i)).toBeInTheDocument();
  });
});
