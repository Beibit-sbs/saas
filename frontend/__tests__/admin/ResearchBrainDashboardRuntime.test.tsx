import React from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const { mockApi } = vi.hoisted(() => ({
  mockApi: {
    getResearchDashboardSummary: vi.fn(),
    getResearchDashboardKpis: vi.fn(),
    getResearchDashboardSignals: vi.fn(),
    getResearchDashboardRisks: vi.fn(),
    getResearchDashboardScientometrics: vi.fn(),
  },
}));

vi.mock('@/modules/research-brain/api', () => ({ researchBrainApi: mockApi }));
vi.mock('@/shared/ui/permission-gate', () => ({ RequirePermission: ({ children }: { children: React.ReactNode }) => <>{children}</> }));

import { ResearchBrainDashboardPage } from '@/modules/research-brain/page';

function renderWithClient(ui: React.ReactNode) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(<QueryClientProvider client={client}>{ui}</QueryClientProvider>);
}

describe('Research Brain executive dashboard runtime', () => {
  beforeEach(() => {
    mockApi.getResearchDashboardSummary.mockResolvedValue({
      tenant_id: 1,
      generated_at: '2026-06-10T00:00:00Z',
      kpis: {
        researchers: 8,
        publications: 42,
        citations: 640,
        h_index: 66,
        international_publications: 14,
        indexed_publications: 21,
        grants: 7,
        ethics_reviews: 5,
        risk_count: 9,
        signal_count: 9,
      },
      signals: {
        owner: 'brain_core',
        signal_count: 9,
        signals: [
          {
            family: 'publication_gap',
            owner: 'brain_core',
            dimension: 'publication',
            source: 'research_science',
            severity: 'HIGH',
            observed_count: 2,
            affected_entities: ['R-200'],
            description: 'Researchers with no publications indicate publication gap.',
            read_only: true,
          },
        ],
      },
      risks: {
        owner: 'brain_core',
        critical_risks: 3,
        medium_risks: 4,
        low_risks: 2,
        trend_direction: 'up',
        recommendations: ['Escalate near-deadline grants for delivery review.'],
      },
      scientometrics: {
        owner: 'analytics',
        top_researchers: [
          {
            researcher_id: 'R-100',
            citation_count: 120,
            h_index: 14,
            i10_index: 11,
            publication_count: 22,
            international_publications: 9,
            indexed_publications: 16,
            top_publications: ['PUB-1'],
            trend_direction: 'up',
            impact_score: 96,
            scientometric_risk: 'LOW',
            external_identities: [],
            trends: [],
          },
        ],
        citation_leaderboard: [],
        h_index_leaderboard: [],
        impact_leaders: [],
        publication_leaders: [],
      },
      activity: {
        generated_at: '2026-06-10T00:00:00Z',
        publication_activity: 42,
        grant_activity: 7,
        ethics_activity: 5,
        risk_activity: 9,
        signal_activity: 9,
      },
      provider_execution_enabled: false,
      external_calls_enabled: false,
    });

    mockApi.getResearchDashboardKpis.mockResolvedValue({
      researchers: 8,
      publications: 42,
      citations: 640,
      h_index: 66,
      international_publications: 14,
      indexed_publications: 21,
      grants: 7,
      ethics_reviews: 5,
      risk_count: 9,
      signal_count: 9,
    });

    mockApi.getResearchDashboardSignals.mockResolvedValue({
      owner: 'brain_core',
      signal_count: 9,
      signals: [
        {
          family: 'publication_gap',
          owner: 'brain_core',
          dimension: 'publication',
          source: 'research_science',
          severity: 'HIGH',
          observed_count: 2,
          affected_entities: ['R-200'],
          description: 'Researchers with no publications indicate publication gap.',
          read_only: true,
        },
      ],
    });

    mockApi.getResearchDashboardRisks.mockResolvedValue({
      owner: 'brain_core',
      critical_risks: 3,
      medium_risks: 4,
      low_risks: 2,
      trend_direction: 'up',
      recommendations: ['Escalate near-deadline grants for delivery review.'],
    });

    mockApi.getResearchDashboardScientometrics.mockResolvedValue({
      owner: 'analytics',
      top_researchers: [
        {
          researcher_id: 'R-100',
          citation_count: 120,
          h_index: 14,
          i10_index: 11,
          publication_count: 22,
          international_publications: 9,
          indexed_publications: 16,
          top_publications: ['PUB-1'],
          trend_direction: 'up',
          impact_score: 96,
          scientometric_risk: 'LOW',
          external_identities: [],
          trends: [],
        },
      ],
      citation_leaderboard: [],
      h_index_leaderboard: [],
      impact_leaders: [],
      publication_leaders: [],
    });
  });

  it('renders executive dashboard widgets and inventory sections', async () => {
    renderWithClient(<ResearchBrainDashboardPage />);

    expect(await screen.findByTestId('research-brain-dashboard-page')).toBeInTheDocument();
    expect(screen.getByTestId('dashboard-kpi-overview-widget')).toBeInTheDocument();
    expect(screen.getByTestId('dashboard-research-health-widget')).toBeInTheDocument();
    expect(screen.getByTestId('dashboard-scientometric-summary-widget')).toBeInTheDocument();
    expect(screen.getByTestId('dashboard-risk-summary-widget')).toBeInTheDocument();
    expect(screen.getByTestId('dashboard-signal-summary-widget')).toBeInTheDocument();
    expect(screen.getByTestId('dashboard-top-researchers-widget')).toBeInTheDocument();
    expect(screen.getByTestId('dashboard-activity-summary-widget')).toBeInTheDocument();
  });
});
