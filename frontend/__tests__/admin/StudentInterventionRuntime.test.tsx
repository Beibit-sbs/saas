import React from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const { mockApi } = vi.hoisted(() => ({
  mockApi: {
    getStudentInterventionRuntime: vi.fn(),
  },
}));

vi.mock('@/modules/student-success/api', () => ({ studentSuccessApi: mockApi }));

import { StudentInterventionRuntimePage } from '@/modules/student-success/pages';

function renderWithClient(ui: React.ReactNode) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(<QueryClientProvider client={client}>{ui}</QueryClientProvider>);
}

describe('Student Intervention runtime', () => {
  beforeEach(() => {
    mockApi.getStudentInterventionRuntime.mockResolvedValue({
      tenant_id: 1,
      owner_module: 'student_success_brain',
      runtime_surface: 'STUDENT_INTERVENTION_RUNTIME',
      runtime_mode: 'READ_ONLY_AGGREGATOR',
      generated_at: '2026-06-12T00:00:00Z',
      read_only: true,
      aggregator_only: true,
      intervention_summary: {
        owner_module: 'student_success_brain',
        records: 24,
        read_only: true,
        aggregator_only: true,
        source_modules: ['student_lifecycle', 'student_services'],
      },
      intervention_priority_groups: {
        owner_module: 'student_success_brain',
        records: 16,
        read_only: true,
        aggregator_only: true,
        source_modules: ['student_lifecycle', 'student_success_analytics'],
      },
      intervention_recommendations: {
        owner_module: 'student_success_brain',
        records: 13,
        read_only: true,
        aggregator_only: true,
        source_modules: ['academic_operations', 'student_lifecycle', 'student_services'],
      },
      advisor_interventions: {
        owner_module: 'student_success_brain',
        records: 12,
        read_only: true,
        aggregator_only: true,
        source_modules: ['advising', 'student_services', 'interventions'],
      },
      dean_interventions: {
        owner_module: 'student_success_brain',
        records: 10,
        read_only: true,
        aggregator_only: true,
        source_modules: ['academic_operations', 'student_services', 'advising'],
      },
      support_programs: {
        owner_module: 'student_success_brain',
        records: 11,
        read_only: true,
        aggregator_only: true,
        source_modules: ['student_services', 'career_services', 'financial_aid'],
      },
      intervention_effectiveness_signals: {
        owner_module: 'student_success_brain',
        records: 15,
        read_only: true,
        aggregator_only: true,
        source_modules: ['analytics', 'student_services', 'reporting_runtime'],
      },
      intervention_signal_summary: {
        owner_module: 'student_success_brain',
        records: 31,
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
        workflow_execution_enabled: false,
        approval_execution_enabled: false,
        background_jobs_enabled: false,
        notification_execution_enabled: false,
        provider_mutation_enabled: false,
        outbound_integrations_enabled: false,
        intervention_execution_enabled: false,
        limitations: ['read_only_runtime', 'no_intervention_execution'],
      },
    });
  });

  it('renders Student Intervention panels and runtime safety constraints', async () => {
    renderWithClient(<StudentInterventionRuntimePage />);

    expect(await screen.findByTestId('intervention-runtime-panel')).toBeInTheDocument();
    expect(screen.getByTestId('intervention-summary-panel')).toBeInTheDocument();
    expect(screen.getByTestId('intervention-priority-panel')).toBeInTheDocument();
    expect(screen.getByTestId('intervention-recommendations-panel')).toBeInTheDocument();
    expect(screen.getByTestId('advisor-interventions-panel')).toBeInTheDocument();
    expect(screen.getByTestId('dean-interventions-panel')).toBeInTheDocument();
    expect(screen.getByTestId('support-programs-panel')).toBeInTheDocument();
    expect(screen.getByTestId('intervention-effectiveness-panel')).toBeInTheDocument();
    expect(screen.getByTestId('intervention-signal-panel')).toBeInTheDocument();
    expect(screen.getByText('no_intervention_execution')).toBeInTheDocument();
  });
});
