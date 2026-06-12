import React from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const { mockApi } = vi.hoisted(() => ({
  mockApi: {
    getAssessmentRuntime: vi.fn(),
  },
}));

vi.mock('@/modules/academic-operations-runtime/api', () => ({ academicOperationsRuntimeApi: mockApi }));

import { AssessmentRuntimePage } from '@/modules/academic-operations-runtime/pages';

function renderWithClient(ui: React.ReactNode) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(<QueryClientProvider client={client}>{ui}</QueryClientProvider>);
}

describe('Assessment runtime', () => {
  beforeEach(() => {
    mockApi.getAssessmentRuntime.mockResolvedValue({
      tenant_id: 1,
      overview: {
        owner_module: 'academic_operations_runtime',
        runtime_scope: 'ASSESSMENT_RUNTIME',
        generated_at: '2026-06-12T00:00:00Z',
        read_only: true,
        aggregator_only: true,
      },
      assessment_statistics: {
        exams_total: 12,
        completed_exams_total: 9,
        gradebook_entries_total: 28,
        grading_distribution_total: 28,
        schedule_alignment_total: 10,
        assessment_signals_total: 6,
        canonical_bridge_total: 8,
      },
      exam_governance_summary: {
        owner_module: 'academic_operations',
        records: 12,
        read_only: true,
        aggregator_only: true,
        source_modules: ['exam_governance', 'academic_operations'],
      },
      gradebook_readiness: {
        owner_module: 'academic_operations',
        records: 28,
        read_only: true,
        aggregator_only: true,
        source_modules: ['grades', 'academic_operations'],
      },
      grading_distribution: {
        excellent_band: 11,
        good_band: 9,
        warning_band: 5,
        critical_band: 3,
        read_only: true,
      },
      assessment_schedule_alignment: {
        owner_module: 'academic_operations',
        records: 10,
        read_only: true,
        aggregator_only: true,
        source_modules: ['scheduling', 'exam_governance', 'academic_operations'],
      },
      assessment_risk_summary: {
        risk_score: 36,
        open_risks: 2,
        indicators: ['exam_completion_gap', 'gradebook_warning'],
        read_only: true,
      },
      high_risk_assessments: {
        owner_module: 'academic_operations',
        records: 4,
        read_only: true,
        aggregator_only: true,
        source_modules: ['exam_governance', 'grades', 'scheduling'],
      },
      assessment_signals: {
        generated_signals: 6,
        signal_types: ['gradebook_warning', 'exam_completion_gap'],
        read_only: true,
      },
      assessment_readiness: {
        ready_for_runtime: false,
        checklist: ['read_only_runtime', 'aggregator_only_runtime'],
        readiness_score: 74,
      },
    });
  });

  it('renders all required assessment runtime panels', async () => {
    renderWithClient(<AssessmentRuntimePage />);

    expect(await screen.findByTestId('assessment-overview-panel')).toBeInTheDocument();
    expect(screen.getByTestId('assessment-statistics-panel')).toBeInTheDocument();
    expect(screen.getByTestId('exam-governance-panel')).toBeInTheDocument();
    expect(screen.getByTestId('gradebook-readiness-panel')).toBeInTheDocument();
    expect(screen.getByTestId('grading-distribution-panel')).toBeInTheDocument();
    expect(screen.getByTestId('assessment-schedule-alignment-panel')).toBeInTheDocument();
    expect(screen.getByTestId('assessment-risk-summary-panel')).toBeInTheDocument();
    expect(screen.getByTestId('high-risk-assessments-panel')).toBeInTheDocument();
    expect(screen.getByTestId('assessment-signals-panel')).toBeInTheDocument();
    expect(screen.getByTestId('assessment-readiness-panel')).toBeInTheDocument();
  });
});
