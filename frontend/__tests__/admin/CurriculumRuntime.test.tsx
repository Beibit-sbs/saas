import React from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const { mockApi } = vi.hoisted(() => ({
  mockApi: {
    getCurriculumRuntime: vi.fn(),
  },
}));

vi.mock('@/modules/academic-operations-runtime/api', () => ({ academicOperationsRuntimeApi: mockApi }));

import { CurriculumRuntimePage } from '@/modules/academic-operations-runtime/pages';

function renderWithClient(ui: React.ReactNode) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(<QueryClientProvider client={client}>{ui}</QueryClientProvider>);
}

describe('Curriculum runtime', () => {
  beforeEach(() => {
    mockApi.getCurriculumRuntime.mockResolvedValue({
      tenant_id: 1,
      overview: {
        owner_module: 'academic_operations_runtime',
        runtime_scope: 'CURRICULUM_RUNTIME',
        generated_at: '2026-06-12T00:00:00Z',
        read_only: true,
        aggregator_only: true,
      },
      curriculum_statistics: {
        program_structures_total: 12,
        curriculum_versions_total: 4,
        curriculum_health_score: 92,
        course_catalog_linkage_total: 10,
        prerequisite_chains_total: 7,
        learning_outcomes_total: 15,
        academic_plans_total: 6,
        canonical_bridge_total: 3,
      },
      program_structures: {
        owner_module: 'academic_operations',
        records: 12,
        read_only: true,
        aggregator_only: true,
        source_modules: ['curriculum_management', 'course_catalog_management'],
      },
      curriculum_versions: {
        owner_module: 'academic_operations',
        records: 4,
        read_only: true,
        aggregator_only: true,
        source_modules: ['curriculum_management'],
      },
      curriculum_health: {
        healthy: true,
        consistency_score: 92,
        issues: [],
      },
      course_catalog_linkage: {
        owner_module: 'academic_operations',
        records: 10,
        read_only: true,
        aggregator_only: true,
        source_modules: ['course_catalog_management'],
      },
      prerequisite_chains: {
        owner_module: 'academic_operations',
        records: 7,
        read_only: true,
        aggregator_only: true,
        source_modules: ['prerequisite_management'],
      },
      learning_outcomes_summary: {
        owner_module: 'academic_operations',
        records: 15,
        read_only: true,
        aggregator_only: true,
        source_modules: ['course_learning_outcomes', 'program_learning_outcomes'],
      },
      curriculum_risks: {
        risk_score: 12,
        open_risks: 0,
        indicators: [],
      },
      curriculum_readiness: {
        ready_for_runtime: true,
        checklist: ['read_only_runtime', 'aggregator_only_runtime'],
        readiness_score: 94,
      },
    });
  });

  it('renders all required curriculum runtime panels', async () => {
    renderWithClient(<CurriculumRuntimePage />);

    expect(await screen.findByTestId('curriculum-overview-panel')).toBeInTheDocument();
    expect(screen.getByTestId('curriculum-statistics-panel')).toBeInTheDocument();
    expect(screen.getByTestId('curriculum-program-structures-panel')).toBeInTheDocument();
    expect(screen.getByTestId('curriculum-versions-panel')).toBeInTheDocument();
    expect(screen.getByTestId('curriculum-health-panel')).toBeInTheDocument();
    expect(screen.getByTestId('curriculum-catalog-linkage-panel')).toBeInTheDocument();
    expect(screen.getByTestId('curriculum-prerequisites-panel')).toBeInTheDocument();
    expect(screen.getByTestId('curriculum-learning-outcomes-panel')).toBeInTheDocument();
    expect(screen.getByTestId('curriculum-risks-panel')).toBeInTheDocument();
    expect(screen.getByTestId('curriculum-readiness-panel')).toBeInTheDocument();
  });
});
