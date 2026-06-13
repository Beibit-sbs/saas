import React from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const { mockApi } = vi.hoisted(() => ({
  mockApi: {
    getAcademicOperationsSignalsRuntime: vi.fn(),
  },
}));

vi.mock('@/modules/academic-operations-runtime/api', () => ({ academicOperationsRuntimeApi: mockApi }));

import { AcademicOperationsSignalsRuntimePage } from '@/modules/academic-operations-runtime/pages';

function renderWithClient(ui: React.ReactNode) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(<QueryClientProvider client={client}>{ui}</QueryClientProvider>);
}

describe('Academic Operations Signals runtime', () => {
  beforeEach(() => {
    mockApi.getAcademicOperationsSignalsRuntime.mockResolvedValue({
      tenant_id: 1,
      overview: {
        owner_module: 'academic_operations_runtime',
        runtime_scope: 'ACADEMIC_OPERATIONS_SIGNALS_RUNTIME',
        generated_at: '2026-06-13T00:00:00Z',
        read_only: true,
        aggregator_only: true,
      },
      signal_summary: {
        total_signals: 10,
        high_priority_total: 3,
        medium_priority_total: 4,
        low_priority_total: 3,
        read_only: true,
      },
      signal_distribution: {
        by_severity: { HIGH: 3, MEDIUM: 4, LOW: 3 },
        by_domain: {
          curriculum: 2,
          timetable: 2,
          attendance: 2,
          assessment: 2,
          teaching_load: 2,
          internship: 2,
        },
        read_only: true,
      },
      high_priority_signals: {
        owner_module: 'academic_operations_runtime',
        records: 3,
        read_only: true,
        aggregator_only: true,
        source_modules: ['academic_operations', 'brain_core'],
        items: [],
      },
      medium_priority_signals: {
        owner_module: 'academic_operations_runtime',
        records: 4,
        read_only: true,
        aggregator_only: true,
        source_modules: ['academic_operations', 'brain_core'],
        items: [],
      },
      low_priority_signals: {
        owner_module: 'academic_operations_runtime',
        records: 3,
        read_only: true,
        aggregator_only: true,
        source_modules: ['academic_operations', 'brain_core'],
        items: [],
      },
      curriculum_signals: {
        owner_module: 'academic_operations_runtime',
        records: 2,
        read_only: true,
        aggregator_only: true,
        source_modules: ['academic_operations', 'curriculum', 'brain_core'],
        items: [],
      },
      timetable_signals: {
        owner_module: 'academic_operations_runtime',
        records: 2,
        read_only: true,
        aggregator_only: true,
        source_modules: ['scheduling', 'academic_operations', 'brain_core'],
        items: [],
      },
      attendance_signals: {
        owner_module: 'academic_operations_runtime',
        records: 2,
        read_only: true,
        aggregator_only: true,
        source_modules: ['attendance', 'academic_operations', 'brain_core'],
        items: [],
      },
      assessment_signals: {
        owner_module: 'academic_operations_runtime',
        records: 2,
        read_only: true,
        aggregator_only: true,
        source_modules: ['academic_operations', 'scheduling', 'brain_core'],
        items: [],
      },
      teaching_load_signals: {
        owner_module: 'academic_operations_runtime',
        records: 2,
        read_only: true,
        aggregator_only: true,
        source_modules: ['faculty', 'academic_operations', 'brain_core'],
        items: [],
      },
      internship_signals: {
        owner_module: 'academic_operations_runtime',
        records: 2,
        read_only: true,
        aggregator_only: true,
        source_modules: ['internship', 'academic_operations', 'brain_core'],
        items: [],
      },
      health_score: {
        composite_score: 66,
        classification: 'WATCH',
        contributing_factors: ['curriculum_risk=82'],
        read_only: true,
      },
      recommended_actions: [
        {
          action_id: 'AO-ACT-001',
          title: 'Mitigate Curriculum Coverage Risk',
          priority: 'HIGH',
          rationale: 'High curriculum risk.',
          source_signal_ids: ['AO-SIG-001'],
        },
      ],
    });
  });

  it('renders all required signals runtime panels', async () => {
    renderWithClient(<AcademicOperationsSignalsRuntimePage />);

    expect(await screen.findByTestId('signals-overview-panel')).toBeInTheDocument();
    expect(screen.getByTestId('signal-summary-panel')).toBeInTheDocument();
    expect(screen.getByTestId('signal-distribution-panel')).toBeInTheDocument();
    expect(screen.getByTestId('high-priority-signals-panel')).toBeInTheDocument();
    expect(screen.getByTestId('medium-priority-signals-panel')).toBeInTheDocument();
    expect(screen.getByTestId('low-priority-signals-panel')).toBeInTheDocument();
    expect(screen.getByTestId('curriculum-signals-panel')).toBeInTheDocument();
    expect(screen.getByTestId('timetable-signals-panel')).toBeInTheDocument();
    expect(screen.getByTestId('attendance-signals-panel')).toBeInTheDocument();
    expect(screen.getByTestId('assessment-signals-panel')).toBeInTheDocument();
    expect(screen.getByTestId('teaching-load-signals-panel')).toBeInTheDocument();
    expect(screen.getByTestId('internship-signals-panel')).toBeInTheDocument();
    expect(screen.getByTestId('health-score-panel')).toBeInTheDocument();
    expect(screen.getByTestId('recommended-actions-panel')).toBeInTheDocument();
  });
});
