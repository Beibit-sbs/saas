import React from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const { mockApi } = vi.hoisted(() => ({
  mockApi: {
    getInternshipRuntime: vi.fn(),
  },
}));

vi.mock('@/modules/academic-operations-runtime/api', () => ({ academicOperationsRuntimeApi: mockApi }));

import { InternshipRuntimePage } from '@/modules/academic-operations-runtime/pages';

function renderWithClient(ui: React.ReactNode) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(<QueryClientProvider client={client}>{ui}</QueryClientProvider>);
}

describe('Internship runtime', () => {
  beforeEach(() => {
    mockApi.getInternshipRuntime.mockResolvedValue({
      tenant_id: 1,
      overview: {
        owner_module: 'academic_operations_runtime',
        runtime_scope: 'INTERNSHIP_RUNTIME',
        generated_at: '2026-06-12T00:00:00Z',
        read_only: true,
        aggregator_only: true,
      },
      internship_statistics: {
        participation_rate: 80,
        completion_rate: 62.5,
        active_rate: 55,
        placement_rate: 40,
        total_internships: 20,
        active_internships: 11,
        completed_internships: 9,
        employer_count: 6,
      },
      placement_distribution: {
        by_employer: { 'EMP-1': 5, 'EMP-2': 3 },
        by_industry: { engineering: 6, finance: 2 },
        by_department: { cs: 4, ba: 4 },
        read_only: true,
      },
      completion_summary: {
        completed: 9,
        active: 11,
        overdue: 2,
        read_only: true,
      },
      active_internships: {
        owner_module: 'internship',
        records: 2,
        read_only: true,
        aggregator_only: true,
        source_modules: ['internship', 'academic_operations'],
        items: [
          {
            internship_identifier: 'POST-1',
            employer: 'EMP-1',
            student_count: 3,
            status: 'ACTIVE',
          },
        ],
      },
      employer_engagement: {
        employer_participation_rate: 60,
        repeat_employers: 2,
        placement_volume: 8,
        employer_count: 6,
        read_only: true,
      },
      internship_risk_summary: {
        high_risk_count: 2,
        medium_risk_count: 4,
        low_risk_count: 14,
        read_only: true,
      },
      high_risk_internships: {
        owner_module: 'internship',
        records: 1,
        read_only: true,
        aggregator_only: true,
        source_modules: ['internship', 'brain_core', 'academic_operations'],
        items: [
          {
            internship_identifier: 'POST-5',
            employer: 'EMP-2',
            student_count: 0,
            risk_reason: 'no_participation_detected',
          },
        ],
      },
      internship_signals: {
        generated_signals: 2,
        signal_types: ['AO-SIG-INT-001', 'AO-SIG-INT-002'],
        indicators: ['high_risk_internships_present', 'overdue_internships_detected'],
        read_only: true,
      },
      internship_readiness: {
        readiness_score: 71,
        readiness_classification: 'READY',
        readiness_drivers: ['read_only_runtime', 'aggregator_only_runtime'],
        ready_for_runtime: true,
      },
    });
  });

  it('renders all required internship runtime panels', async () => {
    renderWithClient(<InternshipRuntimePage />);

    expect(await screen.findByTestId('internship-overview-panel')).toBeInTheDocument();
    expect(screen.getByTestId('internship-statistics-panel')).toBeInTheDocument();
    expect(screen.getByTestId('placement-distribution-panel')).toBeInTheDocument();
    expect(screen.getByTestId('completion-summary-panel')).toBeInTheDocument();
    expect(screen.getByTestId('active-internships-panel')).toBeInTheDocument();
    expect(screen.getByTestId('employer-engagement-panel')).toBeInTheDocument();
    expect(screen.getByTestId('internship-risk-panel')).toBeInTheDocument();
    expect(screen.getByTestId('high-risk-internships-panel')).toBeInTheDocument();
    expect(screen.getByTestId('internship-signals-panel')).toBeInTheDocument();
    expect(screen.getByTestId('internship-readiness-panel')).toBeInTheDocument();
  });
});
