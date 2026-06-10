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
    getControlTower: vi.fn(),
    getControlTowerSummary: vi.fn(),
    getControlTowerRisks: vi.fn(),
    getControlTowerKpis: vi.fn(),
    getControlTowerEscalations: vi.fn(),
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

describe('Executive Control Tower runtime', () => {
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
      execution_status_counts: { NOT_STARTED: 1, IN_PROGRESS: 1, AT_RISK: 1, ESCALATED: 1, OVERDUE: 1, COMPLETED: 1, CLOSED: 1 },
      read_only: true,
      aggregator_only: true,
      owner_modules: ['committee_decision_registry', 'order_decree_registry', 'rector_assignment_workflow'],
      generated_at: '2026-06-10T00:00:00Z',
    });
    mockApi.getDecisionExecution.mockResolvedValue({
      tenant_id: 1,
      total_decisions: 7,
      execution_status_counts: { NOT_STARTED: 1, IN_PROGRESS: 1, AT_RISK: 1, ESCALATED: 1, OVERDUE: 1, COMPLETED: 1, CLOSED: 1 },
      overdue_items: 1,
      escalated_items: 1,
      signal_families: ['decision_stagnation', 'overdue_assignment', 'execution_delay', 'escalation_risk', 'protocol_non_execution'],
      read_only: true,
      aggregator_only: true,
      generated_at: '2026-06-10T00:00:00Z',
    });

    mockApi.getAssignments.mockResolvedValue([]);
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
      execution_status_counts: { NOT_STARTED: 1, IN_PROGRESS: 2, AT_RISK: 1, ESCALATED: 1, OVERDUE: 1, COMPLETED: 1, CLOSED: 0 },
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
      execution_status_counts: { NOT_STARTED: 1, IN_PROGRESS: 2, AT_RISK: 1, ESCALATED: 1, OVERDUE: 1, COMPLETED: 1, CLOSED: 0 },
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

    mockApi.getControlTower.mockResolvedValue({
      tenant_id: 1,
      dashboard_owner_module: 'executive_control_tower',
      dashboard_view: 'rector_dashboard',
      total_decisions: 7,
      total_protocols: 5,
      total_assignments: 7,
      active_assignments: 5,
      completed_assignments: 2,
      overdue_assignments: 1,
      escalated_assignments: 1,
      execution_rate: 62,
      risk_score: 48,
      kpi_score: 68,
      executive_workload: 50,
      strategic_initiatives: { on_track: 4, at_risk: 2, delayed: 1 },
      read_only: true,
      aggregator_only: true,
      auditability_preserved: true,
      generated_at: '2026-06-10T00:00:00Z',
    });
    mockApi.getControlTowerSummary.mockResolvedValue({
      tenant_id: 1,
      rector_overview: {
        tenant_id: 1,
        dashboard_owner_module: 'executive_control_tower',
        dashboard_view: 'rector_dashboard',
        total_decisions: 7,
        total_protocols: 5,
        total_assignments: 7,
        active_assignments: 5,
        completed_assignments: 2,
        overdue_assignments: 1,
        escalated_assignments: 1,
        execution_rate: 62,
        risk_score: 48,
        kpi_score: 68,
        executive_workload: 50,
        strategic_initiatives: { on_track: 4, at_risk: 2, delayed: 1 },
        read_only: true,
        aggregator_only: true,
        auditability_preserved: true,
        generated_at: '2026-06-10T00:00:00Z',
      },
      university_execution_status: {
        tenant_id: 1,
        total_decisions: 7,
        total_protocols: 5,
        total_assignments: 7,
        active_assignments: 5,
        completed_assignments: 2,
        overdue_assignments: 1,
        escalated_assignments: 1,
        execution_rate: 62,
        completion_rate: 28,
        escalation_rate: 14,
        workload_distribution: { rectorate: 2, 'strategy-office': 2 },
        unit_performance: { rectorate: 80, 'strategy-office': 75 },
        strategic_initiative_status: { on_track: 4, at_risk: 2, delayed: 1 },
        read_only: true,
        aggregator_only: true,
        generated_at: '2026-06-10T00:00:00Z',
      },
      strategic_initiatives: { on_track: 4, at_risk: 2, delayed: 1 },
      executive_risks: {
        tenant_id: 1,
        risk_score: 48,
        risk_distribution: { low: 3, medium: 2, high: 1, critical: 1 },
        high_risk_assignments: [],
        high_risk_units: { 'chief-of-staff-office': 2 },
        high_risk_initiatives: { strategic_reform_track: 1 },
        escalation_hotspots: { 'chief-of-staff-office': 2 },
        overdue_hotspots: { 'strategy-office': 1 },
        signal_families: ['executive_workload', 'kpi_drift'],
        read_only: true,
        aggregator_only: true,
        generated_at: '2026-06-10T00:00:00Z',
      },
      kpi_performance: {
        tenant_id: 1,
        kpi_score: 68,
        kpi_distribution: { green: 5, amber: 2, red: 1 },
        execution_rate: 62,
        completion_rate: 28,
        escalation_rate: 14,
        unit_performance: { rectorate: 80, 'strategy-office': 75 },
        strategic_initiative_status: { on_track: 4, at_risk: 2, delayed: 1 },
        signal_families: ['kpi_drift', 'strategic_goal_slippage'],
        read_only: true,
        aggregator_only: true,
        generated_at: '2026-06-10T00:00:00Z',
      },
      escalation_summary: { overdue_assignments: 1, escalated_assignments: 1, escalation_rate: 14 },
      read_only: true,
      aggregator_only: true,
      generated_at: '2026-06-10T00:00:00Z',
    });
    mockApi.getControlTowerRisks.mockResolvedValue({
      tenant_id: 1,
      risk_score: 48,
      risk_distribution: { low: 3, medium: 2, high: 1, critical: 1 },
      high_risk_assignments: [],
      high_risk_units: { 'chief-of-staff-office': 2 },
      high_risk_initiatives: { strategic_reform_track: 1 },
      escalation_hotspots: { 'chief-of-staff-office': 2 },
      overdue_hotspots: { 'strategy-office': 1 },
      signal_families: ['executive_workload', 'kpi_drift'],
      read_only: true,
      aggregator_only: true,
      generated_at: '2026-06-10T00:00:00Z',
    });
    mockApi.getControlTowerKpis.mockResolvedValue({
      tenant_id: 1,
      kpi_score: 68,
      kpi_distribution: { green: 5, amber: 2, red: 1 },
      execution_rate: 62,
      completion_rate: 28,
      escalation_rate: 14,
      unit_performance: { rectorate: 80, 'strategy-office': 75 },
      strategic_initiative_status: { on_track: 4, at_risk: 2, delayed: 1 },
      signal_families: ['kpi_drift', 'strategic_goal_slippage'],
      read_only: true,
      aggregator_only: true,
      generated_at: '2026-06-10T00:00:00Z',
    });
    mockApi.getControlTowerEscalations.mockResolvedValue({
      tenant_id: 1,
      total_decisions: 7,
      total_protocols: 5,
      total_assignments: 7,
      active_assignments: 5,
      completed_assignments: 2,
      overdue_assignments: 1,
      escalated_assignments: 1,
      execution_rate: 62,
      completion_rate: 28,
      escalation_rate: 14,
      workload_distribution: { rectorate: 2, 'strategy-office': 2 },
      unit_performance: { rectorate: 80, 'strategy-office': 75 },
      strategic_initiative_status: { on_track: 4, at_risk: 2, delayed: 1 },
      read_only: true,
      aggregator_only: true,
      generated_at: '2026-06-10T00:00:00Z',
    });

    mockApi.getMeetings.mockResolvedValue([]);
    mockApi.getMeetingSummary.mockResolvedValue({ tenant_id: 1, entries: [], total_meetings: 4, meeting_status_counts: { SCHEDULED: 1 }, total_protocols: 6, total_decisions: 10, read_only: true, generated_at: '2026-06-10T00:00:00Z' });
    mockApi.getProtocols.mockResolvedValue([]);
    mockApi.getProtocolSummary.mockResolvedValue({ tenant_id: 1, entries: [], total_protocols: 5, protocol_status_counts: { DRAFT: 1 }, total_decisions: 15, total_assignments: 20, average_execution_progress: 62, overdue_items: 2, escalated_items: 1, read_only: true, generated_at: '2026-06-10T00:00:00Z' });
    mockApi.getProtocolExecution.mockResolvedValue({ tenant_id: 1, total_protocols: 5, average_execution_progress: 62, overdue_items: 2, escalated_items: 1, completion_status: { COMPLETED: 1 }, linkage_inventory: { meeting_registry: 5 }, signal_families: ['protocol_non_execution'], read_only: true, generated_at: '2026-06-10T00:00:00Z' });
  });

  it('renders control tower, KPI center, and risk center', async () => {
    renderWithClient(<ExecutiveGovernanceRuntimeShellPage />);

    expect(await screen.findByTestId('executive-control-tower-runtime')).toBeInTheDocument();
    expect(screen.getByTestId('executive-kpi-center-runtime')).toBeInTheDocument();
    expect(screen.getByTestId('executive-risk-center-runtime')).toBeInTheDocument();
  });

  it('renders rector dashboard and escalation sections', async () => {
    renderWithClient(<ExecutiveGovernanceRuntimeShellPage />);

    expect(await screen.findByTestId('rector-dashboard-runtime')).toBeInTheDocument();
    expect(screen.getByTestId('control-tower-escalation-runtime')).toBeInTheDocument();
    expect(screen.getByTestId('strategic-initiatives-runtime')).toBeInTheDocument();
  });
});
