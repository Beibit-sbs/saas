import React from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const { mockApi } = vi.hoisted(() => ({
  mockApi: {
    getQualityAccreditationRuntimeShell: vi.fn(),
  },
}));

vi.mock('@/modules/quality-accreditation/api', () => ({ qualityAccreditationApi: mockApi }));
vi.mock('@/shared/ui/permission-gate', () => ({ RequirePermission: ({ children }: { children: React.ReactNode }) => <>{children}</> }));

import { QualityAccreditationRuntimeShellPage } from '@/modules/quality-accreditation/pages';

function renderWithClient(ui: React.ReactNode) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(<QueryClientProvider client={client}>{ui}</QueryClientProvider>);
}

describe('Quality Accreditation runtime shell', () => {
  beforeEach(() => {
    mockApi.getQualityAccreditationRuntimeShell.mockResolvedValue({
      tenant_id: 1,
      owner_module: 'quality_accreditation',
      runtime_shell: 'QUALITY_ACCREDITATION_RUNTIME_SHELL',
      runtime_mode: 'READ_ONLY_AGGREGATOR',
      generated_at: '2026-06-10T00:00:00Z',
      read_only: true,
      aggregator_only: true,
      overview: {
        owner_module: 'quality_accreditation',
        records: 4,
        read_only: true,
        aggregator_only: true,
        source_modules: ['quality_accreditation'],
      },
      readiness: {
        owner_module: 'quality_accreditation',
        records: 7,
        read_only: true,
        aggregator_only: true,
        source_modules: ['quality_accreditation', 'academic_operations'],
      },
      evidence: {
        owner_module: 'quality_accreditation',
        records: 9,
        read_only: true,
        aggregator_only: true,
        source_modules: ['quality_accreditation'],
      },
      risk: {
        owner_module: 'brain_core',
        records: 5,
        read_only: true,
        aggregator_only: true,
        source_modules: ['brain_core', 'quality_accreditation'],
      },
      dashboard: {
        owner_module: 'quality_accreditation',
        records: 12,
        read_only: true,
        aggregator_only: true,
        source_modules: ['quality_accreditation', 'analytics', 'reporting_runtime'],
      },
      safety: {
        read_only: true,
        aggregator_only: true,
        human_review_required: true,
        provider_integration_enabled: false,
        official_accreditation_approval_enabled: false,
        official_ministry_submission_enabled: false,
        official_ranking_claim_enabled: false,
        hidden_score_present: false,
        limitations: ['metadata_only_foundation', 'human_review_required'],
      },
    });
  });

  it('renders all runtime shell sections with required test ids', async () => {
    renderWithClient(<QualityAccreditationRuntimeShellPage />);

    expect(await screen.findByTestId('quality-accreditation-runtime-shell')).toBeInTheDocument();
    expect(screen.getByTestId('quality-accreditation-overview')).toBeInTheDocument();
    expect(screen.getByTestId('quality-accreditation-readiness')).toBeInTheDocument();
    expect(screen.getByTestId('quality-accreditation-evidence')).toBeInTheDocument();
    expect(screen.getByTestId('quality-accreditation-risk')).toBeInTheDocument();
    expect(screen.getByTestId('quality-accreditation-dashboard')).toBeInTheDocument();
  });

  it('shows read-only aggregator safety boundaries', async () => {
    renderWithClient(<QualityAccreditationRuntimeShellPage />);

    expect(await screen.findByText('Runtime safety')).toBeInTheDocument();
    expect(screen.getAllByText('Human review required').length).toBeGreaterThan(0);
    expect(screen.getByTestId('quality-accreditation-runtime-safety')).toBeInTheDocument();
    expect(screen.getByText('brain_core')).toBeInTheDocument();
  });
});
