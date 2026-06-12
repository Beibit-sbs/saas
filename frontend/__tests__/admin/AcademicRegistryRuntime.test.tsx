import React from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const { mockApi } = vi.hoisted(() => ({
  mockApi: {
    getAcademicRegistryRuntime: vi.fn(),
  },
}));

vi.mock('@/modules/academic-operations-runtime/api', () => ({ academicOperationsRuntimeApi: mockApi }));

import { AcademicRegistryRuntimePage } from '@/modules/academic-operations-runtime/pages';

function renderWithClient(ui: React.ReactNode) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(<QueryClientProvider client={client}>{ui}</QueryClientProvider>);
}

describe('Academic Registry runtime', () => {
  beforeEach(() => {
    mockApi.getAcademicRegistryRuntime.mockResolvedValue({
      tenant_id: 1,
      overview: {
        owner_module: 'academic_operations_runtime',
        runtime_scope: 'ACADEMIC_REGISTRY_RUNTIME',
        generated_at: '2026-06-12T00:00:00Z',
        read_only: true,
        aggregator_only: true,
      },
      registry_statistics: {
        academic_periods_total: 4,
        academic_groups_total: 9,
        curriculum_registry_total: 7,
        course_catalog_linkage_total: 3,
        student_registry_linkage_total: 12,
        canonical_bridge_total: 2,
      },
      academic_periods: {
        owner_module: 'academic_operations',
        records: 4,
        read_only: true,
        aggregator_only: true,
        source_modules: ['academic_operations'],
      },
      academic_groups: {
        owner_module: 'academic_operations',
        records: 9,
        read_only: true,
        aggregator_only: true,
        source_modules: ['academic_operations'],
      },
      curriculum_linkage: {
        owner_module: 'academic_operations',
        records: 7,
        read_only: true,
        aggregator_only: true,
        source_modules: ['academic_operations', 'course_catalog_management'],
      },
      catalog_linkage: {
        owner_module: 'academic_operations',
        records: 3,
        read_only: true,
        aggregator_only: true,
        source_modules: ['course_catalog_management'],
      },
      sis_status: {
        provider: 'student_information_system_integration',
        status: 'READINESS_ONLY',
        integration_mode: 'READINESS_ONLY',
        ready: true,
        evidence_count: 0,
        read_only: true,
      },
      lms_status: {
        provider: 'learning_management_system_integration',
        status: 'READINESS_ONLY',
        integration_mode: 'READINESS_ONLY',
        ready: true,
        evidence_count: 0,
        read_only: true,
      },
      health: {
        healthy: true,
        consistency_score: 88,
        issues: [],
      },
      readiness: {
        ready_for_runtime: true,
        checklist: ['read_only_runtime', 'aggregator_only_runtime'],
        readiness_score: 90,
      },
    });
  });

  it('renders all required academic registry runtime panels', async () => {
    renderWithClient(<AcademicRegistryRuntimePage />);

    expect(await screen.findByTestId('academic-registry-overview-panel')).toBeInTheDocument();
    expect(screen.getByTestId('academic-registry-statistics-panel')).toBeInTheDocument();
    expect(screen.getByTestId('academic-registry-periods-panel')).toBeInTheDocument();
    expect(screen.getByTestId('academic-registry-groups-panel')).toBeInTheDocument();
    expect(screen.getByTestId('academic-registry-curriculum-panel')).toBeInTheDocument();
    expect(screen.getByTestId('academic-registry-catalog-panel')).toBeInTheDocument();
    expect(screen.getByTestId('academic-registry-sis-panel')).toBeInTheDocument();
    expect(screen.getByTestId('academic-registry-lms-panel')).toBeInTheDocument();
    expect(screen.getByTestId('academic-registry-health-panel')).toBeInTheDocument();
    expect(screen.getByTestId('academic-registry-readiness-panel')).toBeInTheDocument();
  });
});
