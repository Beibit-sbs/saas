import React from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const { mockApi } = vi.hoisted(() => ({
  mockApi: {
    getStudentAdvisorRuntime: vi.fn(),
  },
}));

vi.mock('@/modules/student-success/api', () => ({ studentSuccessApi: mockApi }));

import { StudentAdvisorRuntimePage } from '@/modules/student-success/pages';

function renderWithClient(ui: React.ReactNode) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(<QueryClientProvider client={client}>{ui}</QueryClientProvider>);
}

describe('Student Advisor runtime', () => {
  beforeEach(() => {
    mockApi.getStudentAdvisorRuntime.mockResolvedValue({
      tenant_id: 1,
      owner_module: 'student_success_brain',
      runtime_surface: 'STUDENT_ADVISOR_RUNTIME',
      runtime_mode: 'READ_ONLY_AGGREGATOR',
      generated_at: '2026-06-12T00:00:00Z',
      read_only: true,
      aggregator_only: true,
      advisor_summary: {
        owner_module: 'student_success_brain',
        records: 18,
        read_only: true,
        aggregator_only: true,
        source_modules: ['student_lifecycle', 'advising', 'student_services'],
      },
      advisor_workload_distribution: {
        owner_module: 'student_success_brain',
        records: 12,
        read_only: true,
        aggregator_only: true,
        source_modules: ['advising', 'interventions', 'student_services'],
      },
      advisor_student_assignments: {
        owner_module: 'student_success_brain',
        records: 14,
        read_only: true,
        aggregator_only: true,
        source_modules: ['student_lifecycle', 'advising'],
      },
      advisor_intervention_queue: {
        owner_module: 'student_success_brain',
        records: 11,
        read_only: true,
        aggregator_only: true,
        source_modules: ['interventions', 'student_success_analytics'],
      },
      advisor_follow_up_summary: {
        owner_module: 'student_success_brain',
        records: 13,
        read_only: true,
        aggregator_only: true,
        source_modules: ['student_services', 'advising', 'interventions'],
      },
      advisor_risk_coverage: {
        owner_module: 'student_success_brain',
        records: 15,
        read_only: true,
        aggregator_only: true,
        source_modules: ['academic_operations', 'student_lifecycle', 'student_services'],
      },
      advisor_effectiveness_summary: {
        owner_module: 'student_success_brain',
        records: 17,
        read_only: true,
        aggregator_only: true,
        source_modules: ['analytics', 'advising', 'reporting_runtime'],
      },
      advisor_signal_summary: {
        owner_module: 'student_success_brain',
        records: 29,
        read_only: true,
        aggregator_only: true,
        source_modules: ['brain_core', 'analytics', 'student_lifecycle'],
      },
      safety: {
        read_only: true,
        aggregator_only: true,
        tenant_aware: true,
        summary_read_required: true,
        write_operations_enabled: false,
        intervention_execution_enabled: false,
        workflow_execution_enabled: false,
        approval_execution_enabled: false,
        background_jobs_enabled: false,
        notification_execution_enabled: false,
        provider_mutation_enabled: false,
        outbound_integrations_enabled: false,
        scheduling_engine_enabled: false,
        limitations: ['read_only_runtime', 'no_scheduling_engine'],
      },
    });
  });

  it('renders Student Advisor panels and runtime safety constraints', async () => {
    renderWithClient(<StudentAdvisorRuntimePage />);

    expect(await screen.findByTestId('advisor-runtime-panel')).toBeInTheDocument();
    expect(screen.getByTestId('advisor-summary-panel')).toBeInTheDocument();
    expect(screen.getByTestId('advisor-workload-panel')).toBeInTheDocument();
    expect(screen.getByTestId('advisor-assignment-panel')).toBeInTheDocument();
    expect(screen.getByTestId('advisor-queue-panel')).toBeInTheDocument();
    expect(screen.getByTestId('advisor-followup-panel')).toBeInTheDocument();
    expect(screen.getByTestId('advisor-risk-coverage-panel')).toBeInTheDocument();
    expect(screen.getByTestId('advisor-effectiveness-panel')).toBeInTheDocument();
    expect(screen.getByTestId('advisor-signal-panel')).toBeInTheDocument();
    expect(screen.getByText('no_scheduling_engine')).toBeInTheDocument();
  });
});
