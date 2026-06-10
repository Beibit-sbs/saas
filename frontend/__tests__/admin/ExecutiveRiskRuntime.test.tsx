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
    getRisks: vi.fn(),
    getRiskSummary: vi.fn(),
    getRiskHeatmap: vi.fn(),
    getRiskEscalations: vi.fn(),
    getRiskScore: vi.fn(),
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

describe('Executive Risk runtime', () => {
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
      executive_signals: 16,
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
      executive_signals: 16,
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
      executive_signals: 16,
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

    mockApi.getKpis.mockResolvedValue([]);
    mockApi.getKpiSummary.mockResolvedValue({ tenant_id: 1, entries: [], total_kpis: 0, completion_rate: 0, achievement_rate: 0, deviation_rate: 0, risk_rate: 0, status_counts: {}, owner_modules: [], read_only: true, aggregator_only: true, generated_at: '2026-06-10T00:00:00Z' });
    mockApi.getKpiPerformance.mockResolvedValue({ tenant_id: 1, university_performance_score: 0, executive_performance_score: 0, unit_performance_score: 0, strategic_performance_score: 0, kpi_completion_rate: 0, kpi_risk_rate: 0, performance_trend: 'STABLE', kpi_achievement_rate: 0, kpi_deviation_rate: 0, unit_kpi_performance: {}, strategic_kpi_alignment: {}, trend_analysis: {}, signal_families: [], read_only: true, aggregator_only: true, generated_at: '2026-06-10T00:00:00Z' });
    mockApi.getKpiRisks.mockResolvedValue({ tenant_id: 1, high_risk_kpis: [], missed_kpis: [], kpi_deviation_hotspots: {}, low_performance_units: {}, strategic_kpi_gaps: {}, read_only: true, aggregator_only: true, generated_at: '2026-06-10T00:00:00Z' });
    mockApi.getKpiTrends.mockResolvedValue({ tenant_id: 1, trend_direction_counts: {}, performance_scores: [], trend_analysis: {}, signal_families: [], read_only: true, aggregator_only: true, generated_at: '2026-06-10T00:00:00Z' });

    mockApi.getRisks.mockResolvedValue([
      {
        risk_id: 'ER-01',
        risk_category: 'EXECUTION',
        risk_source: 'assignment_execution',
        risk_title: 'Overdue assignment risk',
        risk_description: 'Execution delay detected',
        risk_owner: 'strategy_office',
        risk_level: 'HIGH',
        probability: 72,
        impact: 75,
        risk_score: 73,
        status: 'ESCALATED',
        trend_direction: 'UP',
        escalation_flag: true,
      },
    ]);
    mockApi.getRiskSummary.mockResolvedValue({
      tenant_id: 1,
      entries: [],
      total_risks: 8,
      risk_distribution: { LOW: 2, MEDIUM: 2, HIGH: 3, CRITICAL: 1 },
      risk_category_breakdown: { EXECUTION: 3, KPI: 2, STRATEGIC: 2, SIGNAL: 1 },
      risk_ownership_visibility: { strategy_office: 3, chief_of_staff: 2 },
      risk_trend_analysis: { UP: 4, STABLE: 2, DOWN: 2 },
      risk_hotspots: { assignment_execution: 3, kpi_runtime: 2, strategic_runtime: 2, escalation_center: 1 },
      executive_risk_score: 61,
      owner_modules: ['rector_assignment_workflow', 'analytics', 'brain_core'],
      read_only: true,
      aggregator_only: true,
      generated_at: '2026-06-10T00:00:00Z',
    });
    mockApi.getRiskHeatmap.mockResolvedValue({
      tenant_id: 1,
      heatmap: {
        '0-24': { LOW: 0, MEDIUM: 0, HIGH: 0, CRITICAL: 0 },
        '25-49': { LOW: 2, MEDIUM: 1, HIGH: 0, CRITICAL: 0 },
        '50-74': { LOW: 0, MEDIUM: 1, HIGH: 2, CRITICAL: 0 },
        '75-100': { LOW: 0, MEDIUM: 0, HIGH: 1, CRITICAL: 1 },
      },
      risk_distribution: { LOW: 2, MEDIUM: 2, HIGH: 3, CRITICAL: 1 },
      risk_hotspots: { assignment_execution: 3 },
      read_only: true,
      aggregator_only: true,
      generated_at: '2026-06-10T00:00:00Z',
    });
    mockApi.getRiskEscalations.mockResolvedValue({
      tenant_id: 1,
      high_risk_items: [{
        risk_id: 'ER-01',
        risk_category: 'EXECUTION',
        risk_source: 'assignment_execution',
        risk_title: 'Overdue assignment risk',
        risk_description: 'Execution delay detected',
        risk_owner: 'strategy_office',
        risk_level: 'HIGH',
        probability: 72,
        impact: 75,
        risk_score: 73,
        status: 'ESCALATED',
        trend_direction: 'UP',
        escalation_flag: true,
      }],
      critical_risks: [],
      escalating_risks: [],
      overdue_risks: [],
      risk_hotspots: { assignment_execution: 2 },
      signal_families: ['escalation_risk', 'kpi_drift', 'accreditation_risk'],
      read_only: true,
      aggregator_only: true,
      generated_at: '2026-06-10T00:00:00Z',
    });
    mockApi.getRiskScore.mockResolvedValue({
      tenant_id: 1,
      executive_risk_score: 61,
      risk_band: 'ELEVATED',
      high_risk_items: 4,
      critical_risks: 1,
      escalating_risks: 2,
      overdue_risks: 2,
      trend_direction: 'UP',
      read_only: true,
      aggregator_only: true,
      generated_at: '2026-06-10T00:00:00Z',
    });

    mockApi.getStrategicInitiatives.mockResolvedValue([]);
    mockApi.getStrategicInitiativesSummary.mockResolvedValue({ tenant_id: 1, initiatives: [], total_initiatives: 0, active_initiatives: 0, completed_initiatives: 0, at_risk_initiatives: 0, delayed_initiatives: 0, initiative_kpi_coverage: 0, kpi_completion_alignment: 0, kpi_deviation_visibility: {}, kpi_ownership_visibility: {}, roadmap_visibility: {}, strategic_signal_families: [], rbac_roles: [], read_only: true, aggregator_only: true, generated_at: '2026-06-10T00:00:00Z' });
    mockApi.getStrategicInitiativesRisks.mockResolvedValue({ tenant_id: 1, delayed_initiatives: [], high_risk_initiatives: [], kpi_deviation_hotspots: {}, strategic_bottlenecks: {}, execution_blockers: {}, risk_distribution: {}, strategic_signal_families: [], read_only: true, aggregator_only: true, generated_at: '2026-06-10T00:00:00Z' });

    mockApi.getDevelopmentProgram.mockResolvedValue({ tenant_id: 1, program_name: 'University Transformation Program', program_year: 2026, initiative_count: 0, active_initiatives: 0, completed_initiatives: 0, at_risk_initiatives: 0, delayed_initiatives: 0, overall_progress: 0, strategic_signal_families: [], read_only: true, aggregator_only: true, generated_at: '2026-06-10T00:00:00Z' });
    mockApi.getDevelopmentProgramSummary.mockResolvedValue({ tenant_id: 1, program_name: 'University Transformation Program', program_year: 2026, initiative_count: 0, active_initiatives: 0, completed_initiatives: 0, at_risk_initiatives: 0, delayed_initiatives: 0, overall_progress: 0, strategic_signal_families: [], read_only: true, aggregator_only: true, generated_at: '2026-06-10T00:00:00Z' });

    mockApi.getMeetings.mockResolvedValue([]);
    mockApi.getMeetingSummary.mockResolvedValue({ tenant_id: 1, entries: [], total_meetings: 0, meeting_status_counts: {}, total_protocols: 0, total_decisions: 0, read_only: true, generated_at: '2026-06-10T00:00:00Z' });
    mockApi.getProtocols.mockResolvedValue([]);
    mockApi.getProtocolSummary.mockResolvedValue({ tenant_id: 1, entries: [], total_protocols: 0, protocol_status_counts: {}, total_decisions: 0, total_assignments: 0, average_execution_progress: 0, overdue_items: 0, escalated_items: 0, read_only: true, generated_at: '2026-06-10T00:00:00Z' });
    mockApi.getProtocolExecution.mockResolvedValue({ tenant_id: 1, total_protocols: 0, average_execution_progress: 0, overdue_items: 0, escalated_items: 0, completion_status: {}, linkage_inventory: {}, signal_families: [], read_only: true, generated_at: '2026-06-10T00:00:00Z' });
  });

  it('renders executive risk center, heatmap, analytics, score, and hotspots', async () => {
    renderWithClient(<ExecutiveGovernanceRuntimeShellPage />);

    expect(await screen.findByTestId('executive-risk-runtime-center')).toBeInTheDocument();
    expect(screen.getByTestId('risk-heatmap-runtime')).toBeInTheDocument();
    expect(screen.getByTestId('risk-analytics-runtime')).toBeInTheDocument();
    expect(screen.getByTestId('executive-risk-score-runtime')).toBeInTheDocument();
    expect(screen.getByTestId('risk-hotspots-runtime')).toBeInTheDocument();

    expect(screen.getByText('Total risks: 8')).toBeInTheDocument();
    expect(screen.getByText('Score: 61')).toBeInTheDocument();
    expect(screen.getByText('Band: ELEVATED')).toBeInTheDocument();
    expect(screen.getByText('assignment_execution: 3')).toBeInTheDocument();
  });
});
