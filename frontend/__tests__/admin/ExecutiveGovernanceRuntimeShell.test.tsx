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
