import React from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const { mockApi } = vi.hoisted(() => ({
  mockApi: {
    getStudentSuccessDashboardRuntime: vi.fn(),
  },
}));

vi.mock('@/modules/student-success/api', () => ({ studentSuccessApi: mockApi }));

import { StudentSuccessDashboardRuntimePage } from '@/modules/student-success/pages';

function renderWithClient(ui: React.ReactNode) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(<QueryClientProvider client={client}>{ui}</QueryClientProvider>);
}

describe('Student Success Dashboard runtime', () => {
  beforeEach(() => {
    mockApi.getStudentSuccessDashboardRuntime.mockResolvedValue({
      tenant_id: 1,
      owner_module: 'student_success_brain',
      runtime_surface: 'STUDENT_SUCCESS_DASHBOARD_RUNTIME',
      runtime_mode: 'READ_ONLY_AGGREGATOR',
      generated_at: '2026-06-12T00:00:00Z',
      read_only: true,
      aggregator_only: true,
      executive_summary: {
        owner_module: 'student_success_brain',
        records: 66,
        read_only: true,
        aggregator_only: true,
        source_modules: ['student_success_runtime_shell', 'student_success_signals_runtime', 'reporting_runtime'],
      },
      student_population: {
        owner_module: 'student_success_brain',
        records: 53,
        read_only: true,
        aggregator_only: true,
        source_modules: ['student_registry_runtime', 'student_lifecycle'],
      },
      retention_overview: {
        owner_module: 'student_success_brain',
        records: 42,
        read_only: true,
        aggregator_only: true,
        source_modules: ['student_retention_runtime', 'student_success_analytics'],
      },
      academic_risk_overview: {
        owner_module: 'student_success_brain',
        records: 39,
        read_only: true,
        aggregator_only: true,
        source_modules: ['student_academic_risk_runtime', 'academic_operations'],
      },
      attendance_risk_overview: {
        owner_module: 'student_success_brain',
        records: 36,
        read_only: true,
        aggregator_only: true,
        source_modules: ['student_attendance_risk_runtime', 'attendance_tracking'],
      },
      intervention_overview: {
        owner_module: 'student_success_brain',
        records: 47,
        read_only: true,
        aggregator_only: true,
        source_modules: ['student_intervention_runtime', 'interventions'],
      },
      advisor_overview: {
        owner_module: 'student_success_brain',
        records: 35,
        read_only: true,
        aggregator_only: true,
        source_modules: ['student_advisor_runtime', 'advising'],
      },
      success_signals: {
        owner_module: 'student_success_brain',
        records: 120,
        read_only: true,
        aggregator_only: true,
        source_modules: ['student_success_signals_runtime', 'student_success_analytics'],
      },
      priority_actions: {
        owner_module: 'student_success_brain',
        records: 74,
        read_only: true,
        aggregator_only: true,
        source_modules: ['student_success_signals_runtime', 'student_intervention_runtime', 'student_advisor_runtime'],
      },
      dashboard_kpis: {
        owner_module: 'student_success_brain',
        records: 385,
        read_only: true,
        aggregator_only: true,
        source_modules: ['student_success_runtime_shell', 'student_success_signals_runtime', 'reporting_runtime'],
      },
      safety: {
        read_only: true,
        aggregator_only: true,
        tenant_aware: true,
        summary_read_required: true,
        write_operations_enabled: false,
        workflow_execution_enabled: false,
        approval_execution_enabled: false,
        background_jobs_enabled: false,
        notification_execution_enabled: false,
        provider_mutation_enabled: false,
        outbound_integrations_enabled: false,
        scheduling_engine_enabled: false,
        persistence_enabled: false,
        limitations: ['read_only_runtime', 'no_scheduling_engine'],
      },
    });
  });

  it('renders Student Success Dashboard panels and KPI visibility', async () => {
    renderWithClient(<StudentSuccessDashboardRuntimePage />);

    expect(await screen.findByTestId('dashboard-summary-panel')).toBeInTheDocument();
    expect(screen.getByTestId('dashboard-kpi-panel')).toBeInTheDocument();
    expect(screen.getByTestId('dashboard-retention-panel')).toBeInTheDocument();
    expect(screen.getByTestId('dashboard-academic-risk-panel')).toBeInTheDocument();
    expect(screen.getByTestId('dashboard-attendance-risk-panel')).toBeInTheDocument();
    expect(screen.getByTestId('dashboard-intervention-panel')).toBeInTheDocument();
    expect(screen.getByTestId('dashboard-advisor-panel')).toBeInTheDocument();
    expect(screen.getByTestId('dashboard-signals-panel')).toBeInTheDocument();
    expect(screen.getByTestId('dashboard-priority-actions-panel')).toBeInTheDocument();
    expect(screen.getByText('no_scheduling_engine')).toBeInTheDocument();
  });
});
