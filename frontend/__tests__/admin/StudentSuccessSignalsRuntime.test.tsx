import React from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const { mockApi } = vi.hoisted(() => ({
  mockApi: {
    getStudentSuccessSignalsRuntime: vi.fn(),
  },
}));

vi.mock('@/modules/student-success/api', () => ({ studentSuccessApi: mockApi }));

import { StudentSuccessSignalsRuntimePage } from '@/modules/student-success/pages';

function renderWithClient(ui: React.ReactNode) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(<QueryClientProvider client={client}>{ui}</QueryClientProvider>);
}

describe('Student Success Signals runtime', () => {
  beforeEach(() => {
    mockApi.getStudentSuccessSignalsRuntime.mockResolvedValue({
      tenant_id: 1,
      owner_module: 'student_success_brain',
      runtime_surface: 'STUDENT_SUCCESS_SIGNALS_RUNTIME',
      runtime_mode: 'READ_ONLY_AGGREGATOR',
      generated_at: '2026-06-12T00:00:00Z',
      read_only: true,
      aggregator_only: true,
      success_signal_summary: {
        owner_module: 'student_success_brain',
        records: 120,
        read_only: true,
        aggregator_only: true,
        source_modules: ['student_success_runtime', 'student_success_analytics', 'brain_core'],
      },
      retention_signals: {
        owner_module: 'student_success_brain',
        records: 20,
        read_only: true,
        aggregator_only: true,
        source_modules: ['student_retention_runtime', 'student_success_analytics'],
      },
      academic_signals: {
        owner_module: 'student_success_brain',
        records: 21,
        read_only: true,
        aggregator_only: true,
        source_modules: ['student_academic_risk_runtime', 'academic_operations'],
      },
      attendance_signals: {
        owner_module: 'student_success_brain',
        records: 19,
        read_only: true,
        aggregator_only: true,
        source_modules: ['student_attendance_risk_runtime', 'attendance_tracking'],
      },
      intervention_signals: {
        owner_module: 'student_success_brain',
        records: 22,
        read_only: true,
        aggregator_only: true,
        source_modules: ['student_intervention_runtime', 'interventions'],
      },
      advisor_signals: {
        owner_module: 'student_success_brain',
        records: 18,
        read_only: true,
        aggregator_only: true,
        source_modules: ['student_advisor_runtime', 'advising'],
      },
      early_warning_signals: {
        owner_module: 'student_success_brain',
        records: 27,
        read_only: true,
        aggregator_only: true,
        source_modules: ['student_retention_runtime', 'student_academic_risk_runtime'],
      },
      success_indicator_signals: {
        owner_module: 'student_success_brain',
        records: 38,
        read_only: true,
        aggregator_only: true,
        source_modules: ['student_success_runtime_shell', 'student_registry_runtime'],
      },
      signal_trend_summary: {
        owner_module: 'student_success_brain',
        records: 41,
        read_only: true,
        aggregator_only: true,
        source_modules: ['student_retention_runtime', 'student_attendance_risk_runtime', 'reporting_runtime'],
      },
      signal_scorecard: {
        owner_module: 'student_success_brain',
        records: 189,
        read_only: true,
        aggregator_only: true,
        source_modules: ['student_success_runtime', 'student_success_analytics', 'reporting_runtime'],
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
        signal_execution_engine_enabled: false,
        persistence_enabled: false,
        limitations: ['read_only_runtime', 'no_signal_execution_engine'],
      },
    });
  });

  it('renders Student Success Signals runtime panels and safety constraints', async () => {
    renderWithClient(<StudentSuccessSignalsRuntimePage />);

    expect(await screen.findByTestId('success-signals-runtime-panel')).toBeInTheDocument();
    expect(screen.getByTestId('signal-summary-panel')).toBeInTheDocument();
    expect(screen.getByTestId('retention-signals-panel')).toBeInTheDocument();
    expect(screen.getByTestId('academic-signals-panel')).toBeInTheDocument();
    expect(screen.getByTestId('attendance-signals-panel')).toBeInTheDocument();
    expect(screen.getByTestId('intervention-signals-panel')).toBeInTheDocument();
    expect(screen.getByTestId('advisor-signals-panel')).toBeInTheDocument();
    expect(screen.getByTestId('early-warning-panel')).toBeInTheDocument();
    expect(screen.getByTestId('success-indicators-panel')).toBeInTheDocument();
    expect(screen.getByTestId('signal-trends-panel')).toBeInTheDocument();
    expect(screen.getByTestId('signal-scorecard-panel')).toBeInTheDocument();
    expect(screen.getByText('no_signal_execution_engine')).toBeInTheDocument();
  });
});
