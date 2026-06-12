import React from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const { mockApi } = vi.hoisted(() => ({
  mockApi: {
    getTimetableRuntime: vi.fn(),
  },
}));

vi.mock('@/modules/academic-operations-runtime/api', () => ({ academicOperationsRuntimeApi: mockApi }));

import { TimetableRuntimePage } from '@/modules/academic-operations-runtime/pages';

function renderWithClient(ui: React.ReactNode) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(<QueryClientProvider client={client}>{ui}</QueryClientProvider>);
}

describe('Timetable runtime', () => {
  beforeEach(() => {
    mockApi.getTimetableRuntime.mockResolvedValue({
      tenant_id: 1,
      overview: {
        owner_module: 'academic_operations_runtime',
        runtime_scope: 'TIMETABLE_RUNTIME',
        generated_at: '2026-06-12T00:00:00Z',
        read_only: true,
        aggregator_only: true,
      },
      timetable_statistics: {
        course_sections_total: 18,
        schedules_total: 25,
        calendar_periods_total: 4,
        rooms_total: 12,
        instructors_total: 14,
        students_total: 220,
        conflicts_total: 3,
        capacity_alerts_total: 2,
        canonical_bridge_total: 6,
      },
      academic_calendar_summary: {
        owner_module: 'academic_calendar',
        records: 4,
        read_only: true,
        aggregator_only: true,
        source_modules: ['academic_calendar', 'scheduling'],
      },
      room_utilization: {
        records: 12,
        utilization_rate: 78,
        underutilized_rooms: 2,
        overloaded_rooms: 1,
        read_only: true,
      },
      instructor_allocation: {
        records: 14,
        assigned_instructors: 13,
        unassigned_sections: 1,
        read_only: true,
      },
      student_schedule_summary: {
        owner_module: 'timetable_management',
        records: 220,
        read_only: true,
        aggregator_only: true,
        source_modules: ['scheduling', 'student_lifecycle'],
      },
      schedule_conflicts: {
        records: 3,
        conflict_rate: 16,
        critical_conflicts: 1,
        read_only: true,
      },
      capacity_indicators: {
        records: 2,
        over_capacity_sections: 2,
        under_capacity_sections: 1,
        read_only: true,
      },
      timetable_health: {
        healthy: false,
        consistency_score: 82,
        issues: ['schedule_conflicts_detected'],
      },
      timetable_readiness: {
        ready_for_runtime: false,
        checklist: ['read_only_runtime', 'aggregator_only_runtime'],
        readiness_score: 79,
      },
    });
  });

  it('renders all required timetable runtime panels', async () => {
    renderWithClient(<TimetableRuntimePage />);

    expect(await screen.findByTestId('timetable-overview-panel')).toBeInTheDocument();
    expect(screen.getByTestId('timetable-statistics-panel')).toBeInTheDocument();
    expect(screen.getByTestId('academic-calendar-panel')).toBeInTheDocument();
    expect(screen.getByTestId('room-utilization-panel')).toBeInTheDocument();
    expect(screen.getByTestId('instructor-allocation-panel')).toBeInTheDocument();
    expect(screen.getByTestId('student-schedule-panel')).toBeInTheDocument();
    expect(screen.getByTestId('schedule-conflicts-panel')).toBeInTheDocument();
    expect(screen.getByTestId('capacity-indicators-panel')).toBeInTheDocument();
    expect(screen.getByTestId('timetable-health-panel')).toBeInTheDocument();
    expect(screen.getByTestId('timetable-readiness-panel')).toBeInTheDocument();
  });
});
