import React from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const { mockApi } = vi.hoisted(() => ({
  mockApi: {
    getStudentAttendanceRiskRuntime: vi.fn(),
  },
}));

vi.mock('@/modules/student-success/api', () => ({ studentSuccessApi: mockApi }));

import { StudentAttendanceRiskRuntimePage } from '@/modules/student-success/pages';

function renderWithClient(ui: React.ReactNode) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(<QueryClientProvider client={client}>{ui}</QueryClientProvider>);
}

describe('Student Attendance Risk runtime', () => {
  beforeEach(() => {
    mockApi.getStudentAttendanceRiskRuntime.mockResolvedValue({
      tenant_id: 1,
      owner_module: 'student_success_brain',
      runtime_surface: 'STUDENT_ATTENDANCE_RISK_RUNTIME',
      runtime_mode: 'READ_ONLY_AGGREGATOR',
      generated_at: '2026-06-12T00:00:00Z',
      read_only: true,
      aggregator_only: true,
      attendance_risk_summary: {
        owner_module: 'student_success_brain',
        records: 23,
        read_only: true,
        aggregator_only: true,
        source_modules: ['student_lifecycle', 'academic_operations'],
      },
      absence_distribution: {
        owner_module: 'student_success_brain',
        records: 14,
        read_only: true,
        aggregator_only: true,
        source_modules: ['student_lifecycle', 'attendance_tracking'],
      },
      chronic_absence_summary: {
        owner_module: 'student_success_brain',
        records: 12,
        read_only: true,
        aggregator_only: true,
        source_modules: ['student_services', 'interventions'],
      },
      missed_class_summary: {
        owner_module: 'student_success_brain',
        records: 11,
        read_only: true,
        aggregator_only: true,
        source_modules: ['academic_operations', 'student_lifecycle'],
      },
      attendance_trend_summary: {
        owner_module: 'student_success_brain',
        records: 13,
        read_only: true,
        aggregator_only: true,
        source_modules: ['student_lifecycle', 'reporting_runtime'],
      },
      punctuality_summary: {
        owner_module: 'student_success_brain',
        records: 9,
        read_only: true,
        aggregator_only: true,
        source_modules: ['academic_operations', 'student_services'],
      },
      engagement_attendance_summary: {
        owner_module: 'student_success_brain',
        records: 10,
        read_only: true,
        aggregator_only: true,
        source_modules: ['student_lifecycle', 'interventions', 'advising'],
      },
      attendance_signal_summary: {
        owner_module: 'student_success_brain',
        records: 28,
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

  it('renders Student Attendance Risk panels and runtime safety constraints', async () => {
    renderWithClient(<StudentAttendanceRiskRuntimePage />);

    expect(await screen.findByTestId('attendance-risk-runtime-panel')).toBeInTheDocument();
    expect(screen.getByTestId('attendance-risk-summary-panel')).toBeInTheDocument();
    expect(screen.getByTestId('absence-distribution-panel')).toBeInTheDocument();
    expect(screen.getByTestId('chronic-absence-panel')).toBeInTheDocument();
    expect(screen.getByTestId('missed-class-panel')).toBeInTheDocument();
    expect(screen.getByTestId('attendance-trend-panel')).toBeInTheDocument();
    expect(screen.getByTestId('punctuality-panel')).toBeInTheDocument();
    expect(screen.getByTestId('attendance-signal-panel')).toBeInTheDocument();
    expect(screen.getByTestId('student-attendance-risk-runtime-safety')).toBeInTheDocument();
    expect(screen.getByText('no_outbound_integrations')).toBeInTheDocument();
  });
});
