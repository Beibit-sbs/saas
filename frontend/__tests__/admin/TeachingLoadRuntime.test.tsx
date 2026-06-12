import React from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const { mockApi } = vi.hoisted(() => ({
  mockApi: {
    getTeachingLoadRuntime: vi.fn(),
  },
}));

vi.mock('@/modules/academic-operations-runtime/api', () => ({ academicOperationsRuntimeApi: mockApi }));

import { TeachingLoadRuntimePage } from '@/modules/academic-operations-runtime/pages';

function renderWithClient(ui: React.ReactNode) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(<QueryClientProvider client={client}>{ui}</QueryClientProvider>);
}

describe('Teaching load runtime', () => {
  beforeEach(() => {
    mockApi.getTeachingLoadRuntime.mockResolvedValue({
      tenant_id: 1,
      overview: {
        owner_module: 'academic_operations_runtime',
        runtime_scope: 'TEACHING_LOAD_RUNTIME',
        generated_at: '2026-06-12T00:00:00Z',
        read_only: true,
        aggregator_only: true,
      },
      teaching_load_statistics: {
        tracked_faculty_total: 12,
        department_groups_total: 4,
        high_utilization_total: 3,
        low_utilization_total: 2,
        high_risk_assignments_total: 2,
        teaching_load_signals_total: 3,
        canonical_bridge_total: 7,
      },
      faculty_workload_distribution: {
        evenly_distributed_total: 7,
        overloaded_total: 3,
        underutilized_total: 2,
        fairness_alert_total: 1,
        read_only: true,
      },
      workload_utilization: {
        average_utilization_pct: 0.84,
        median_utilization_pct: 0.81,
        min_utilization_pct: 0.32,
        max_utilization_pct: 1.28,
        utilization_std_dev: 0.19,
        read_only: true,
      },
      overload_risk_summary: {
        risk_score: 55,
        open_risks: 3,
        indicators: ['utilization_above_capacity', 'overload_alerts_present'],
        read_only: true,
      },
      underutilization_summary: {
        owner_module: 'academic_operations',
        records: 2,
        read_only: true,
        aggregator_only: true,
        source_modules: ['faculty', 'teaching_load_contracts'],
      },
      faculty_assignment_health: {
        owner_module: 'academic_operations',
        records: 10,
        read_only: true,
        aggregator_only: true,
        source_modules: ['faculty', 'scheduling'],
      },
      coverage_risk_summary: {
        risk_score: 30,
        open_risks: 2,
        indicators: ['department_distribution_imbalance', 'high_risk_assignment_gap'],
        read_only: true,
      },
      high_risk_assignments: {
        owner_module: 'academic_operations',
        records: 2,
        read_only: true,
        aggregator_only: true,
        source_modules: ['faculty', 'scheduling', 'teaching_load_contracts'],
      },
      teaching_load_signals: {
        generated_signals: 3,
        signal_types: [
          'teaching_load_overload',
          'teaching_load_underutilization',
          'teaching_load_distribution_variance',
        ],
        read_only: true,
      },
      teaching_load_readiness: {
        ready_for_runtime: true,
        checklist: ['read_only_runtime', 'aggregator_only_runtime'],
        readiness_score: 74,
      },
    });
  });

  it('renders all required teaching-load runtime panels', async () => {
    renderWithClient(<TeachingLoadRuntimePage />);

    expect(await screen.findByTestId('teaching-load-overview-panel')).toBeInTheDocument();
    expect(screen.getByTestId('teaching-load-statistics-panel')).toBeInTheDocument();
    expect(screen.getByTestId('faculty-workload-distribution-panel')).toBeInTheDocument();
    expect(screen.getByTestId('workload-utilization-panel')).toBeInTheDocument();
    expect(screen.getByTestId('overload-risk-panel')).toBeInTheDocument();
    expect(screen.getByTestId('underutilization-panel')).toBeInTheDocument();
    expect(screen.getByTestId('faculty-assignment-health-panel')).toBeInTheDocument();
    expect(screen.getByTestId('coverage-risk-panel')).toBeInTheDocument();
    expect(screen.getByTestId('high-risk-assignments-panel')).toBeInTheDocument();
    expect(screen.getByTestId('teaching-load-signals-panel')).toBeInTheDocument();
    expect(screen.getByTestId('teaching-load-readiness-panel')).toBeInTheDocument();
  });
});