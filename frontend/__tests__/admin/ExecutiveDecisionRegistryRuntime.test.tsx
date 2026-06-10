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
  },
}));

vi.mock('@/modules/executive-governance/api', () => ({ executiveGovernanceApi: mockApi }));
vi.mock('@/shared/ui/permission-gate', () => ({ RequirePermission: ({ children }: { children: React.ReactNode }) => <>{children}</> }));

import { ExecutiveGovernanceRuntimeShellPage } from '@/modules/executive-governance/page';

function renderWithClient(ui: React.ReactNode) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(<QueryClientProvider client={client}>{ui}</QueryClientProvider>);
}

describe('Executive Decision Registry runtime', () => {
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
  });

  it('renders decision registry and summaries', async () => {
    renderWithClient(<ExecutiveGovernanceRuntimeShellPage />);

    expect(await screen.findByTestId('executive-decision-registry-view')).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: 'Executive Decisions' })).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: 'Decision Sources' })).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: 'Execution Status' })).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: 'Escalation Summary' })).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: 'Decision Signals' })).toBeInTheDocument();
  });

  it('renders decision summary and execution statuses', async () => {
    renderWithClient(<ExecutiveGovernanceRuntimeShellPage />);

    expect(await screen.findByText('Total decisions: 7')).toBeInTheDocument();
    expect(screen.getByText('committee_decision_registry: 4')).toBeInTheDocument();
    expect(screen.getByText('order_decree_registry: 3')).toBeInTheDocument();
    expect(screen.getByText('IN_PROGRESS: 1')).toBeInTheDocument();
    expect(screen.getByText('OVERDUE: 1')).toBeInTheDocument();
  });

  it('renders decision signal summary', async () => {
    renderWithClient(<ExecutiveGovernanceRuntimeShellPage />);

    expect(await screen.findByTestId('decision-signal-summary')).toBeInTheDocument();
    expect(screen.getByText(/decision_stagnation, overdue_assignment, execution_delay, escalation_risk, protocol_non_execution/i)).toBeInTheDocument();
  });
});
