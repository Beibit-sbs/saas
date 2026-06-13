import React from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const { mockApi } = vi.hoisted(() => ({
  mockApi: {
    getAcademicOperationsDashboardRuntime: vi.fn(),
  },
}));

vi.mock('@/modules/academic-operations-runtime/api', () => ({ academicOperationsRuntimeApi: mockApi }));

import { AcademicOperationsDashboardRuntimePage } from '@/modules/academic-operations-runtime/pages';

function renderWithClient(ui: React.ReactNode) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(<QueryClientProvider client={client}>{ui}</QueryClientProvider>);
}

describe('Academic Operations Dashboard runtime', () => {
  beforeEach(() => {
    mockApi.getAcademicOperationsDashboardRuntime.mockResolvedValue({
      tenant_id: 1,
      overview: {
        owner_module: 'academic_operations_runtime',
        runtime_scope: 'ACADEMIC_OPERATIONS_DASHBOARD_RUNTIME',
        generated_at: '2026-06-13T00:00:00Z',
        read_only: true,
        aggregator_only: true,
      },
      kpi_summary: {
        runtime_slice_count: 9,
        aggregated_records_total: 220,
        high_priority_total: 3,
        recommended_actions_total: 4,
        read_only: true,
      },
      registry_summary: {
        owner_module: 'academic_operations_runtime',
        records: 32,
        read_only: true,
        aggregator_only: true,
        source_modules: ['academic_operations_runtime_shell', 'academic_registry_runtime'],
      },
      curriculum_summary: {
        owner_module: 'academic_operations_runtime',
        records: 28,
        read_only: true,
        aggregator_only: true,
        source_modules: ['curriculum_runtime', 'course_catalog_management', 'prerequisite_management'],
      },
      timetable_summary: {
        owner_module: 'academic_operations_runtime',
        records: 34,
        read_only: true,
        aggregator_only: true,
        source_modules: ['timetable_runtime', 'scheduling'],
      },
      attendance_summary: {
        owner_module: 'academic_operations_runtime',
        records: 29,
        read_only: true,
        aggregator_only: true,
        source_modules: ['attendance_runtime', 'attendance'],
      },
      assessment_summary: {
        owner_module: 'academic_operations_runtime',
        records: 25,
        read_only: true,
        aggregator_only: true,
        source_modules: ['assessment_runtime', 'grades', 'exam_governance'],
      },
      teaching_load_summary: {
        owner_module: 'academic_operations_runtime',
        records: 24,
        read_only: true,
        aggregator_only: true,
        source_modules: ['teaching_load_runtime', 'faculty', 'teaching_load_contracts'],
      },
      internship_summary: {
        owner_module: 'academic_operations_runtime',
        records: 22,
        read_only: true,
        aggregator_only: true,
        source_modules: ['internship_runtime', 'internship'],
      },
      signals_summary: {
        owner_module: 'academic_operations_runtime',
        records: 26,
        read_only: true,
        aggregator_only: true,
        source_modules: ['academic_operations_signals_runtime', 'brain_core'],
      },
      high_priority_items: [
        {
          item_id: 'AO-SIG-001',
          title: 'Curriculum Coverage Risk',
          priority: 'HIGH',
          status: 'ACTION_REQUIRED',
          score: 82,
          domain: 'curriculum',
          source_signal_ids: ['AO-SIG-001'],
          read_only: true,
        },
      ],
      recommended_actions: [
        {
          action_id: 'AO-ACT-001',
          title: 'Mitigate Curriculum Coverage Risk',
          priority: 'HIGH',
          rationale: 'High curriculum risk.',
          source_signal_ids: ['AO-SIG-001'],
        },
      ],
      academic_operations_health_score: {
        composite_score: 68,
        classification: 'WATCH',
        contributing_factors: ['curriculum_consistency=77'],
        read_only: true,
      },
    });
  });

  it('renders all required dashboard runtime panels', async () => {
    renderWithClient(<AcademicOperationsDashboardRuntimePage />);

    expect(await screen.findByTestId('dashboard-overview-panel')).toBeInTheDocument();
    expect(screen.getByTestId('dashboard-kpi-panel')).toBeInTheDocument();
    expect(screen.getByTestId('dashboard-registry-panel')).toBeInTheDocument();
    expect(screen.getByTestId('dashboard-curriculum-panel')).toBeInTheDocument();
    expect(screen.getByTestId('dashboard-timetable-panel')).toBeInTheDocument();
    expect(screen.getByTestId('dashboard-attendance-panel')).toBeInTheDocument();
    expect(screen.getByTestId('dashboard-assessment-panel')).toBeInTheDocument();
    expect(screen.getByTestId('dashboard-teaching-load-panel')).toBeInTheDocument();
    expect(screen.getByTestId('dashboard-internship-panel')).toBeInTheDocument();
    expect(screen.getByTestId('dashboard-signals-panel')).toBeInTheDocument();
    expect(screen.getByTestId('dashboard-priority-panel')).toBeInTheDocument();
    expect(screen.getByTestId('dashboard-actions-panel')).toBeInTheDocument();
    expect(screen.getByTestId('dashboard-health-panel')).toBeInTheDocument();
  });
});
