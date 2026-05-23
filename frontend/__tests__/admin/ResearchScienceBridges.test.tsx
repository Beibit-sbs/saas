import React from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const { mockApi } = vi.hoisted(() => ({
  mockApi: {
    listResearchBridges: vi.fn(),
    getResearchBridgeSummary: vi.fn(),
  },
}));

vi.mock('@/modules/research-science/api', () => ({ researchScienceApi: mockApi }));
vi.mock('@/shared/ui/permission-gate', () => ({ RequirePermission: ({ children }: { children: React.ReactNode }) => <>{children}</> }));

import { ResearchBridgePage } from '@/modules/research-science/pages';

function renderWithClient(ui: React.ReactNode) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(<QueryClientProvider client={client}>{ui}</QueryClientProvider>);
}

describe('Research Science bridges', () => {
  beforeEach(() => {
    mockApi.listResearchBridges.mockResolvedValue({ items: [{ id: 1, tenant_id: 1, status: 'ACTIVE', metadata: {}, created_at: '2026-05-23', updated_at: '2026-05-23', archived_at: null, human_review_required: true, autonomous_decision: false, provider_integration_enabled: false, external_database_sync_enabled: false, official_verification_enabled: false, hidden_score_present: false, incomplete_data: true, limitations: [], bridge_target: 'academic_operations', source_entity_type: 'research_project', source_entity_id: 1, target_reference: 'AO-1', bridge_status: 'ACTIVE', bridge_ref: 'BR-1', read_only_first: true, mutation_allowed: false, provider_sync_enabled: false, external_submission_enabled: false }] });
    mockApi.getResearchBridgeSummary.mockResolvedValue({ tenant_id: 1, bridge_counts: { academic_operations: 1, student_lifecycle: 2 }, read_only_first: true, mutation_allowed: false, provider_sync_enabled: false, external_submission_enabled: false });
  });

  it('renders all bridge cards and the bridge registry', async () => {
    renderWithClient(<ResearchBridgePage />);

    expect(await screen.findByTestId('research-bridges-page')).toBeInTheDocument();
    expect(screen.getByText(/executive governance/i)).toBeInTheDocument();
    expect(screen.getByText(/academic operations/i)).toBeInTheDocument();
    expect(screen.getByText(/integration \/ provider readiness/i)).toBeInTheDocument();
    expect(screen.getByText('AO-1')).toBeInTheDocument();
  });

  it('renders read-only-first and no provider sync states', async () => {
    renderWithClient(<ResearchBridgePage />);

    expect((await screen.findAllByText(/read-only-first/i)).length).toBeGreaterThan(0);
    expect(screen.getAllByText('false').length).toBeGreaterThan(0);
    expect(screen.getAllByText(/provider sync enabled/i).length).toBeGreaterThan(0);
  });

  it('does not expose cross-suite mutation actions', async () => {
    renderWithClient(<ResearchBridgePage />);

    expect((await screen.findAllByText(/bridge metadata/i)).length).toBeGreaterThan(0);
    expect(screen.queryByRole('button', { name: /mutate/i })).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /sync provider/i })).not.toBeInTheDocument();
  });
});