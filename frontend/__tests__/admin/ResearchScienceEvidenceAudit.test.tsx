import React from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const { mockApi } = vi.hoisted(() => ({
  mockApi: {
    listResearchEvidence: vi.fn(),
    listResearchAuditEvents: vi.fn(),
  },
}));

vi.mock('@/modules/research-science/api', () => ({ researchScienceApi: mockApi }));
vi.mock('@/shared/ui/permission-gate', () => ({ RequirePermission: ({ children }: { children: React.ReactNode }) => <>{children}</> }));

import { ResearchAuditPage, ResearchEvidencePage } from '@/modules/research-science/pages';

function renderWithClient(ui: React.ReactNode) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(<QueryClientProvider client={client}>{ui}</QueryClientProvider>);
}

describe('Research Science evidence and audit', () => {
  beforeEach(() => {
    mockApi.listResearchEvidence.mockResolvedValue({ items: [{ id: 1, tenant_id: 1, status: 'ACTIVE', metadata: {}, created_at: '2026-05-23', updated_at: '2026-05-23', archived_at: null, human_review_required: true, autonomous_decision: false, provider_integration_enabled: false, external_database_sync_enabled: false, official_verification_enabled: false, hidden_score_present: false, incomplete_data: true, limitations: [], source_entity_type: 'research_project', source_entity_id: 1, evidence_type: 'NOTE', title: 'Evidence One', description: null, reference_uri: null, storage_ref: null, submitted_by_user_id: 'admin', submitted_at: '2026-05-23', verification_status: 'METADATA_ONLY', verified_by_user_id: null, reviewed_at: null, provider_verified: false, official_external_verification: false, fake_evidence: false }] });
    mockApi.listResearchAuditEvents.mockResolvedValue({ items: [{ id: 2, tenant_id: 1, event_type: 'PROJECT_CREATED', source_entity_type: 'research_project', source_entity_id: 1, actor_user_id: 'admin', previous_status: null, new_status: 'DRAFT', payload: {}, request_id: null, created_at: '2026-05-23', human_review_required: true, autonomous_decision: false, provider_integration_enabled: false, hidden_score_present: false }] });
  });

  it('renders evidence metadata-only details', async () => {
    renderWithClient(<ResearchEvidencePage />);

    expect(await screen.findByText('Evidence One')).toBeInTheDocument();
    expect(screen.getByText('NOTE')).toBeInTheDocument();
    expect(screen.getAllByText(/official external verification/i).length).toBeGreaterThan(0);
  });

  it('renders audit events with autonomous_decision=false', async () => {
    renderWithClient(<ResearchAuditPage />);

    expect(await screen.findByText('PROJECT_CREATED')).toBeInTheDocument();
    expect(screen.getAllByText(/autonomous_decision/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText('false').length).toBeGreaterThan(0);
  });

  it('does not render fake evidence or provider verification actions', async () => {
    renderWithClient(
      <div>
        <ResearchEvidencePage />
        <ResearchAuditPage />
      </div>,
    );

    expect(await screen.findByText('Evidence One')).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /fake evidence/i })).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /provider verification/i })).not.toBeInTheDocument();
  });
});