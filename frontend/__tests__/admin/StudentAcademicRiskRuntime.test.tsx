import React from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const { mockApi } = vi.hoisted(() => ({
  mockApi: {
    getStudentAcademicRiskRuntime: vi.fn(),
  },
}));

vi.mock('@/modules/student-success/api', () => ({ studentSuccessApi: mockApi }));

import { StudentAcademicRiskRuntimePage } from '@/modules/student-success/pages';

function renderWithClient(ui: React.ReactNode) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(<QueryClientProvider client={client}>{ui}</QueryClientProvider>);
}

describe('Student Academic Risk runtime', () => {
  beforeEach(() => {
    mockApi.getStudentAcademicRiskRuntime.mockResolvedValue({
      tenant_id: 1,
      owner_module: 'student_success_brain',
      runtime_surface: 'STUDENT_ACADEMIC_RISK_RUNTIME',
      runtime_mode: 'READ_ONLY_AGGREGATOR',
      generated_at: '2026-06-12T00:00:00Z',
      read_only: true,
      aggregator_only: true,
      academic_risk_summary: {
        owner_module: 'student_success_brain',
        records: 24,
        read_only: true,
        aggregator_only: true,
        source_modules: ['student_lifecycle', 'academic_operations'],
      },
      gpa_risk_distribution: {
        owner_module: 'student_success_brain',
        records: 15,
        read_only: true,
        aggregator_only: true,
        source_modules: ['student_lifecycle', 'academic_operations'],
      },
      failed_course_risk_summary: {
        owner_module: 'student_success_brain',
        records: 12,
        read_only: true,
        aggregator_only: true,
        source_modules: ['student_lifecycle', 'degree_progress'],
      },
      low_performance_summary: {
        owner_module: 'student_success_brain',
        records: 11,
        read_only: true,
        aggregator_only: true,
        source_modules: ['academic_operations', 'student_lifecycle'],
      },
      probation_summary: {
        owner_module: 'student_success_brain',
        records: 9,
        read_only: true,
        aggregator_only: true,
        source_modules: ['student_services', 'student_lifecycle'],
      },
      progression_risk_summary: {
        owner_module: 'student_success_brain',
        records: 14,
        read_only: true,
        aggregator_only: true,
        source_modules: ['degree_progress', 'student_lifecycle'],
      },
      academic_alert_summary: {
        owner_module: 'student_success_brain',
        records: 10,
        read_only: true,
        aggregator_only: true,
        source_modules: ['interventions', 'student_services', 'advising'],
      },
      academic_signal_summary: {
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
        provider_mutation_enabled: false,
        outbound_integrations_enabled: false,
        limitations: ['read_only_runtime', 'no_outbound_integrations'],
      },
    });
  });

  it('renders Student Academic Risk panels and runtime safety constraints', async () => {
    renderWithClient(<StudentAcademicRiskRuntimePage />);

    expect(await screen.findByTestId('academic-risk-runtime-panel')).toBeInTheDocument();
    expect(screen.getByTestId('academic-risk-summary-panel')).toBeInTheDocument();
    expect(screen.getByTestId('gpa-risk-panel')).toBeInTheDocument();
    expect(screen.getByTestId('failed-course-risk-panel')).toBeInTheDocument();
    expect(screen.getByTestId('probation-panel')).toBeInTheDocument();
    expect(screen.getByTestId('progression-risk-panel')).toBeInTheDocument();
    expect(screen.getByTestId('academic-alert-panel')).toBeInTheDocument();
    expect(screen.getByTestId('student-academic-risk-runtime-safety')).toBeInTheDocument();
    expect(screen.getByText('no_outbound_integrations')).toBeInTheDocument();
  });
});
