import React from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const { mockApi } = vi.hoisted(() => ({
  mockApi: {
    useImprovementPlanRuntime: vi.fn(),
  },
}));

vi.mock('@/modules/quality-accreditation/api', () => ({ qualityAccreditationApi: mockApi }));
vi.mock('@/shared/ui/permission-gate', () => ({ RequirePermission: ({ children }: { children: React.ReactNode }) => <>{children}</> }));

import { QualityAccreditationImprovementPlanRuntimePage } from '@/modules/quality-accreditation/pages';

function renderWithClient(ui: React.ReactNode) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(<QueryClientProvider client={client}>{ui}</QueryClientProvider>);
}

describe('Improvement plan runtime', () => {
  beforeEach(() => {
    mockApi.useImprovementPlanRuntime.mockResolvedValue({
      tenant_id: 1,
      owner_module: 'quality_accreditation',
      runtime_registry: 'IMPROVEMENT_PLAN_RUNTIME',
      runtime_mode: 'READ_ONLY_AGGREGATOR',
      generated_at: '2026-06-11T00:00:00Z',
      read_only: true,
      aggregator_only: true,
      improvement_plans: [
        {
          plan_id: 'PLAN-1',
          plan_title: 'Quality Accreditation Improvement Plan',
          accreditation_standard: 'INSTITUTIONAL_QUALITY_STANDARD_SET',
          owner_unit: 'quality_accreditation',
          progress_tracking_status: 'TRACKED',
          completion_percentage: 52,
          initiatives: [
            {
              initiative_id: 'INIT-1',
              initiative_title: 'Curriculum and standards remediation',
              strategic_theme: 'ACADEMIC_QUALITY',
              owner_unit: 'academic_operations',
              status: 'IN_PROGRESS',
              completion_percentage: 67,
              milestones: [
                {
                  milestone_id: 'MS-1',
                  milestone_title: 'Finalize curriculum mapping remediation',
                  due_date: '2026-07-15T00:00:00Z',
                  completion_percentage: 80,
                  status: 'IN_PROGRESS',
                  read_only: true,
                  aggregator_only: true,
                },
              ],
              kpi_targets: [
                {
                  kpi_target_id: 'KPI-1',
                  kpi_name: 'Evidence completeness ratio',
                  baseline_value: 62,
                  target_value: 90,
                  current_value: 78,
                  unit: 'percent',
                  read_only: true,
                  aggregator_only: true,
                },
              ],
              read_only: true,
              aggregator_only: true,
            },
          ],
          roadmaps: [
            {
              roadmap_id: 'ROADMAP-1',
              roadmap_title: 'Accreditation Improvement Roadmap 2026',
              accreditation_cycle: '2026-2027',
              phase: 'EXECUTION',
              initiatives_total: 3,
              initiatives_completed: 1,
              completion_percentage: 46,
              read_only: true,
              aggregator_only: true,
            },
          ],
          forecasts: [
            {
              forecast_id: 'FC-1',
              forecast_type: 'COMPLETION_FORECAST',
              confidence_level: 'MEDIUM',
              projected_completion_date: '2026-11-30T00:00:00Z',
              readiness_forecast_score: 79,
              risk_level: 'MEDIUM',
              read_only: true,
              aggregator_only: true,
            },
          ],
          last_updated: '2026-06-11T00:00:00Z',
          read_only: true,
          aggregator_only: true,
        },
      ],
    });
  });

  it('renders improvement plan runtime sections', async () => {
    renderWithClient(<QualityAccreditationImprovementPlanRuntimePage />);

    expect(await screen.findByTestId('improvement-plan-runtime')).toBeInTheDocument();
    expect(screen.getByTestId('improvement-roadmap-panel')).toBeInTheDocument();
    expect(screen.getByTestId('improvement-milestones-panel')).toBeInTheDocument();
    expect(screen.getByTestId('improvement-kpi-targets-panel')).toBeInTheDocument();
    expect(screen.getByTestId('improvement-progress-panel')).toBeInTheDocument();
    expect(screen.getByTestId('improvement-forecast-panel')).toBeInTheDocument();
    expect(screen.getByText('Accreditation Improvement Roadmap 2026')).toBeInTheDocument();
  });

  it('integrates with improvement runtime API contract', async () => {
    renderWithClient(<QualityAccreditationImprovementPlanRuntimePage />);

    expect(await screen.findByRole('heading', { name: 'Improvement Plan Runtime', level: 1 })).toBeInTheDocument();
    expect(mockApi.useImprovementPlanRuntime).toHaveBeenCalled();
  });
});
