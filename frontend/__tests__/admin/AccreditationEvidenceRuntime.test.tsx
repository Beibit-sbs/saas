import React from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const { mockApi } = vi.hoisted(() => ({
  mockApi: {
    getAccreditationEvidenceRuntime: vi.fn(),
  },
}));

vi.mock('@/modules/quality-accreditation/api', () => ({ qualityAccreditationApi: mockApi }));
vi.mock('@/shared/ui/permission-gate', () => ({ RequirePermission: ({ children }: { children: React.ReactNode }) => <>{children}</> }));

import { QualityAccreditationAccreditationEvidenceRuntimePage } from '@/modules/quality-accreditation/pages';

function renderWithClient(ui: React.ReactNode) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(<QueryClientProvider client={client}>{ui}</QueryClientProvider>);
}

describe('Accreditation evidence runtime', () => {
  beforeEach(() => {
    mockApi.getAccreditationEvidenceRuntime.mockResolvedValue({
      tenant_id: 1,
      owner_module: 'quality_accreditation',
      runtime_registry: 'ACCREDITATION_EVIDENCE_RUNTIME',
      runtime_mode: 'READ_ONLY_AGGREGATOR',
      generated_at: '2026-06-10T00:00:00Z',
      read_only: true,
      aggregator_only: true,
      evidence_inventory: [
        {
          evidence_id: 'EVID-001',
          evidence_name: 'Curriculum mapping evidence bundle',
          evidence_category: 'CURRICULUM',
          accreditation_standard: 'STD-001',
          accreditation_section: 'CURRICULUM_ALIGNMENT',
          owner_unit: 'academic_operations',
          evidence_status: 'REVIEWED_METADATA_ONLY',
          completeness_score: 94,
          last_updated: '2026-06-09T00:00:00Z',
          risk_level: 'LOW',
          read_only: true,
          aggregator_only: true,
        },
      ],
      evidence_categories: [
        {
          evidence_category: 'CURRICULUM',
          evidence_count: 1,
          average_completeness_score: 94,
          read_only: true,
          aggregator_only: true,
        },
      ],
      evidence_readiness: [
        {
          readiness_band: 'READY',
          evidence_count: 1,
          read_only: true,
          aggregator_only: true,
        },
      ],
      evidence_coverage: [
        {
          coverage_scope: 'STD-001',
          evidence_count: 1,
          covered_count: 1,
          coverage_percent: 100,
          read_only: true,
          aggregator_only: true,
        },
      ],
      evidence_risk: [
        {
          risk_level: 'LOW',
          evidence_count: 1,
          read_only: true,
          aggregator_only: true,
        },
      ],
    });
  });

  it('renders accreditation evidence runtime sections and evidence table', async () => {
    renderWithClient(<QualityAccreditationAccreditationEvidenceRuntimePage />);

    expect(await screen.findByTestId('accreditation-evidence-runtime')).toBeInTheDocument();
    expect(screen.getByTestId('evidence-inventory-table')).toBeInTheDocument();
    expect(screen.getByTestId('evidence-category-summary')).toBeInTheDocument();
    expect(screen.getByTestId('evidence-readiness-summary')).toBeInTheDocument();
    expect(screen.getByTestId('evidence-coverage-summary')).toBeInTheDocument();
    expect(screen.getByTestId('evidence-risk-summary')).toBeInTheDocument();
    expect(screen.getByText('Curriculum mapping evidence bundle')).toBeInTheDocument();
    expect(screen.getAllByText('CURRICULUM').length).toBeGreaterThan(0);
    expect(screen.getByText('09 Jun 2026')).toBeInTheDocument();
  });

  it('integrates with the accreditation evidence runtime API client', async () => {
    renderWithClient(<QualityAccreditationAccreditationEvidenceRuntimePage />);

    expect(await screen.findByRole('heading', { name: 'Accreditation Evidence Runtime', level: 1 })).toBeInTheDocument();
    expect(mockApi.getAccreditationEvidenceRuntime).toHaveBeenCalled();
  });
});
