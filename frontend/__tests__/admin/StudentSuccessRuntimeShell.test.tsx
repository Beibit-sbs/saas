import React from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const { mockApi } = vi.hoisted(() => ({
  mockApi: {
    getRuntimeShell: vi.fn(),
  },
}));

vi.mock('@/modules/student-success/api', () => ({ studentSuccessApi: mockApi }));

import { StudentSuccessRuntimeShellPage } from '@/modules/student-success/pages';

function renderWithClient(ui: React.ReactNode) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(<QueryClientProvider client={client}>{ui}</QueryClientProvider>);
}

describe('Student Success runtime shell', () => {
  beforeEach(() => {
    mockApi.getRuntimeShell.mockResolvedValue({
      tenant_id: 1,
      owner_module: 'student_success_brain',
      runtime_shell: 'STUDENT_SUCCESS_RUNTIME_SHELL',
      runtime_mode: 'READ_ONLY_AGGREGATOR',
      generated_at: '2026-06-11T00:00:00Z',
      read_only: true,
      aggregator_only: true,
      student_success_overview: {
        owner_module: 'student_success_brain',
        records: 10,
        read_only: true,
        aggregator_only: true,
        source_modules: ['student_lifecycle'],
      },
      lifecycle_summary: {
        owner_module: 'student_lifecycle',
        records: 20,
        read_only: true,
        aggregator_only: true,
        source_modules: ['student_lifecycle'],
      },
      retention_summary: {
        owner_module: 'student_success_brain',
        records: 9,
        read_only: true,
        aggregator_only: true,
        source_modules: ['student_lifecycle', 'student_success_analytics'],
      },
      risk_summary: {
        owner_module: 'student_success_brain',
        records: 7,
        read_only: true,
        aggregator_only: true,
        source_modules: ['academic_operations', 'student_services'],
      },
      intervention_summary: {
        owner_module: 'student_services',
        records: 4,
        read_only: true,
        aggregator_only: true,
        source_modules: ['interventions', 'student_lifecycle'],
      },
      advisor_summary: {
        owner_module: 'student_success_brain',
        records: 3,
        read_only: true,
        aggregator_only: true,
        source_modules: ['student_services'],
      },
      signal_summary: {
        owner_module: 'student_success_brain',
        records: 11,
        read_only: true,
        aggregator_only: true,
        source_modules: ['academic_operations', 'finance', 'career', 'alumni'],
      },
      dashboard_summary: {
        owner_module: 'student_success_brain',
        records: 27,
        read_only: true,
        aggregator_only: true,
        source_modules: ['student_success_brain', 'student_lifecycle', 'reporting_runtime'],
      },
      safety: {
        read_only: true,
        aggregator_only: true,
        tenant_aware: true,
        summary_read_required: true,
        workflow_execution_enabled: false,
        provider_mutation_enabled: false,
        limitations: ['read_only_runtime', 'no_provider_mutation'],
      },
    });
  });

  it('renders runtime shell sections and safety boundaries', async () => {
    renderWithClient(<StudentSuccessRuntimeShellPage />);

    expect(await screen.findByTestId('student-success-runtime-shell')).toBeInTheDocument();
    expect(screen.getByTestId('student-success-overview')).toBeInTheDocument();
    expect(screen.getByTestId('student-success-lifecycle-summary')).toBeInTheDocument();
    expect(screen.getByTestId('student-success-retention-summary')).toBeInTheDocument();
    expect(screen.getByTestId('student-success-risk-summary')).toBeInTheDocument();
    expect(screen.getByTestId('student-success-intervention-summary')).toBeInTheDocument();
    expect(screen.getByTestId('student-success-advisor-summary')).toBeInTheDocument();
    expect(screen.getByTestId('student-success-signal-summary')).toBeInTheDocument();
    expect(screen.getByTestId('student-success-dashboard-summary')).toBeInTheDocument();
    expect(screen.getByTestId('student-success-runtime-safety')).toBeInTheDocument();
    expect(screen.getByText('read_only_runtime')).toBeInTheDocument();
  });
});
