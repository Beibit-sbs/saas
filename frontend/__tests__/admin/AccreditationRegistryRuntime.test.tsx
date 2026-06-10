import React from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const { mockApi } = vi.hoisted(() => ({
  mockApi: {
    getAccreditationRegistry: vi.fn(),
  },
}));

vi.mock('@/modules/quality-accreditation/api', () => ({ qualityAccreditationApi: mockApi }));
vi.mock('@/shared/ui/permission-gate', () => ({ RequirePermission: ({ children }: { children: React.ReactNode }) => <>{children}</> }));

import { QualityAccreditationAccreditationRegistryPage } from '@/modules/quality-accreditation/pages';

function renderWithClient(ui: React.ReactNode) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(<QueryClientProvider client={client}>{ui}</QueryClientProvider>);
}

describe('Accreditation registry runtime', () => {
  beforeEach(() => {
    mockApi.getAccreditationRegistry.mockResolvedValue({
      tenant_id: 1,
      owner_module: 'quality_accreditation',
      runtime_registry: 'ACCREDITATION_REGISTRY_RUNTIME',
      runtime_mode: 'READ_ONLY_AGGREGATOR',
      generated_at: '2026-06-10T00:00:00Z',
      read_only: true,
      aggregator_only: true,
      active_accreditations: [
        {
          accreditation_id: 'ACC-001',
          accreditation_name: 'Institutional Quality Accreditation',
          accreditation_type: 'INSTITUTIONAL',
          accreditation_scope: 'quality_accreditation',
          provider: 'quality_accreditation',
          status: 'ACTIVE_METADATA_ONLY',
          issued_date: '2026-01-01T00:00:00Z',
          expiry_date: '2026-12-30T00:00:00Z',
          readiness_score: 92,
          risk_level: 'LOW',
          read_only: true,
          aggregator_only: true,
        },
        {
          accreditation_id: 'ACC-002',
          accreditation_name: 'Program Accreditation Registry',
          accreditation_type: 'PROGRAM',
          accreditation_scope: 'academic_operations',
          provider: 'academic_operations',
          status: 'REVIEW_REQUIRED',
          issued_date: '2026-02-01T00:00:00Z',
          expiry_date: '2026-06-20T00:00:00Z',
          readiness_score: 48,
          risk_level: 'HIGH',
          read_only: true,
          aggregator_only: true,
        },
      ],
      expiring_accreditations: [
        {
          accreditation_id: 'ACC-002',
          accreditation_name: 'Program Accreditation Registry',
          accreditation_type: 'PROGRAM',
          accreditation_scope: 'academic_operations',
          provider: 'academic_operations',
          status: 'REVIEW_REQUIRED',
          issued_date: '2026-02-01T00:00:00Z',
          expiry_date: '2026-06-20T00:00:00Z',
          readiness_score: 48,
          risk_level: 'HIGH',
          read_only: true,
          aggregator_only: true,
        },
      ],
      accreditation_provider: [
        {
          provider: 'academic_operations',
          accreditation_count: 1,
          active_count: 1,
          expiring_count: 1,
          read_only: true,
          aggregator_only: true,
        },
        {
          provider: 'quality_accreditation',
          accreditation_count: 1,
          active_count: 1,
          expiring_count: 0,
          read_only: true,
          aggregator_only: true,
        },
      ],
      accreditation_status: [
        { status: 'ACTIVE_METADATA_ONLY', accreditation_count: 1, read_only: true, aggregator_only: true },
        { status: 'REVIEW_REQUIRED', accreditation_count: 1, read_only: true, aggregator_only: true },
      ],
      accreditation_readiness: [
        { readiness_band: 'READY', accreditation_count: 1, average_readiness_score: 92, read_only: true, aggregator_only: true },
        { readiness_band: 'NEEDS_ATTENTION', accreditation_count: 1, average_readiness_score: 48, read_only: true, aggregator_only: true },
      ],
      accreditation_risk: [
        { risk_level: 'LOW', accreditation_count: 1, read_only: true, aggregator_only: true },
        { risk_level: 'HIGH', accreditation_count: 1, read_only: true, aggregator_only: true },
      ],
    });
  });

  it('renders the accreditation registry runtime sections and table', async () => {
    renderWithClient(<QualityAccreditationAccreditationRegistryPage />);

    expect(await screen.findByTestId('accreditation-registry-runtime')).toBeInTheDocument();
    expect(screen.getByTestId('accreditation-registry-table')).toBeInTheDocument();
    expect(screen.getByTestId('accreditation-provider-summary')).toBeInTheDocument();
    expect(screen.getByTestId('accreditation-status-summary')).toBeInTheDocument();
    expect(screen.getByTestId('accreditation-readiness-summary')).toBeInTheDocument();
    expect(screen.getByTestId('accreditation-risk-summary')).toBeInTheDocument();
    expect(screen.getByText('Institutional Quality Accreditation')).toBeInTheDocument();
    expect(screen.getAllByText('Program Accreditation Registry').length).toBeGreaterThan(0);
    expect(screen.getAllByText('quality_accreditation').length).toBeGreaterThan(0);
    expect(screen.getAllByText('academic_operations').length).toBeGreaterThan(0);
    expect(screen.getByText('30 Dec 2026')).toBeInTheDocument();
  });

  it('integrates with the accreditation registry API client', async () => {
    renderWithClient(<QualityAccreditationAccreditationRegistryPage />);

    expect(await screen.findByRole('heading', { name: 'Accreditation Registry', level: 1 })).toBeInTheDocument();
    expect(mockApi.getAccreditationRegistry).toHaveBeenCalled();
  });
});
