import React from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const { mockApi } = vi.hoisted(() => ({
  mockApi: {
    getSelfAssessmentRuntime: vi.fn(),
  },
}));

vi.mock('@/modules/quality-accreditation/api', () => ({ qualityAccreditationApi: mockApi }));
vi.mock('@/shared/ui/permission-gate', () => ({ RequirePermission: ({ children }: { children: React.ReactNode }) => <>{children}</> }));

import { QualityAccreditationSelfAssessmentRuntimePage } from '@/modules/quality-accreditation/pages';

function renderWithClient(ui: React.ReactNode) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(<QueryClientProvider client={client}>{ui}</QueryClientProvider>);
}

describe('Self assessment runtime', () => {
  beforeEach(() => {
    mockApi.getSelfAssessmentRuntime.mockResolvedValue({
      tenant_id: 1,
      owner_module: 'quality_accreditation',
      runtime_registry: 'SELF_ASSESSMENT_RUNTIME',
      runtime_mode: 'READ_ONLY_AGGREGATOR',
      generated_at: '2026-06-10T00:00:00Z',
      read_only: true,
      aggregator_only: true,
      standards: [
        {
          standard_id: 'STD-001',
          standard_name: 'Curriculum Quality Standard',
          accreditation_framework: 'NATIONAL_QUALITY_FRAMEWORK',
          readiness_score: 88,
          completion_percentage: 84,
          evidence_coverage: 80,
          gap_count: 1,
          risk_level: 'MEDIUM',
          owner_unit: 'academic_operations',
          last_updated: '2026-06-10T00:00:00Z',
          read_only: true,
          aggregator_only: true,
        },
      ],
      scorecard: {
        standards_total: 1,
        ready_standards: 1,
        average_readiness_score: 88,
        average_completion_percentage: 84,
        average_evidence_coverage: 80,
        high_risk_standards: 0,
        gap_total: 1,
        read_only: true,
        aggregator_only: true,
      },
      readiness_summary: [
        { readiness_band: 'READY', standard_count: 1, average_readiness_score: 88, read_only: true, aggregator_only: true },
      ],
      coverage_summary: [
        { coverage_scope: 'NATIONAL_QUALITY_FRAMEWORK', standard_count: 1, average_evidence_coverage: 80, read_only: true, aggregator_only: true },
      ],
      risk_summary: [
        { risk_level: 'MEDIUM', standard_count: 1, read_only: true, aggregator_only: true },
      ],
    });
  });

  it('renders self-assessment runtime sections and standards table', async () => {
    renderWithClient(<QualityAccreditationSelfAssessmentRuntimePage />);

    expect(await screen.findByTestId('self-assessment-runtime')).toBeInTheDocument();
    expect(screen.getByTestId('self-assessment-standards-table')).toBeInTheDocument();
    expect(screen.getByTestId('self-assessment-readiness-summary')).toBeInTheDocument();
    expect(screen.getByTestId('self-assessment-scorecard')).toBeInTheDocument();
    expect(screen.getByTestId('self-assessment-coverage-summary')).toBeInTheDocument();
    expect(screen.getByTestId('self-assessment-risk-summary')).toBeInTheDocument();
    expect(screen.getByText('Curriculum Quality Standard')).toBeInTheDocument();
  });

  it('integrates with self-assessment runtime API client', async () => {
    renderWithClient(<QualityAccreditationSelfAssessmentRuntimePage />);

    expect(await screen.findByRole('heading', { name: 'Self Assessment Runtime', level: 1 })).toBeInTheDocument();
    expect(mockApi.getSelfAssessmentRuntime).toHaveBeenCalled();
  });
});
