import React from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const { mockApi } = vi.hoisted(() => ({
  mockApi: {
    listInternalQualityAudits: vi.fn(),
    listQualityAuditFindings: vi.fn(),
    listQualityAuditEvents: vi.fn(),
    listQualityStatusHistory: vi.fn(),
    listProgramReviewCycles: vi.fn(),
    listLearningOutcomesAssessments: vi.fn(),
    listStakeholderFeedback: vi.fn(),
    listSurveyQualityMetadata: vi.fn(),
    listAccreditationCommitteeWorkflows: vi.fn(),
    listExternalExpertReviews: vi.fn(),
    listExpertResponsePlans: vi.fn(),
  },
}));

vi.mock('@/modules/quality-accreditation/api', () => ({ qualityAccreditationApi: mockApi }));
vi.mock('@/shared/ui/permission-gate', () => ({ RequirePermission: ({ children }: { children: React.ReactNode }) => <>{children}</> }));

import {
  QualityAccreditationCommitteePage,
  QualityAccreditationExternalReviewPage,
  QualityAccreditationInternalAuditsPage,
  QualityAccreditationLearningOutcomesPage,
  QualityAccreditationProgramReviewPage,
  QualityAccreditationStakeholderFeedbackPage,
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

describe('Quality Accreditation audit and feedback pages', () => {
  beforeEach(() => {
    mockApi.listInternalQualityAudits.mockResolvedValue({ items: [{ ...baseItem, audit_ref: 'AUD-1', title: 'Internal Audit' }] });
    mockApi.listQualityAuditFindings.mockResolvedValue({ items: [{ ...baseItem, finding_ref: 'FIND-1', title: 'Audit Finding' }] });
    mockApi.listQualityAuditEvents.mockResolvedValue({ items: [{ id: 1, tenant_id: 1, event_type: 'REVIEWED', source_entity_type: 'evidence', source_entity_id: 1, actor_user_id: 'user-1', previous_status: 'OPEN', new_status: 'REVIEWED', payload: {}, created_at: '2026-05-25T00:00:00Z', human_review_required: true, provider_integration_enabled: false, hidden_score_present: false }] });
    mockApi.listQualityStatusHistory.mockResolvedValue({ items: [{ id: 1, tenant_id: 1, source_entity_type: 'evidence', source_entity_id: 1, previous_status: 'OPEN', new_status: 'REVIEWED', changed_by_user_id: 'user-1', created_at: '2026-05-25T00:00:00Z', metadata: {} }] });
    mockApi.listProgramReviewCycles.mockResolvedValue({ items: [{ ...baseItem, cycle_ref: 'CYCLE-1', title: 'Program Review Cycle' }] });
    mockApi.listLearningOutcomesAssessments.mockResolvedValue({ items: [{ ...baseItem, assessment_ref: 'ASSMT-1', title: 'Learning Outcome Assessment' }] });
    mockApi.listStakeholderFeedback.mockResolvedValue({ items: [{ ...baseItem, feedback_ref: 'FDB-1', title: 'Stakeholder Feedback' }] });
    mockApi.listSurveyQualityMetadata.mockResolvedValue({ items: [{ ...baseItem, survey_ref: 'SUR-1', title: 'Survey Metadata' }] });
    mockApi.listAccreditationCommitteeWorkflows.mockResolvedValue({ items: [{ ...baseItem, workflow_ref: 'WF-1', title: 'Committee Workflow' }] });
    mockApi.listExternalExpertReviews.mockResolvedValue({ items: [{ ...baseItem, review_ref: 'REV-1', title: 'External Review' }] });
    mockApi.listExpertResponsePlans.mockResolvedValue({ items: [{ ...baseItem, response_plan_ref: 'RESP-1', title: 'Response Plan' }] });
  });

  it('renders the internal audits page with audit and status history panels', async () => {
    renderWithClient(<QualityAccreditationInternalAuditsPage />);

    expect(await screen.findByText(/internal quality audits/i)).toBeInTheDocument();
    expect(screen.getAllByText(/audit findings/i).length).toBeGreaterThan(0);
    expect(screen.getByRole('heading', { name: /audit events/i })).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: /status history/i })).toBeInTheDocument();
  });

  it('renders the program review and learning outcomes pages without automatic closure or grading claims', async () => {
    renderWithClient(<><QualityAccreditationProgramReviewPage /><QualityAccreditationLearningOutcomesPage /></>);

    expect(await screen.findByText(/program review cycles/i)).toBeInTheDocument();
    expect(screen.getByText(/automatic program closure/i)).toBeInTheDocument();
    expect(screen.getAllByText(/automatic grading/i).length).toBeGreaterThan(0);
  });

  it('renders the stakeholder feedback page without fake surveys or hidden scores', async () => {
    renderWithClient(<QualityAccreditationStakeholderFeedbackPage />);

    expect(await screen.findByText(/stakeholder feedback metadata/i)).toBeInTheDocument();
    expect(screen.getByText(/survey quality metadata/i)).toBeInTheDocument();
    expect(screen.getAllByText(/no fake survey results/i).length).toBeGreaterThan(0);
  });

  it('renders committee and external review pages with human-decision and no fake expert approval boundaries', async () => {
    renderWithClient(<><QualityAccreditationCommitteePage /><QualityAccreditationExternalReviewPage /></>);

    expect(await screen.findByText(/committee workflow metadata/i)).toBeInTheDocument();
    expect(screen.getAllByText(/human decisions only/i).length).toBeGreaterThan(0);
    expect(screen.getByText(/external expert reviews/i)).toBeInTheDocument();
    expect(screen.getAllByText(/fake expert approval/i).length).toBeGreaterThan(0);
  });
});