import React from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const { mockApi } = vi.hoisted(() => ({
  mockApi: {
    getScientometricsDashboard: vi.fn(),
    getScientometricRanking: vi.fn(),
    listResearchers: vi.fn(),
    getResearcherScientometrics: vi.fn(),
    getResearcherCitationAnalytics: vi.fn(),
    getResearcherImpactAnalytics: vi.fn(),
    getResearcherPublicationImpact: vi.fn(),
    getResearcherScientometricTrends: vi.fn(),
  },
}));

vi.mock('@/modules/research-brain/api', () => ({ researchBrainApi: mockApi }));
vi.mock('@/shared/ui/permission-gate', () => ({ RequirePermission: ({ children }: { children: React.ReactNode }) => <>{children}</> }));

import { ResearchBrainScientometricsPage } from '@/modules/research-brain/page';

function renderWithClient(ui: React.ReactNode) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(<QueryClientProvider client={client}>{ui}</QueryClientProvider>);
}

describe('Research Brain scientometrics runtime', () => {
  beforeEach(() => {
    mockApi.getScientometricsDashboard.mockResolvedValue({
      tenant_id: 1,
      top_researchers: [
        {
          researcher_id: 'R-100',
          citation_count: 120,
          h_index: 14,
          i10_index: 11,
          publication_count: 22,
          international_publications: 9,
          indexed_publications: 16,
          top_publications: ['PUB-1', 'PUB-2'],
          trend_direction: 'up',
          impact_score: 96.0,
          scientometric_risk: 'LOW',
          external_identities: [
            { provider_name: 'ORCID', provider_identifier: 'orcid:R-100', provider_status: 'PENDING' },
          ],
          trends: [
            { period: 'current', citation_count: 120, h_index: 14, i10_index: 11, trend_direction: 'up', impact_score: 96.0 },
          ],
        },
      ],
      citation_leaderboard: [
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
          impact_score: 96.0,
          scientometric_risk: 'LOW',
        },
      ],
      h_index_leaderboard: [
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
          impact_score: 96.0,
          scientometric_risk: 'LOW',
        },
      ],
      publication_impact_summary: [
        {
          researcher_id: 'R-100',
          publication_count: 22,
          international_publications: 9,
          indexed_publications: 16,
          top_publications: ['PUB-1'],
          citation_count: 120,
          h_index: 14,
          i10_index: 11,
          trend_direction: 'up',
          impact_score: 96.0,
          scientometric_risk: 'LOW',
        },
      ],
      scientometric_trend_summary: [
        { period: 'R-100', citation_count: 120, h_index: 14, i10_index: 11, trend_direction: 'up', impact_score: 96.0 },
      ],
      provider_execution_enabled: false,
      external_calls_enabled: false,
    });

    mockApi.getScientometricRanking.mockResolvedValue({
      tenant_id: 1,
      items: [{ researcher_id: 'R-100', rank: 1, impact_score: 96.0, scientometric_risk: 'LOW' }],
    });

    mockApi.listResearchers.mockResolvedValue({
      items: [{ researcher_id: 'R-100' }],
    });

    mockApi.getResearcherScientometrics.mockResolvedValue({
      researcher_id: 'R-100',
      citation_count: 120,
      h_index: 14,
      i10_index: 11,
      publication_count: 22,
      international_publications: 9,
      indexed_publications: 16,
      top_publications: ['PUB-1'],
      trend_direction: 'up',
      impact_score: 96.0,
      scientometric_risk: 'LOW',
      external_identities: [
        { provider_name: 'ORCID', provider_identifier: 'orcid:R-100', provider_status: 'PENDING' },
        { provider_name: 'Scopus', provider_identifier: 'scopus:R-100', provider_status: 'NOT_CONNECTED' },
        { provider_name: 'WebOfScience', provider_identifier: 'webofscience:R-100', provider_status: 'NOT_CONNECTED' },
        { provider_name: 'GoogleScholar', provider_identifier: 'googlescholar:R-100', provider_status: 'NOT_CONNECTED' },
        { provider_name: 'DOI', provider_identifier: 'doi:R-100', provider_status: 'READY' },
      ],
      trends: [{ period: 'current', citation_count: 120, h_index: 14, i10_index: 11, trend_direction: 'up', impact_score: 96.0 }],
    });

    mockApi.getResearcherCitationAnalytics.mockResolvedValue({
      researcher_id: 'R-100',
      citation_count: 120,
      h_index: 14,
      i10_index: 11,
      publication_count: 22,
      international_publications: 9,
      indexed_publications: 16,
      top_publications: ['PUB-1'],
      trend_direction: 'up',
      impact_score: 96.0,
      scientometric_risk: 'LOW',
    });

    mockApi.getResearcherImpactAnalytics.mockResolvedValue({
      researcher_id: 'R-100',
      publication_count: 22,
      international_publications: 9,
      indexed_publications: 16,
      top_publications: ['PUB-1'],
      citation_count: 120,
      h_index: 14,
      i10_index: 11,
      trend_direction: 'up',
      impact_score: 96.0,
      scientometric_risk: 'LOW',
    });

    mockApi.getResearcherPublicationImpact.mockResolvedValue({
      researcher_id: 'R-100',
      publication_count: 22,
      international_publications: 9,
      indexed_publications: 16,
      top_publications: ['PUB-1'],
      citation_count: 120,
      h_index: 14,
      i10_index: 11,
      trend_direction: 'up',
      impact_score: 96.0,
      scientometric_risk: 'LOW',
    });

    mockApi.getResearcherScientometricTrends.mockResolvedValue([
      { period: 'trailing_12m', citation_count: 102, h_index: 13, i10_index: 10, trend_direction: 'stable', impact_score: 88.0 },
      { period: 'current', citation_count: 120, h_index: 14, i10_index: 11, trend_direction: 'up', impact_score: 96.0 },
    ]);
  });

  it('renders scientometrics dashboard widgets', async () => {
    renderWithClient(<ResearchBrainScientometricsPage />);

    expect(await screen.findByTestId('research-brain-scientometrics-page')).toBeInTheDocument();
    expect(screen.getByTestId('scientometrics-top-researchers-widget')).toBeInTheDocument();
    expect(screen.getByTestId('scientometrics-citation-leaderboard-widget')).toBeInTheDocument();
    expect(screen.getByTestId('scientometrics-hindex-leaderboard-widget')).toBeInTheDocument();
    expect(screen.getByTestId('scientometrics-publication-impact-summary-widget')).toBeInTheDocument();
    expect(screen.getByTestId('scientometrics-trend-summary-widget')).toBeInTheDocument();
  });

  it('renders profile, citation, impact, identity readiness, and trends views', async () => {
    renderWithClient(<ResearchBrainScientometricsPage />);

    expect(await screen.findByTestId('scientometric-profile-view')).toBeInTheDocument();
    expect(screen.getByTestId('citation-analytics-view')).toBeInTheDocument();
    expect(screen.getByTestId('publication-impact-view')).toBeInTheDocument();
    expect(screen.getByTestId('external-identity-readiness-view')).toBeInTheDocument();
    expect(screen.getByTestId('scientometric-trends-view')).toBeInTheDocument();
    expect(screen.getByText(/ORCID: PENDING/i)).toBeInTheDocument();
    expect(screen.getByText(/DOI: READY/i)).toBeInTheDocument();
  });
});
