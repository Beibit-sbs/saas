import React from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const { mockApi } = vi.hoisted(() => ({
  mockApi: {
    getAttendanceRuntime: vi.fn(),
  },
}));

vi.mock('@/modules/academic-operations-runtime/api', () => ({ academicOperationsRuntimeApi: mockApi }));

import { AttendanceRuntimePage } from '@/modules/academic-operations-runtime/pages';

function renderWithClient(ui: React.ReactNode) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(<QueryClientProvider client={client}>{ui}</QueryClientProvider>);
}

describe('Attendance runtime', () => {
  beforeEach(() => {
    mockApi.getAttendanceRuntime.mockResolvedValue({
      tenant_id: 1,
      overview: {
        owner_module: 'academic_operations_runtime',
        runtime_scope: 'ATTENDANCE_RUNTIME',
        generated_at: '2026-06-12T00:00:00Z',
        read_only: true,
        aggregator_only: true,
      },
      attendance_statistics: {
        tracked_students_total: 220,
        tracked_courses_total: 18,
        average_attendance_rate: 84,
        at_risk_students_total: 31,
        intervention_candidates_total: 14,
        trend_windows_total: 3,
        canonical_bridge_total: 5,
      },
      attendance_distribution: {
        excellent_band: 80,
        good_band: 90,
        warning_band: 35,
        critical_band: 15,
        read_only: true,
      },
      attendance_trends: {
        improving_count: 24,
        stable_count: 130,
        declining_count: 31,
        trend_score: 67,
        read_only: true,
      },
      attendance_risk_summary: {
        risk_score: 45,
        open_risks: 2,
        primary_risks: ['critical_absence_population', 'intervention_backlog'],
        read_only: true,
      },
      high_risk_population: {
        owner_module: 'attendance',
        records: 31,
        read_only: true,
        aggregator_only: true,
        source_modules: ['attendance', 'attendance_tracking', 'scheduling'],
      },
      course_attendance_health: {
        owner_module: 'attendance',
        records: 18,
        read_only: true,
        aggregator_only: true,
        source_modules: ['attendance', 'scheduling', 'academic_operations'],
      },
      attendance_intervention_candidates: {
        owner_module: 'attendance',
        records: 14,
        read_only: true,
        aggregator_only: true,
        source_modules: ['attendance_tracking', 'academic_operations'],
      },
      attendance_signals: {
        generated_signals: 23,
        signal_types: ['warning_attendance_drop', 'critical_attendance_risk'],
        read_only: true,
      },
      attendance_readiness: {
        ready_for_runtime: false,
        checklist: ['read_only_runtime', 'aggregator_only_runtime'],
        readiness_score: 71,
      },
    });
  });

  it('renders all required attendance runtime panels', async () => {
    renderWithClient(<AttendanceRuntimePage />);

    expect(await screen.findByTestId('attendance-overview-panel')).toBeInTheDocument();
    expect(screen.getByTestId('attendance-statistics-panel')).toBeInTheDocument();
    expect(screen.getByTestId('attendance-distribution-panel')).toBeInTheDocument();
    expect(screen.getByTestId('attendance-trends-panel')).toBeInTheDocument();
    expect(screen.getByTestId('attendance-risk-summary-panel')).toBeInTheDocument();
    expect(screen.getByTestId('high-risk-population-panel')).toBeInTheDocument();
    expect(screen.getByTestId('course-attendance-health-panel')).toBeInTheDocument();
    expect(screen.getByTestId('attendance-intervention-panel')).toBeInTheDocument();
    expect(screen.getByTestId('attendance-signals-panel')).toBeInTheDocument();
    expect(screen.getByTestId('attendance-readiness-panel')).toBeInTheDocument();
  });
});
