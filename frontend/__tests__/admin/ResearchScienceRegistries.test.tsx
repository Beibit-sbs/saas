import React from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const { mockApi } = vi.hoisted(() => ({
  mockApi: {
    listResearchProjects: vi.fn(),
    listStudentResearchWork: vi.fn(),
    listScientificSupervision: vi.fn(),
    listPublications: vi.fn(),
    listConferences: vi.fn(),
    listGrants: vi.fn(),
    listGrantDeliverables: vi.fn(),
    listEthicsRequests: vi.fn(),
    listEthicsAmendments: vi.fn(),
  },
}));

vi.mock('@/modules/research-science/api', () => ({ researchScienceApi: mockApi }));
vi.mock('@/shared/ui/permission-gate', () => ({ RequirePermission: ({ children }: { children: React.ReactNode }) => <>{children}</> }));

import {
  ConferenceParticipationPage,
  GrantApplicationPage,
  PublicationRegistryPage,
  ResearchEthicsPage,
  ResearchProjectsPage,
  ScientificSupervisionPage,
  StudentResearchWorkPage,
} from '@/modules/research-science/pages';

function renderWithClient(ui: React.ReactNode) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(<QueryClientProvider client={client}>{ui}</QueryClientProvider>);
}

describe('Research Science registries', () => {
  beforeEach(() => {
    mockApi.listResearchProjects.mockResolvedValue({ items: [{ id: 1, tenant_id: 1, status: 'ACTIVE', metadata: {}, created_at: '2026-05-23', updated_at: '2026-05-23', archived_at: null, human_review_required: true, autonomous_decision: false, provider_integration_enabled: false, external_database_sync_enabled: false, official_verification_enabled: false, hidden_score_present: false, incomplete_data: true, limitations: [], project_ref: 'RP-1', department_ref: 'DEP-1', program_ref: 'PRG-1', external_ref: null, title: 'Project One', notes: null }] });
    mockApi.listStudentResearchWork.mockResolvedValue({ items: [{ id: 2, tenant_id: 1, status: 'ACTIVE', metadata: {}, created_at: '2026-05-23', updated_at: '2026-05-23', archived_at: null, human_review_required: true, autonomous_decision: false, provider_integration_enabled: false, external_database_sync_enabled: false, official_verification_enabled: false, hidden_score_present: false, incomplete_data: true, limitations: [], student_ref: 'STU-1', faculty_ref: 'FAC-1', project_ref: 'RP-1', publication_ref: 'PUB-1', conference_ref: 'CONF-1', topic_title: 'Thesis Topic', notes: null }] });
    mockApi.listScientificSupervision.mockResolvedValue({ items: [{ id: 3, tenant_id: 1, status: 'ACTIVE', metadata: {}, created_at: '2026-05-23', updated_at: '2026-05-23', archived_at: null, human_review_required: true, autonomous_decision: false, provider_integration_enabled: false, external_database_sync_enabled: false, official_verification_enabled: false, hidden_score_present: false, incomplete_data: true, limitations: [], student_ref: 'STU-1', faculty_ref: 'FAC-1', project_ref: 'RP-1', supervision_ref: 'SUP-1', notes: null }] });
    mockApi.listPublications.mockResolvedValue({ items: [{ id: 4, tenant_id: 1, status: 'ACTIVE', metadata: {}, created_at: '2026-05-23', updated_at: '2026-05-23', archived_at: null, human_review_required: true, autonomous_decision: false, provider_integration_enabled: false, external_database_sync_enabled: false, official_verification_enabled: false, hidden_score_present: false, incomplete_data: true, limitations: [], publication_ref: 'PUB-1', faculty_ref: 'FAC-1', student_ref: 'STU-1', project_ref: 'RP-1', external_ref: null, title: 'Publication One', fake_publication: false, autonomous_publication_verification_enabled: false }] });
    mockApi.listConferences.mockResolvedValue({ items: [{ id: 5, tenant_id: 1, status: 'ACTIVE', metadata: {}, created_at: '2026-05-23', updated_at: '2026-05-23', archived_at: null, human_review_required: true, autonomous_decision: false, provider_integration_enabled: false, external_database_sync_enabled: false, official_verification_enabled: false, hidden_score_present: false, incomplete_data: true, limitations: [], conference_ref: 'CONF-1', faculty_ref: 'FAC-1', student_ref: 'STU-1', project_ref: 'RP-1', external_ref: null, title: 'Conference One', fake_certificate: false }] });
    mockApi.listGrants.mockResolvedValue({ items: [{ id: 6, tenant_id: 1, status: 'ACTIVE', metadata: {}, created_at: '2026-05-23', updated_at: '2026-05-23', archived_at: null, human_review_required: true, autonomous_decision: false, provider_integration_enabled: false, external_database_sync_enabled: false, official_verification_enabled: false, hidden_score_present: false, incomplete_data: true, limitations: [], grant_ref: 'GR-1', project_ref: 'RP-1', department_ref: 'DEP-1', faculty_ref: 'FAC-1', external_ref: null, title: 'Grant One', fake_grant_evidence: false, autonomous_grant_submission_enabled: false }] });
    mockApi.listGrantDeliverables.mockResolvedValue({ items: [{ id: 7, tenant_id: 1, status: 'ACTIVE', metadata: {}, created_at: '2026-05-23', updated_at: '2026-05-23', archived_at: null, human_review_required: true, autonomous_decision: false, provider_integration_enabled: false, external_database_sync_enabled: false, official_verification_enabled: false, hidden_score_present: false, incomplete_data: true, limitations: [], grant_ref: 'GR-1', project_ref: 'RP-1', external_ref: null, deliverable_ref: 'DEL-1', title: 'Deliverable One', fake_grant_evidence: false, autonomous_grant_submission_enabled: false }] });
    mockApi.listEthicsRequests.mockResolvedValue({ items: [{ id: 8, tenant_id: 1, status: 'ACTIVE', metadata: {}, created_at: '2026-05-23', updated_at: '2026-05-23', archived_at: null, human_review_required: true, autonomous_decision: false, provider_integration_enabled: false, external_database_sync_enabled: false, official_verification_enabled: false, hidden_score_present: false, incomplete_data: true, limitations: [], ethics_ref: 'ETH-1', project_ref: 'RP-1', faculty_ref: 'FAC-1', student_ref: 'STU-1', title: 'Ethics One', autonomous_ethics_approval_enabled: false }] });
    mockApi.listEthicsAmendments.mockResolvedValue({ items: [{ id: 9, tenant_id: 1, status: 'ACTIVE', metadata: {}, created_at: '2026-05-23', updated_at: '2026-05-23', archived_at: null, human_review_required: true, autonomous_decision: false, provider_integration_enabled: false, external_database_sync_enabled: false, official_verification_enabled: false, hidden_score_present: false, incomplete_data: true, limitations: [], ethics_ref: 'ETH-1', project_ref: 'RP-1', external_ref: null, amendment_ref: 'AMD-1', title: 'Amendment One' }] });
  });

  it('renders projects, student research, and supervision pages', async () => {
    renderWithClient(
      <div>
        <ResearchProjectsPage />
        <StudentResearchWorkPage />
        <ScientificSupervisionPage />
      </div>,
    );

    expect(await screen.findByText('Project One')).toBeInTheDocument();
    expect(screen.getByText('Thesis Topic')).toBeInTheDocument();
    expect(screen.getByText('SUP-1')).toBeInTheDocument();
  });

  it('renders publications and conferences without forbidden buttons', async () => {
    renderWithClient(
      <div>
        <PublicationRegistryPage />
        <ConferenceParticipationPage />
      </div>,
    );

    expect(await screen.findByText('Publication One')).toBeInTheDocument();
    expect(screen.getByText('Conference One')).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /fake publication/i })).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /fake certificate/i })).not.toBeInTheDocument();
  });

  it('renders grants and deliverables without forbidden grant evidence actions', async () => {
    renderWithClient(<GrantApplicationPage />);

    expect(await screen.findByText('Grant One')).toBeInTheDocument();
    expect(screen.getByText('Deliverable One')).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /fake grant evidence/i })).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /auto submit grant/i })).not.toBeInTheDocument();
  });

  it('renders ethics requests and amendments without autonomous approval UI', async () => {
    renderWithClient(<ResearchEthicsPage />);

    expect(await screen.findByText('Ethics One')).toBeInTheDocument();
    expect(screen.getByText('Amendment One')).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /auto approve ethics/i })).not.toBeInTheDocument();
  });
});