import React from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const { mockApi } = vi.hoisted(() => ({
  mockApi: {
    listProgramReadiness: vi.fn(),
    listInstitutionalReadiness: vi.fn(),
    listSelfAssessmentReports: vi.fn(),
    listSelfAssessmentSections: vi.fn(),
    listQualityImprovementPlans: vi.fn(),
    listQualityImprovementActions: vi.fn(),
  },
}));

vi.mock('@/modules/quality-accreditation/api', () => ({ qualityAccreditationApi: mockApi }));
vi.mock('@/shared/ui/permission-gate', () => ({ RequirePermission: ({ children }: { children: React.ReactNode }) => <>{children}</> }));

import {
  QualityAccreditationImprovementPlansPage,
  QualityAccreditationInstitutionalReadinessPage,
  QualityAccreditationProgramReadinessPage,
  QualityAccreditationSelfAssessmentPage,
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

describe('Quality Accreditation readiness and reports pages', () => {
  beforeEach(() => {
    mockApi.listProgramReadiness.mockResolvedValue({ items: [{ ...baseItem, readiness_ref: 'PR-1', title: 'Program Readiness' }] });
    mockApi.listInstitutionalReadiness.mockResolvedValue({ items: [{ ...baseItem, readiness_ref: 'IR-1', title: 'Institutional Readiness' }] });
    mockApi.listSelfAssessmentReports.mockResolvedValue({ items: [{ ...baseItem, report_ref: 'SAR-1', title: 'Self-Assessment Report' }] });
    mockApi.listSelfAssessmentSections.mockResolvedValue({ items: [{ ...baseItem, section_ref: 'SEC-1', title: 'Section 1' }] });
    mockApi.listQualityImprovementPlans.mockResolvedValue({ items: [{ ...baseItem, plan_ref: 'PLAN-1', title: 'Improvement Plan' }] });
    mockApi.listQualityImprovementActions.mockResolvedValue({ items: [{ ...baseItem, action_ref: 'ACT-1', title: 'Improvement Action' }] });
  });

  it('renders the program readiness page and its no hidden program score boundary', async () => {
    renderWithClient(<QualityAccreditationProgramReadinessPage />);

    expect(await screen.findByRole('heading', { name: /program readiness metadata/i })).toBeInTheDocument();
    expect(screen.getAllByText(/hidden program score/i).length).toBeGreaterThan(0);
  });

  it('renders the institutional readiness page and its no official ministry submission boundary', async () => {
    renderWithClient(<QualityAccreditationInstitutionalReadinessPage />);

    expect(await screen.findByRole('heading', { name: /institutional readiness metadata/i })).toBeInTheDocument();
    expect(screen.getAllByText(/no official ministry submission/i).length).toBeGreaterThan(0);
  });

  it('renders the self-assessment page and its draft internal review boundary', async () => {
    renderWithClient(<QualityAccreditationSelfAssessmentPage />);

    expect(await screen.findByRole('heading', { name: /self-assessment reports/i })).toBeInTheDocument();
    expect(screen.getByText(/draft\/internal review artifacts only/i)).toBeInTheDocument();
  });

  it('renders improvement plans and keeps no autonomous sanction messaging visible', async () => {
    renderWithClient(<QualityAccreditationImprovementPlansPage />);

    expect(await screen.findByRole('heading', { name: /improvement actions/i })).toBeInTheDocument();
    expect(screen.getAllByText(/autonomous sanction/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/automatic program closure/i).length).toBeGreaterThan(0);
  });
});