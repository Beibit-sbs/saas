import React from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const { mockApi } = vi.hoisted(() => ({
  mockApi: {
    getStudentRetentionRuntime: vi.fn(),
  },
}));

vi.mock('@/modules/student-success/api', () => ({ studentSuccessApi: mockApi }));

import { StudentRetentionRuntimePage } from '@/modules/student-success/pages';

function renderWithClient(ui: React.ReactNode) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(<QueryClientProvider client={client}>{ui}</QueryClientProvider>);
}

describe('Student Retention runtime', () => {
  beforeEach(() => {
    mockApi.getStudentRetentionRuntime.mockResolvedValue({
      tenant_id: 1,
      owner_module: 'student_success_brain',
      runtime_surface: 'STUDENT_RETENTION_RUNTIME',
      runtime_mode: 'READ_ONLY_AGGREGATOR',
      generated_at: '2026-06-12T00:00:00Z',
      read_only: true,
      aggregator_only: true,
      retention_summary: {
        owner_module: 'student_success_brain',
        records: 20,
        read_only: true,
        aggregator_only: true,
        source_modules: ['student_lifecycle', 'student_success_analytics'],
      },
      retention_score_distribution: {
        owner_module: 'student_success_brain',
        records: 18,
        read_only: true,
        aggregator_only: true,
        source_modules: ['academic_operations'],
      },
      retention_risk_distribution: {
        owner_module: 'student_success_brain',
        records: 14,
        read_only: true,
        aggregator_only: true,
        source_modules: ['student_services'],
      },
      dropout_risk_summary: {
        owner_module: 'student_success_brain',
        records: 11,
        read_only: true,
        aggregator_only: true,
        source_modules: ['interventions'],
      },
      persistence_summary: {
        owner_module: 'student_success_brain',
        records: 17,
        read_only: true,
        aggregator_only: true,
        source_modules: ['student_lifecycle', 'student_services'],
      },
      retention_trend_summary: {
        owner_module: 'student_success_brain',
        records: 16,
        read_only: true,
        aggregator_only: true,
        source_modules: ['reporting_runtime'],
      },
      cohort_retention_summary: {
        owner_module: 'student_success_brain',
        records: 15,
        read_only: true,
        aggregator_only: true,
        source_modules: ['student_lifecycle'],
      },
      retention_signal_summary: {
        owner_module: 'student_success_brain',
        records: 13,
        read_only: true,
        aggregator_only: true,
        source_modules: ['finance', 'career', 'alumni'],
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
        outbound_providers_enabled: false,
        external_integrations_enabled: false,
        limitations: ['read_only_runtime', 'no_external_integrations'],
      },
    });
  });

  it('renders Student Retention panels and runtime safety constraints', async () => {
    renderWithClient(<StudentRetentionRuntimePage />);

    expect(await screen.findByTestId('retention-runtime-panel')).toBeInTheDocument();
    expect(screen.getByTestId('retention-score-panel')).toBeInTheDocument();
    expect(screen.getByTestId('retention-risk-panel')).toBeInTheDocument();
    expect(screen.getByTestId('dropout-risk-panel')).toBeInTheDocument();
    expect(screen.getByTestId('persistence-panel')).toBeInTheDocument();
    expect(screen.getByTestId('retention-trend-panel')).toBeInTheDocument();
    expect(screen.getByTestId('cohort-retention-panel')).toBeInTheDocument();
    expect(screen.getByTestId('student-retention-runtime-safety')).toBeInTheDocument();
    expect(screen.getByText('no_external_integrations')).toBeInTheDocument();
  });
});
