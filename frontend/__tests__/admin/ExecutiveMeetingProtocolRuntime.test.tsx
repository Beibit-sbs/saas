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
    getAssignments: vi.fn(),
    getAssignmentSummary: vi.fn(),
    getAssignmentExecution: vi.fn(),
    getAssignmentRisks: vi.fn(),
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

describe('Executive Meeting and Protocol runtime', () => {
  beforeEach(() => {
    mockApi.getOverview.mockResolvedValue({
      tenant_id: 1,
      owner_module: 'executive_control_tower',
      runtime_boundary: 'UNIFIED_READ_ONLY_RUNTIME_SHELL',
      navigation_entry: '/console/executive-governance',
      canonical_modules: ['executive_control_tower', 'rector_assignment_workflow', 'committee_decision_registry', 'order_decree_registry', 'analytics', 'brain_core'],
      read_only_runtime: true,
      provider_integrations_enabled: false,
      external_calls_enabled: false,
      executive_assignments: 20,
      executive_decisions: 12,
      executive_protocols: 8,
      executive_meetings: 5,
      overdue_items: 3,
      escalated_items: 2,
      strategic_items: 6,
      executive_signals: 10,
      generated_at: '2026-06-10T00:00:00Z',
    });

    mockApi.getSummary.mockResolvedValue({
      tenant_id: 1,
      read_only: true,
      owner_modules: ['executive_control_tower', 'rector_assignment_workflow', 'brain_core'],
      executive_assignments: 20,
      executive_decisions: 12,
      executive_protocols: 8,
      executive_meetings: 5,
      overdue_items: 3,
      escalated_items: 2,
      strategic_items: 6,
      executive_signals: 10,
      generated_at: '2026-06-10T00:00:00Z',
    });

    mockApi.getSignals.mockResolvedValue([
      { signal_family: 'overdue_assignment', owner_module: 'brain_core', source_module: 'rector_assignment_workflow', read_only: true, observed_items: 3, notes: 'n1' },
    ]);

    mockApi.getDashboard.mockResolvedValue({
      tenant_id: 1,
      dashboard_owner_module: 'executive_control_tower',
      dashboard_view: 'executive_control_tower',
      widgets: ['Executive Overview'],
      executive_assignments: 20,
      executive_decisions: 12,
      executive_protocols: 8,
      executive_meetings: 5,
      overdue_items: 3,
      escalated_items: 2,
      strategic_items: 6,
      executive_signals: 10,
      signal_summaries: [],
      rbac_roles: ['rector', 'vice_rector', 'chief_of_staff', 'executive_manager', 'auditor', 'administrator'],
      read_only: true,
      auditability_preserved: true,
      generated_at: '2026-06-10T00:00:00Z',
    });

    mockApi.getDecisions.mockResolvedValue([]);
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

    mockApi.getAssignments.mockResolvedValue([
      {
        assignment_id: 'EGA-01-001',
        assignment_title: 'Executive assignment item 1',
        assignment_source: 'rector_assignment_workflow',
        assignment_type: 'RECTOR_ASSIGNMENT',
        assigned_unit: 'strategy-office',
        assigned_person: 'exec.user.1',
        created_at: '2026-06-10T00:00:00Z',
        due_date: '2026-06-10T00:00:00Z',
        completion_percent: 52,
        execution_status: 'IN_PROGRESS',
        risk_level: 'MEDIUM',
        overdue_flag: false,
        escalation_flag: false,
      },
    ]);
    mockApi.getAssignmentSummary.mockResolvedValue({
      tenant_id: 1,
      entries: [],
      total_assignments: 7,
      active_assignments: 5,
      completed_assignments: 2,
      overdue_assignments: 1,
      escalated_assignments: 1,
      execution_performance: 62,
      execution_trend: 'STABLE',
      read_only: true,
      aggregator_only: true,
      owner_modules: ['rector_assignment_workflow', 'decision_registry', 'protocol_registry', 'analytics'],
      generated_at: '2026-06-10T00:00:00Z',
    });
    mockApi.getAssignmentExecution.mockResolvedValue({
      tenant_id: 1,
      total_assignments: 7,
      execution_status_counts: {
        NOT_STARTED: 1,
        IN_PROGRESS: 2,
        AT_RISK: 1,
        ESCALATED: 1,
        OVERDUE: 1,
        COMPLETED: 1,
        CLOSED: 0,
      },
      overdue_assignments: 1,
      escalated_assignments: 1,
      execution_performance: 62,
      execution_trend: 'STABLE',
      escalation_inventory: { high: 1, critical: 0, overdue: 1 },
      escalation_summary: { total_escalations: 1, high_risk: 1, overdue: 1 },
      escalation_trends: ['weekly_stable', 'monthly_improving'],
      high_risk_assignments: [],
      signal_families: ['overdue_assignment', 'execution_delay', 'escalation_risk', 'assignment_stagnation', 'workload_imbalance'],
      read_only: true,
      aggregator_only: true,
      generated_at: '2026-06-10T00:00:00Z',
    });
    mockApi.getAssignmentRisks.mockResolvedValue({
      tenant_id: 1,
      total_assignments: 7,
      execution_status_counts: {
        NOT_STARTED: 1,
        IN_PROGRESS: 2,
        AT_RISK: 1,
        ESCALATED: 1,
        OVERDUE: 1,
        COMPLETED: 1,
        CLOSED: 0,
      },
      overdue_assignments: 1,
      escalated_assignments: 1,
      execution_performance: 62,
      execution_trend: 'DECLINING',
      escalation_inventory: { high: 1, critical: 0, overdue: 1 },
      escalation_summary: { total_escalations: 1, high_risk: 1, overdue: 1 },
      escalation_trends: ['high_risk_watchlist_active', 'escalation_rate_stable'],
      high_risk_assignments: [],
      signal_families: ['overdue_assignment', 'execution_delay', 'escalation_risk', 'assignment_stagnation', 'workload_imbalance'],
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

  it('renders meeting and protocol runtime sections', async () => {
    renderWithClient(<ExecutiveGovernanceRuntimeShellPage />);

    expect(await screen.findByTestId('meeting-registry-runtime')).toBeInTheDocument();
    expect(screen.getByTestId('meeting-analytics-runtime')).toBeInTheDocument();
    expect(screen.getByTestId('protocol-registry-runtime')).toBeInTheDocument();
    expect(screen.getByTestId('protocol-execution-runtime')).toBeInTheDocument();
    expect(screen.getByTestId('protocol-signals-runtime')).toBeInTheDocument();
  });

  it('renders protocol linkage inventory and signal families', async () => {
    renderWithClient(<ExecutiveGovernanceRuntimeShellPage />);

    expect(await screen.findByText('meeting_registry: 5')).toBeInTheDocument();
    expect(screen.getByText('decision_registry: 15')).toBeInTheDocument();
    expect(screen.getByText(/protocol_non_execution, execution_delay, overdue_assignment, escalation_risk, decision_stagnation/i)).toBeInTheDocument();
  });
});
