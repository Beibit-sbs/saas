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
    getKpis: vi.fn(),
    getKpiSummary: vi.fn(),
    getKpiPerformance: vi.fn(),
    getKpiRisks: vi.fn(),
    getKpiTrends: vi.fn(),
    getStrategicInitiatives: vi.fn(),
    getStrategicInitiativesSummary: vi.fn(),
    getStrategicInitiativesRisks: vi.fn(),
    getDevelopmentProgram: vi.fn(),
    getDevelopmentProgramSummary: vi.fn(),
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

describe('Executive KPI Performance runtime', () => {
  beforeEach(() => {
    mockApi.getOverview.mockResolvedValue({
      tenant_id: 1,
      owner_module: 'executive_control_tower',
      runtime_boundary: 'UNIFIED_READ_ONLY_RUNTIME_SHELL',
      navigation_entry: '/console/executive-governance',
      canonical_modules: ['executive_control_tower', 'analytics', 'brain_core'],
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
      executive_signals: 14,
      generated_at: '2026-06-10T00:00:00Z',
    });

    mockApi.getSummary.mockResolvedValue({
      tenant_id: 1,
      read_only: true,
      owner_modules: ['executive_control_tower', 'analytics', 'brain_core'],
      executive_assignments: 20,
      executive_decisions: 12,
      executive_protocols: 8,
      executive_meetings: 5,
      overdue_items: 3,
      escalated_items: 2,
      strategic_items: 6,
      executive_signals: 14,
      generated_at: '2026-06-10T00:00:00Z',
    });

    mockApi.getSignals.mockResolvedValue([]);
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
      executive_signals: 14,
      signal_summaries: [],
      rbac_roles: ['rector', 'strategic_office', 'auditor', 'administrator'],
      read_only: true,
      auditability_preserved: true,
      generated_at: '2026-06-10T00:00:00Z',
    });

    mockApi.getDecisions.mockResolvedValue([]);
    mockApi.getDecisionSummary.mockResolvedValue({ tenant_id: 1, entries: [], total_decisions: 0, decision_sources: {}, execution_status_counts: {}, read_only: true, aggregator_only: true, owner_modules: [], generated_at: '2026-06-10T00:00:00Z' });
    mockApi.getDecisionExecution.mockResolvedValue({ tenant_id: 1, total_decisions: 0, execution_status_counts: {}, overdue_items: 0, escalated_items: 0, signal_families: [], read_only: true, aggregator_only: true, generated_at: '2026-06-10T00:00:00Z' });

    mockApi.getAssignments.mockResolvedValue([]);
    mockApi.getAssignmentSummary.mockResolvedValue({ tenant_id: 1, entries: [], total_assignments: 0, active_assignments: 0, completed_assignments: 0, overdue_assignments: 0, escalated_assignments: 0, execution_performance: 0, execution_trend: 'STABLE', read_only: true, aggregator_only: true, owner_modules: [], generated_at: '2026-06-10T00:00:00Z' });
    mockApi.getAssignmentExecution.mockResolvedValue({ tenant_id: 1, total_assignments: 0, execution_status_counts: {}, overdue_assignments: 0, escalated_assignments: 0, execution_performance: 0, execution_trend: 'STABLE', escalation_inventory: {}, escalation_summary: {}, escalation_trends: [], high_risk_assignments: [], signal_families: [], read_only: true, aggregator_only: true, generated_at: '2026-06-10T00:00:00Z' });
    mockApi.getAssignmentRisks.mockResolvedValue({ tenant_id: 1, total_assignments: 0, execution_status_counts: {}, overdue_assignments: 0, escalated_assignments: 0, execution_performance: 0, execution_trend: 'STABLE', escalation_inventory: {}, escalation_summary: {}, escalation_trends: [], high_risk_assignments: [], signal_families: [], read_only: true, aggregator_only: true, generated_at: '2026-06-10T00:00:00Z' });

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
        workload_distribution: {},
        unit_performance: {},
        strategic_initiative_status: {},
        read_only: true,
        aggregator_only: true,
        generated_at: '2026-06-10T00:00:00Z',
      },
      strategic_initiatives: { on_track: 4, at_risk: 2, delayed: 1 },
      executive_risks: { tenant_id: 1, risk_score: 48, risk_distribution: {}, high_risk_assignments: [], high_risk_units: {}, high_risk_initiatives: {}, escalation_hotspots: {}, overdue_hotspots: {}, signal_families: [], read_only: true, aggregator_only: true, generated_at: '2026-06-10T00:00:00Z' },
      kpi_performance: { tenant_id: 1, kpi_score: 68, kpi_distribution: {}, execution_rate: 62, completion_rate: 28, escalation_rate: 14, unit_performance: {}, strategic_initiative_status: {}, signal_families: [], read_only: true, aggregator_only: true, generated_at: '2026-06-10T00:00:00Z' },
      escalation_summary: { overdue_assignments: 1, escalated_assignments: 1, escalation_rate: 14 },
      read_only: true,
      aggregator_only: true,
      generated_at: '2026-06-10T00:00:00Z',
    });
    mockApi.getControlTowerRisks.mockResolvedValue({ tenant_id: 1, risk_score: 48, risk_distribution: {}, high_risk_assignments: [], high_risk_units: {}, high_risk_initiatives: {}, escalation_hotspots: {}, overdue_hotspots: {}, signal_families: [], read_only: true, aggregator_only: true, generated_at: '2026-06-10T00:00:00Z' });
    mockApi.getControlTowerKpis.mockResolvedValue({ tenant_id: 1, kpi_score: 68, kpi_distribution: {}, execution_rate: 62, completion_rate: 28, escalation_rate: 14, unit_performance: {}, strategic_initiative_status: {}, signal_families: [], read_only: true, aggregator_only: true, generated_at: '2026-06-10T00:00:00Z' });
    mockApi.getControlTowerEscalations.mockResolvedValue({ tenant_id: 1, total_decisions: 7, total_protocols: 5, total_assignments: 7, active_assignments: 5, completed_assignments: 2, overdue_assignments: 1, escalated_assignments: 1, execution_rate: 62, completion_rate: 28, escalation_rate: 14, workload_distribution: {}, unit_performance: {}, strategic_initiative_status: {}, read_only: true, aggregator_only: true, generated_at: '2026-06-10T00:00:00Z' });

    mockApi.getKpis.mockResolvedValue([
      {
        kpi_id: 'kpi-1',
        kpi_code: 'KPI-1',
        kpi_name: 'Graduation Performance',
        kpi_owner: 'strategy_office',
        kpi_category: 'ACADEMIC_OUTCOME',
        target_value: 90,
        current_value: 84,
        achievement_percent: 93,
        status: 'ON_TRACK',
        risk_level: 'MEDIUM',
        trend_direction: 'STABLE',
        linked_initiatives: ['INIT-1'],
      },
    ]);
    mockApi.getKpiSummary.mockResolvedValue({
      tenant_id: 1,
      entries: [],
      total_kpis: 6,
      completion_rate: 66,
      achievement_rate: 82,
      deviation_rate: 33,
      risk_rate: 34,
      status_counts: { ON_TRACK: 3, AT_RISK: 2, MISSED: 1, EXCEEDED: 0 },
      owner_modules: ['analytics', 'executive_control_tower'],
      read_only: true,
      aggregator_only: true,
      generated_at: '2026-06-10T00:00:00Z',
    });
    mockApi.getKpiPerformance.mockResolvedValue({
      tenant_id: 1,
      university_performance_score: 82,
      executive_performance_score: 76,
      unit_performance_score: 72,
      strategic_performance_score: 83,
      kpi_completion_rate: 66,
      kpi_risk_rate: 34,
      performance_trend: 'STABLE',
      kpi_achievement_rate: 82,
      kpi_deviation_rate: 33,
      unit_kpi_performance: { strategy_office: 80, academic_affairs: 74 },
      strategic_kpi_alignment: { aligned_kpis: 5, misaligned_kpis: 1, alignment_rate: 83 },
      trend_analysis: { upward: 1, stable: 3, downward: 2 },
      signal_families: ['kpi_drift', 'kpi_deviation', 'performance_decline'],
      read_only: true,
      aggregator_only: true,
      generated_at: '2026-06-10T00:00:00Z',
    });
    mockApi.getKpiRisks.mockResolvedValue({
      tenant_id: 1,
      high_risk_kpis: [],
      missed_kpis: [],
      kpi_deviation_hotspots: { academic_affairs: 2 },
      low_performance_units: { operations_office: 2 },
      strategic_kpi_gaps: { transformation_program: 1 },
      read_only: true,
      aggregator_only: true,
      generated_at: '2026-06-10T00:00:00Z',
    });
    mockApi.getKpiTrends.mockResolvedValue({
      tenant_id: 1,
      trend_direction_counts: { UP: 1, STABLE: 3, DOWN: 2 },
      performance_scores: [],
      trend_analysis: { improving_kpis: 1, declining_kpis: 2, stable_kpis: 3 },
      signal_families: ['kpi_drift', 'performance_decline'],
      read_only: true,
      aggregator_only: true,
      generated_at: '2026-06-10T00:00:00Z',
    });

    mockApi.getStrategicInitiatives.mockResolvedValue([]);
    mockApi.getStrategicInitiativesSummary.mockResolvedValue({
      tenant_id: 1,
      initiatives: [],
      total_initiatives: 8,
      active_initiatives: 5,
      completed_initiatives: 2,
      at_risk_initiatives: 1,
      delayed_initiatives: 1,
      initiative_kpi_coverage: 88,
      kpi_completion_alignment: 81,
      kpi_deviation_visibility: { completion_variance: 12 },
      kpi_ownership_visibility: { strategy_office: 5 },
      roadmap_visibility: { Q1: 2, Q2: 2 },
      strategic_signal_families: ['strategic_drift'],
      rbac_roles: ['admin'],
      read_only: true,
      aggregator_only: true,
      generated_at: '2026-06-10T00:00:00Z',
    });
    mockApi.getStrategicInitiativesRisks.mockResolvedValue({ tenant_id: 1, delayed_initiatives: [], high_risk_initiatives: [], kpi_deviation_hotspots: {}, strategic_bottlenecks: {}, execution_blockers: {}, risk_distribution: {}, strategic_signal_families: [], read_only: true, aggregator_only: true, generated_at: '2026-06-10T00:00:00Z' });

    mockApi.getDevelopmentProgram.mockResolvedValue({ tenant_id: 1, program_name: 'University Transformation Program', program_year: 2026, initiative_count: 8, active_initiatives: 5, completed_initiatives: 2, at_risk_initiatives: 1, delayed_initiatives: 1, overall_progress: 74, strategic_signal_families: [], read_only: true, aggregator_only: true, generated_at: '2026-06-10T00:00:00Z' });
    mockApi.getDevelopmentProgramSummary.mockResolvedValue({ tenant_id: 1, program_name: 'University Transformation Program', program_year: 2026, initiative_count: 8, active_initiatives: 5, completed_initiatives: 2, at_risk_initiatives: 1, delayed_initiatives: 1, overall_progress: 74, strategic_signal_families: [], read_only: true, aggregator_only: true, generated_at: '2026-06-10T00:00:00Z' });

    mockApi.getMeetings.mockResolvedValue([]);
    mockApi.getMeetingSummary.mockResolvedValue({ tenant_id: 1, entries: [], total_meetings: 0, meeting_status_counts: {}, total_protocols: 0, total_decisions: 0, read_only: true, generated_at: '2026-06-10T00:00:00Z' });
    mockApi.getProtocols.mockResolvedValue([]);
    mockApi.getProtocolSummary.mockResolvedValue({ tenant_id: 1, entries: [], total_protocols: 0, protocol_status_counts: {}, total_decisions: 0, total_assignments: 0, average_execution_progress: 0, overdue_items: 0, escalated_items: 0, read_only: true, generated_at: '2026-06-10T00:00:00Z' });
    mockApi.getProtocolExecution.mockResolvedValue({ tenant_id: 1, total_protocols: 0, average_execution_progress: 0, overdue_items: 0, escalated_items: 0, completion_status: {}, linkage_inventory: {}, signal_families: [], read_only: true, generated_at: '2026-06-10T00:00:00Z' });
  });

  it('renders KPI runtime, performance, risk, and trend sections', async () => {
    renderWithClient(<ExecutiveGovernanceRuntimeShellPage />);

    expect(await screen.findByTestId('kpi-center-runtime')).toBeInTheDocument();
    expect(screen.getByTestId('kpi-performance-runtime')).toBeInTheDocument();
    expect(screen.getByTestId('kpi-risk-center-runtime')).toBeInTheDocument();
    expect(screen.getByTestId('kpi-trends-runtime')).toBeInTheDocument();
    expect(screen.getByTestId('strategic-kpi-alignment-runtime')).toBeInTheDocument();

    expect(screen.getByText('Total KPIs: 6')).toBeInTheDocument();
    expect(screen.getByText('University performance score: 82')).toBeInTheDocument();
    expect(screen.getByText('Missed KPIs: 0')).toBeInTheDocument();
    expect(screen.getByText('UP: 1')).toBeInTheDocument();
  });
});
