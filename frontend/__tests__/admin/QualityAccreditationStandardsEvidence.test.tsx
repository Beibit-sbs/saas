import React from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const { mockApi } = vi.hoisted(() => ({
  mockApi: {
    listQualityFrameworks: vi.fn(),
    listAccreditationStandards: vi.fn(),
    listStandardCriteria: vi.fn(),
    listStandardsEvidenceRequirements: vi.fn(),
    listQualityEvidence: vi.fn(),
    listEvidenceLimitations: vi.fn(),
  },
}));

vi.mock('@/modules/quality-accreditation/api', () => ({ qualityAccreditationApi: mockApi }));
vi.mock('@/shared/ui/permission-gate', () => ({ RequirePermission: ({ children }: { children: React.ReactNode }) => <>{children}</> }));

import { QualityAccreditationEvidencePage, QualityAccreditationStandardsPage } from '@/modules/quality-accreditation/pages';

function renderWithClient(ui: React.ReactNode) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(<QueryClientProvider client={client}>{ui}</QueryClientProvider>);
}

const baseItem = {
  id: 1,
  tenant_id: 1,
  status: 'ACTIVE',
  metadata: {},
  created_at: '2026-05-25T00:00:00Z',
  updated_at: '2026-05-25T00:00:00Z',
  archived_at: null,
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
  limitations: [],
  read_only_first: true,
  mutation_allowed: false,
};

describe('Quality Accreditation standards and evidence pages', () => {
  beforeEach(() => {
    mockApi.listQualityFrameworks.mockResolvedValue({ items: [{ ...baseItem, framework_ref: 'QF-1', title: 'Quality Framework' }] });
    mockApi.listAccreditationStandards.mockResolvedValue({ items: [{ ...baseItem, standard_ref: 'STD-1', title: 'Institutional Standard' }] });
    mockApi.listStandardCriteria.mockResolvedValue({ items: [{ ...baseItem, criterion_ref: 'CRIT-1', title: 'Criterion A' }] });
    mockApi.listStandardsEvidenceRequirements.mockResolvedValue({ items: [{ ...baseItem, requirement_ref: 'REQ-1', title: 'Evidence Requirement' }] });
    mockApi.listQualityEvidence.mockResolvedValue({ items: [{ ...baseItem, evidence_ref: 'EV-1', title: 'Evidence Record' }] });
    mockApi.listEvidenceLimitations.mockResolvedValue({ items: [{ ...baseItem, limitation_ref: 'LIM-1', title: 'Missing link' }] });
  });

  it('renders standards page framework, criteria, and requirements panels', async () => {
    renderWithClient(<QualityAccreditationStandardsPage />);

    expect(await screen.findByText(/quality framework metadata/i)).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: /accreditation standards/i })).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: /standard criteria/i })).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: /evidence requirements/i })).toBeInTheDocument();
  });

  it('keeps no official approval language visible on the standards page', async () => {
    renderWithClient(<QualityAccreditationStandardsPage />);

    expect((await screen.findAllByText(/official compliance/i)).length).toBeGreaterThan(0);
    expect(screen.getByText(/no official accreditation approval/i)).toBeInTheDocument();
  });

  it('renders evidence page registry and limitations panels', async () => {
    renderWithClient(<QualityAccreditationEvidencePage />);

    expect(await screen.findByText(/quality evidence registry/i)).toBeInTheDocument();
    expect(screen.getByText(/evidence limitations/i)).toBeInTheDocument();
  });

  it('keeps no fake evidence and human review text visible on the evidence page', async () => {
    renderWithClient(<QualityAccreditationEvidencePage />);

    expect((await screen.findAllByText(/reviewed by humans/i)).length).toBeGreaterThan(0);
    expect(screen.getByText(/no fake accreditation evidence/i)).toBeInTheDocument();
  });
});