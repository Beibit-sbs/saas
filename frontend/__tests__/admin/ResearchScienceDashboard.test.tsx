import React from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const { mockApi } = vi.hoisted(() => ({
  mockApi: {
    getResearchScienceHealth: vi.fn(),
    getResearchScienceDashboard: vi.fn(),
    getResearchScienceMatrixSummary: vi.fn(),
    getResearchScienceLimitations: vi.fn(),
  },
}));

vi.mock('@/modules/research-science/api', () => ({ researchScienceApi: mockApi }));
vi.mock('@/shared/ui/permission-gate', () => ({ RequirePermission: ({ children }: { children: React.ReactNode }) => <>{children}</> }));

import { ResearchScienceDashboardPage } from '@/modules/research-science/pages';

function renderWithClient(ui: React.ReactNode) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(<QueryClientProvider client={client}>{ui}</QueryClientProvider>);
}

describe('Research Science dashboard', () => {
  beforeEach(() => {
    mockApi.getResearchScienceHealth.mockResolvedValue({
      tenant_id: 1,
      module: 'research_science',
      target_level: 'L4',
      foundation_status: 'READY',
      runtime_mode: 'METADATA_EVIDENCE_ONLY',
      contract_version: 'A-037.2',
      provider_integration_enabled: false,
      external_database_sync_enabled: false,
      official_verification_enabled: false,
      hidden_score_present: false,
      fake_metrics: false,
      incomplete_data: true,
      limitations: ['Metadata-only research foundation'],
      route_count: 43,
      table_count: 15,
    });
    mockApi.getResearchScienceDashboard.mockResolvedValue({
      tenant_id: 1,
      human_review_required: true,
      autonomous_decision: false,
      provider_integration_enabled: false,
      external_database_sync_enabled: false,
      official_verification_enabled: false,
      hidden_score_present: false,
      fake_metrics: false,
      incomplete_data: true,
      limitations: ['Evidence metadata only'],
      generated_at: '2026-05-23T00:00:00Z',
      contract_version: 'A-037.2',
      source_spec_commit: '02b5564',
      master_matrix_commit: 'c79cc31',
      master_matrix_rows: 467,
      capability_count: 60,
      data_source: 'computed_from_research_science_metadata',
      projects_summary: { ACTIVE: 2 },
      student_research_summary: { ACTIVE: 1 },
      supervision_summary: { ACTIVE: 1 },
      publications_summary: { ACTIVE: 3 },
      conferences_summary: { ACTIVE: 1 },
      grants_summary: { ACTIVE: 2 },
      ethics_summary: { ACTIVE: 1 },
      evidence_summary: { ACTIVE: 4 },
      bridge_summary: { academic_operations: 2 },
      brain_readiness_summary: { review: 1 },
      boundary_summary: { fake_metrics: false },
    });
    mockApi.getResearchScienceMatrixSummary.mockResolvedValue({
      contract_version: 'A-037.2',
      source_spec_commit: '02b5564',
      source_product_map_commit: '10d833e',
      master_matrix_commit: 'c79cc31',
      master_matrix_rows: 467,
      capability_count: 60,
      runtime_mode: 'METADATA_EVIDENCE_ONLY',
      autonomy_mode: 'HUMAN_REVIEW_REQUIRED',
      route_count_expected: '38-45 routes expected',
      table_count_expected: 15,
    });
    mockApi.getResearchScienceLimitations.mockResolvedValue({ items: ['No provider integrations implemented.'] });
  });

  it('renders dashboard anchors and fake_metrics=false', async () => {
    renderWithClient(<ResearchScienceDashboardPage />);

    expect(await screen.findByTestId('research-science-dashboard')).toBeInTheDocument();
    expect(screen.getAllByText(/fake_metrics/i).length).toBeGreaterThan(0);
    expect(screen.getByText('c79cc31')).toBeInTheDocument();
    expect(screen.getAllByText('467').length).toBeGreaterThan(0);
  });

  it('renders backend baseline counts and brain readiness visibility', async () => {
    renderWithClient(<ResearchScienceDashboardPage />);

    expect(await screen.findByText(/backend baseline counts/i)).toBeInTheDocument();
    expect(screen.getByText('15')).toBeInTheDocument();
    expect(screen.getByText('43')).toBeInTheDocument();
    expect(screen.getByText('40')).toBeInTheDocument();
    expect(screen.getByText(/brain readiness signals/i)).toBeInTheDocument();
  });

  it('renders limitations and no hidden score boundary text', async () => {
    renderWithClient(<ResearchScienceDashboardPage />);

    expect(await screen.findByText(/no provider integrations implemented/i)).toBeInTheDocument();
    expect(screen.getByText(/hidden score present/i)).toBeInTheDocument();
  });
});