import React from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const { mockApi } = vi.hoisted(() => ({
  mockApi: {
    listComplianceGapAnalysis: vi.fn(),
    listAccreditationCalendar: vi.fn(),
    listQualityRisks: vi.fn(),
    listQualityBridges: vi.fn(),
    listQualityBrainSignals: vi.fn(),
    getQualityAccreditationLimitations: vi.fn(),
  },
}));

vi.mock('@/modules/quality-accreditation/api', () => ({ qualityAccreditationApi: mockApi }));
vi.mock('@/shared/ui/permission-gate', () => ({ RequirePermission: ({ children }: { children: React.ReactNode }) => <>{children}</> }));

import {
  QualityAccreditationBridgesPage,
  QualityAccreditationCalendarPage,
  QualityAccreditationGapAnalysisPage,
  QualityAccreditationLimitationsPage,
  QualityAccreditationRiskRegisterPage,
} from '@/modules/quality-accreditation/pages';

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

describe('Quality Accreditation risk and bridges pages', () => {
  beforeEach(() => {
    mockApi.listComplianceGapAnalysis.mockResolvedValue({ items: [{ ...baseItem, gap_ref: 'GAP-1', title: 'Gap Analysis' }] });
    mockApi.listAccreditationCalendar.mockResolvedValue({ items: [{ ...baseItem, calendar_ref: 'CAL-1', title: 'Milestone' }] });
    mockApi.listQualityRisks.mockResolvedValue({ items: [{ ...baseItem, risk_ref: 'RISK-1', title: 'Quality Risk' }] });
    mockApi.listQualityBridges.mockResolvedValue({ items: [{ ...baseItem, bridge_ref: 'BR-1', title: 'Bridge Entry' }] });
    mockApi.listQualityBrainSignals.mockResolvedValue({ items: [{ ...baseItem, signal_ref: 'SIG-1', title: 'Brain Signal' }] });
    mockApi.getQualityAccreditationLimitations.mockResolvedValue({ items: ['Provider integrations are not implemented.'] });
  });

  it('renders gap analysis, calendar, and risk register pages', async () => {
    renderWithClient(<><QualityAccreditationGapAnalysisPage /><QualityAccreditationCalendarPage /><QualityAccreditationRiskRegisterPage /></>);

    expect(await screen.findByText(/compliance gap analysis/i)).toBeInTheDocument();
    expect(screen.getAllByText(/accreditation calendar/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/quality risk register/i).length).toBeGreaterThan(0);
  });

  it('renders bridges and brain signals with read-only-first and no provider sync boundaries', async () => {
    renderWithClient(<QualityAccreditationBridgesPage />);

    expect(await screen.findByText(/quality bridge metadata/i)).toBeInTheDocument();
    expect(screen.getByText(/quality brain signals/i)).toBeInTheDocument();
    expect(screen.getAllByText(/read-only-first bridge/i).length).toBeGreaterThan(0);
    expect(screen.getByText(/no provider sync/i)).toBeInTheDocument();
  });

  it('renders the limitations page with no-overclaim runtime limitations', async () => {
    renderWithClient(<QualityAccreditationLimitationsPage />);

    expect((await screen.findAllByText(/frontend runtime is not production-ready/i)).length).toBeGreaterThan(0);
    expect(screen.getByText(/official accreditation approval is not implemented/i)).toBeInTheDocument();
    expect(screen.getByText(/official ranking improvement claims are not implemented/i)).toBeInTheDocument();
  });

  it('keeps forbidden action copy and no cross-suite mutation visible through limitations and bridge messaging', async () => {
    renderWithClient(<><QualityAccreditationBridgesPage /><QualityAccreditationLimitationsPage /></>);

    expect(await screen.findByText(/No cross-suite mutation or provider sync is allowed by default/i)).toBeInTheDocument();
    expect(screen.getByText(/provider_sync_without_provider/i)).toBeInTheDocument();
    expect(screen.getByText(/external_database_sync/i)).toBeInTheDocument();
  });
});