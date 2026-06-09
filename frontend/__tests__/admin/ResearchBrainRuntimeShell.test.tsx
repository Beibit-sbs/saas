import React from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const { mockApi } = vi.hoisted(() => ({
  mockApi: {
    getShell: vi.fn(),
    getOrchestration: vi.fn(),
    getContext: vi.fn(),
    getKpis: vi.fn(),
    getSignals: vi.fn(),
    getRbacValidation: vi.fn(),
  },
}));

vi.mock('@/modules/research-brain/api', () => ({ researchBrainApi: mockApi }));
vi.mock('@/shared/ui/permission-gate', () => ({ RequirePermission: ({ children }: { children: React.ReactNode }) => <>{children}</> }));

import { ResearchBrainRuntimeShellPage } from '@/modules/research-brain/page';

function renderWithClient(ui: React.ReactNode) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(<QueryClientProvider client={client}>{ui}</QueryClientProvider>);
}

describe('Research Brain runtime shell', () => {
  beforeEach(() => {
    mockApi.getShell.mockResolvedValue({
      tenant_id: 1,
      owner_module: 'research_science',
      runtime_boundary: 'UNIFIED_READ_ONLY_RUNTIME_SHELL',
      navigation_entry: '/console/research-brain',
      bridge_modules: ['research', 'research_projects', 'research_grants', 'publication_registry', 'research_ethics', 'analytics', 'brain_core', 'document_workflow'],
      read_only_aggregation: true,
      provider_execution_enabled: false,
      external_calls_enabled: false,
    });
    mockApi.getOrchestration.mockResolvedValue({
      tenant_id: 1,
      projects: { source_module: 'research_science', read_only: true, total: 3, notes: 'projects' },
      grants: { source_module: 'research_science', read_only: true, total: 2, notes: 'grants' },
      publications: { source_module: 'research_science', read_only: true, total: 4, notes: 'publications' },
      ethics: { source_module: 'research_ethics', read_only: true, total: 1, notes: 'ethics' },
      kpi: { source_module: 'analytics', read_only: true, total: 4, notes: 'kpi' },
      signals: { source_module: 'brain_core', read_only: true, total: 4, notes: 'signals' },
    });
    mockApi.getContext.mockResolvedValue({
      tenant_id: 1,
      context: {
        research: { source: 'research', contract_status: 'ACTIVE_BRIDGE', read_only: true, summary: {} },
        publication_registry: { source: 'publication_registry', contract_status: 'FOUNDATION_CONTRACT_READY', read_only: true, summary: {} },
      },
    });
    mockApi.getKpis.mockResolvedValue({
      tenant_id: 1,
      owner_module: 'analytics',
      publication_count: 8,
      grant_count: 5,
      project_count: 4,
      ethics_count: 2,
      read_only: true,
      provider_execution_enabled: false,
    });
    mockApi.getSignals.mockResolvedValue({
      tenant_id: 1,
      signals: [
        { family: 'publication_risk', owner: 'brain_core', source: 'research', consumer: 'dashboard', review_queue: 'research_review_queue', read_only: true, scoring_engine_enabled: false, observed_count: 1 },
        { family: 'grant_risk', owner: 'brain_core', source: 'research', consumer: 'dashboard', review_queue: 'grants_review_queue', read_only: true, scoring_engine_enabled: false, observed_count: 1 },
        { family: 'ethics_risk', owner: 'brain_core', source: 'research_ethics', consumer: 'dashboard', review_queue: 'ethics_review_queue', read_only: true, scoring_engine_enabled: false, observed_count: 1 },
        { family: 'project_delay', owner: 'brain_core', source: 'research_science', consumer: 'dashboard', review_queue: 'project_delay_queue', read_only: true, scoring_engine_enabled: false, observed_count: 1 },
      ],
    });
    mockApi.getRbacValidation.mockResolvedValue({
      tenant_id: 1,
      tenant: 'PASS',
      rbac: 'PASS',
      audit: 'PASS',
      roles: [
        { role: 'researcher', required_permissions: ['research.read'], status: 'PASS' },
        { role: 'research_admin', required_permissions: ['research_science.audit.read'], status: 'PASS' },
      ],
    });
  });

  it('renders unified shell with KPI and signal surfaces', async () => {
    renderWithClient(<ResearchBrainRuntimeShellPage />);

    expect(await screen.findByTestId('research-brain-runtime-shell')).toBeInTheDocument();
    expect(screen.getByText('Research Brain Runtime Shell')).toBeInTheDocument();
    expect(screen.getByText('8')).toBeInTheDocument();
    expect(screen.getByText('5')).toBeInTheDocument();
    expect(screen.getByText('publication_risk')).toBeInTheDocument();
    expect(screen.getByText('grant_risk')).toBeInTheDocument();
  });

  it('renders bridge modules and runtime navigation links', async () => {
    renderWithClient(<ResearchBrainRuntimeShellPage />);

    expect(await screen.findByTestId('research-brain-bridge-modules')).toBeInTheDocument();
    expect(screen.getByText('document_workflow')).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Research Science Overview' })).toHaveAttribute('href', '/console/research-science');
    expect(screen.getByRole('link', { name: 'Research Grants' })).toHaveAttribute('href', '/console/research-grants');
  });

  it('renders no live provider integrations boundary statement', async () => {
    renderWithClient(<ResearchBrainRuntimeShellPage />);

    expect(await screen.findByText(/No live provider integrations/i)).toBeInTheDocument();
    expect(screen.getByTestId('research-brain-rbac-validation')).toBeInTheDocument();
  });
});
