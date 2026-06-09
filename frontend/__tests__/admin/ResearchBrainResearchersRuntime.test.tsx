import React from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const { mockApi } = vi.hoisted(() => ({
  mockApi: {
    listResearchers: vi.fn(),
    getResearcherSummary: vi.fn(),
    getResearcher: vi.fn(),
    getResearcherActivity: vi.fn(),
    getResearcherRisk: vi.fn(),
  },
}));

vi.mock('@/modules/research-brain/api', () => ({ researchBrainApi: mockApi }));
vi.mock('@/shared/ui/permission-gate', () => ({ RequirePermission: ({ children }: { children: React.ReactNode }) => <>{children}</> }));

import { ResearchBrainResearchersPage } from '@/modules/research-brain/page';

function renderWithClient(ui: React.ReactNode) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(<QueryClientProvider client={client}>{ui}</QueryClientProvider>);
}

describe('Research Brain researcher registry runtime', () => {
  beforeEach(() => {
    mockApi.listResearchers.mockResolvedValue({
      items: [
        {
          researcher_id: 'R-100',
          employee_id: 'EMP-100',
          full_name: 'Dr. Ada Lovelace',
          position: 'Principal Investigator',
          faculty: 'Engineering',
          department: 'Computer Science',
          laboratory: 'AI Systems Lab',
          research_areas: ['AI', 'Systems'],
          specializations: ['ML'],
          active_projects: 2,
          active_grants: 1,
          publication_count: 14,
          citation_count: 240,
          h_index: 11,
          risk_level: 'LOW',
          status: 'ACTIVE',
        },
      ],
    });

    mockApi.getResearcherSummary.mockResolvedValue({
      tenant_id: 1,
      total_researchers: 6,
      active_researchers: 5,
      high_risk_researchers: 1,
      publication_total: 42,
      active_projects_total: 8,
      active_grants_total: 4,
    });

    mockApi.getResearcher.mockResolvedValue({
      researcher_id: 'R-100',
      employee_id: 'EMP-100',
      full_name: 'Dr. Ada Lovelace',
      position: 'Principal Investigator',
      faculty: 'Engineering',
      department: 'Computer Science',
      laboratory: 'AI Systems Lab',
      research_areas: ['AI', 'Systems'],
      specializations: ['ML'],
      active_projects: 2,
      active_grants: 1,
      publication_count: 14,
      citation_count: 240,
      h_index: 11,
      risk_level: 'LOW',
      status: 'ACTIVE',
    });

    mockApi.getResearcherActivity.mockResolvedValue({
      tenant_id: 1,
      researcher: {
        researcher_id: 'R-100',
        employee_id: 'EMP-100',
        full_name: 'Dr. Ada Lovelace',
        position: 'Principal Investigator',
        faculty: 'Engineering',
        department: 'Computer Science',
        laboratory: 'AI Systems Lab',
        research_areas: ['AI', 'Systems'],
        specializations: ['ML'],
        status: 'ACTIVE',
      },
      project_summary: { active_projects: 2 },
      grant_summary: { active_grants: 1 },
      publication_summary: { publication_count: 14, citation_count: 240 },
      scientometric_summary: { h_index: 11, citation_count: 240 },
    });

    mockApi.getResearcherRisk.mockResolvedValue({
      tenant_id: 1,
      researcher_id: 'R-100',
      risk_level: 'MEDIUM',
      workload: { active_projects: 3, active_grants: 2, publication_count: 9 },
      signals: ['workload_pressure', 'publication_stagnation'],
      notes: ['Elevated workload', 'Publication throughput dropped in trailing quarter'],
    });
  });

  it('renders researcher registry and profile surfaces', async () => {
    renderWithClient(<ResearchBrainResearchersPage />);

    expect(await screen.findByTestId('research-brain-researchers-page')).toBeInTheDocument();
    expect(screen.getByTestId('researcher-registry-list')).toBeInTheDocument();
    expect(screen.getByTestId('researcher-profile-view')).toBeInTheDocument();
    expect(screen.getByText('Dr. Ada Lovelace')).toBeInTheDocument();
  });

  it('renders workload, grants, publications, and risk surfaces', async () => {
    renderWithClient(<ResearchBrainResearchersPage />);

    expect(await screen.findByTestId('researcher-workload-view')).toBeInTheDocument();
    expect(screen.getByTestId('researcher-grants-view')).toBeInTheDocument();
    expect(screen.getByTestId('researcher-publications-view')).toBeInTheDocument();
    expect(screen.getByTestId('researcher-risk-view')).toBeInTheDocument();
    expect(screen.getByText('Risk Level: MEDIUM')).toBeInTheDocument();
    expect(screen.getByText(/workload_pressure/i)).toBeInTheDocument();
  });
});
