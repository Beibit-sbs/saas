import React from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const { mockApi } = vi.hoisted(() => ({
  mockApi: {
    getQualityAccreditationHealth: vi.fn(),
    getQualityAccreditationDashboard: vi.fn(),
    getQualityAccreditationMatrixSummary: vi.fn(),
    getQualityAccreditationLimitations: vi.fn(),
  },
}));

vi.mock('@/modules/quality-accreditation/api', () => ({ qualityAccreditationApi: mockApi }));
vi.mock('@/shared/ui/permission-gate', () => ({ RequirePermission: ({ children }: { children: React.ReactNode }) => <>{children}</> }));

import { QualityAccreditationDashboardPage } from '@/modules/quality-accreditation/pages';

function renderWithClient(ui: React.ReactNode) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(<QueryClientProvider client={client}>{ui}</QueryClientProvider>);
}

describe('Quality Accreditation dashboard', () => {
  beforeEach(() => {
    mockApi.getQualityAccreditationHealth.mockResolvedValue({
      tenant_id: 1,
      module: 'quality_accreditation',
      target_level: 'L4',
      foundation_status: 'READY',
      runtime_mode: 'METADATA_EVIDENCE_ONLY',
      contract_version: 'A-038.2',
      provider_integration_enabled: false,
      external_database_sync_enabled: false,
      official_accreditation_approval_enabled: false,
      official_ministry_submission_enabled: false,
      official_ranking_claim_enabled: false,
      hidden_score_present: false,
      fake_metrics: false,
      incomplete_data: true,
      limitations: ['Metadata/evidence-only quality foundation'],
      route_count: 70,
      table_count: 32,
    });
    mockApi.getQualityAccreditationDashboard.mockResolvedValue({
      tenant_id: 1,
      human_review_required: true,
      fake_metrics: false,
      fake_evidence: false,
      official_accreditation_approval_enabled: false,
      official_ministry_submission_enabled: false,
      official_ranking_claim_enabled: false,
      automatic_accreditation_decision_enabled: false,
      provider_integration_enabled: false,
      external_database_sync_enabled: false,
      hidden_score_present: false,
      autonomous_decision: false,
      incomplete_data: true,
      limitations: ['Evidence metadata only'],
      generated_at: '2026-05-25T00:00:00Z',
      contract_version: 'A-038.3',
      source_spec_commit: 'ad2cad9',
      source_product_map_commit: '1253e19',
      source_vertical_selection_commit: '7da0c70',
      master_matrix_commit: 'qa-matrix-1',
      master_matrix_rows: 512,
      detailed_capability_count: 32,
      capability_family_count: 9,
      data_source: 'computed_from_quality_accreditation_metadata',
      frameworks_summary: { ACTIVE: 2 },
      standards_summary: { ACTIVE: 4 },
      evidence_summary: { READY: 6 },
      readiness_summary: { PROGRAM: 3 },
      self_assessment_summary: { DRAFT: 1 },
      improvement_summary: { OPEN: 2 },
      audit_summary: { OPEN: 1 },
      program_review_summary: { PLANNED: 1 },
      bridge_summary: { academic_operations: 2 },
      brain_signal_summary: { review: 1 },
      boundary_summary: { fake_metrics: false },
    });
    mockApi.getQualityAccreditationMatrixSummary.mockResolvedValue({
      contract_version: 'A-038.2',
      source_spec_commit: 'ad2cad9',
      source_product_map_commit: '1253e19',
      source_vertical_selection_commit: '7da0c70',
      master_matrix_commit: 'qa-matrix-1',
      master_matrix_rows: 512,
      detailed_capability_count: 32,
      capability_family_count: 9,
      runtime_mode: 'METADATA_EVIDENCE_ONLY',
      route_count_expected: '65-70 routes expected',
      table_count_expected: 32,
      permission_count_expected: 55,
    });
    mockApi.getQualityAccreditationLimitations.mockResolvedValue({ items: ['No provider integrations implemented.'] });
  });

  it('renders dashboard anchors and fake_metrics=false', async () => {
    renderWithClient(<QualityAccreditationDashboardPage />);

    expect(await screen.findByTestId('quality-accreditation-dashboard')).toBeInTheDocument();
    expect(screen.getAllByText(/fake_metrics/i).length).toBeGreaterThan(0);
    expect(screen.getByText('computed_from_quality_accreditation_metadata')).toBeInTheDocument();
  });

  it('renders backend baseline counts and brain readiness visibility', async () => {
    renderWithClient(<QualityAccreditationDashboardPage />);

    expect(await screen.findByText(/backend baseline counts/i)).toBeInTheDocument();
    expect(screen.getByText('32/70/55')).toBeInTheDocument();
    expect(screen.getByText(/brain readiness signals/i)).toBeInTheDocument();
  });

  it('renders evidence, gap, readiness, and limitations summaries', async () => {
    renderWithClient(<QualityAccreditationDashboardPage />);

    expect(await screen.findByText(/evidence completeness summary/i)).toBeInTheDocument();
    expect(screen.getByText(/standards gap summary/i)).toBeInTheDocument();
    expect(screen.getByText(/readiness summary/i)).toBeInTheDocument();
    expect(screen.getByText(/No provider integrations implemented/i)).toBeInTheDocument();
  });
});