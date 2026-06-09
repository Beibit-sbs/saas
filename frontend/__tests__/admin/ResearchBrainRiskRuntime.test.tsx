import React from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const { mockApi } = vi.hoisted(() => ({
  mockApi: {
    getResearchRiskDashboard: vi.fn(),
    getResearchRiskProfile: vi.fn(),
    getResearchRiskSummary: vi.fn(),
    getResearchRiskSignals: vi.fn(),
    getResearchRiskTrends: vi.fn(),
    getResearchRiskRecommendations: vi.fn(),
  },
}));

vi.mock('@/modules/research-brain/api', () => ({ researchBrainApi: mockApi }));
vi.mock('@/shared/ui/permission-gate', () => ({ RequirePermission: ({ children }: { children: React.ReactNode }) => <>{children}</> }));

import { ResearchBrainRiskPage } from '@/modules/research-brain/page';

function renderWithClient(ui: React.ReactNode) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(<QueryClientProvider client={client}>{ui}</QueryClientProvider>);
}

describe('Research Brain research risk runtime', () => {
  beforeEach(() => {
    const profile = {
      tenant_id: 1,
      generated_at: '2026-06-10T00:00:00Z',
      summary: {
        overall_risk_score: 62.5,
        severity: 'HIGH',
        publication_risk: 58,
        grant_risk: 72,
        ethics_risk: 48,
        scientometric_risk: 66,
        execution_risk: 68.5,
        risk_heatmap: {
          publication: 'MEDIUM',
          grant: 'HIGH',
          ethics: 'MEDIUM',
          scientometric: 'HIGH',
          execution: 'HIGH',
        },
        top_critical_risks: ['grant_execution_risk', 'research_output_drop'],
      },
      signals: [
        {
          family: 'publication_delay',
          owner: 'brain_core',
          dimension: 'publication',
          source: 'research_science',
          severity: 'MEDIUM',
          observed_count: 2,
          affected_entities: ['R-100'],
          description: 'Publication delivery delay detected.',
          read_only: true,
        },
      ],
      trends: [
        {
          dimension: 'publication',
          current_score: 58,
          previous_score: 50,
          trend_direction: 'up',
          severity: 'MEDIUM',
        },
      ],
      recommendations: ['Escalate near-deadline grants for delivery review.'],
      provider_execution_enabled: false,
      external_calls_enabled: false,
    };

    mockApi.getResearchRiskDashboard.mockResolvedValue(profile);
    mockApi.getResearchRiskProfile.mockResolvedValue(profile);
    mockApi.getResearchRiskSummary.mockResolvedValue(profile.summary);
    mockApi.getResearchRiskSignals.mockResolvedValue([
      ...profile.signals,
      {
        family: 'grant_execution_risk',
        owner: 'brain_core',
        dimension: 'grant',
        source: 'research_grants',
        severity: 'HIGH',
        observed_count: 3,
        affected_entities: ['R-200'],
        description: 'Grant execution milestones are at risk.',
        read_only: true,
      },
      {
        family: 'ethics_expiration_risk',
        owner: 'brain_core',
        dimension: 'ethics',
        source: 'research_ethics',
        severity: 'MEDIUM',
        observed_count: 1,
        affected_entities: ['ETH-1'],
        description: 'Ethics review expiry window detected.',
        read_only: true,
      },
      {
        family: 'citation_decline_risk',
        owner: 'brain_core',
        dimension: 'scientometric',
        source: 'analytics',
        severity: 'HIGH',
        observed_count: 2,
        affected_entities: ['R-100'],
        description: 'Citation decline trend detected.',
        read_only: true,
      },
      {
        family: 'low_visibility_risk',
        owner: 'brain_core',
        dimension: 'scientometric',
        source: 'publication_registry',
        severity: 'HIGH',
        observed_count: 2,
        affected_entities: ['R-300'],
        description: 'Low visibility profile detected.',
        read_only: true,
      },
      {
        family: 'research_output_drop',
        owner: 'brain_core',
        dimension: 'execution',
        source: 'research_science',
        severity: 'HIGH',
        observed_count: 1,
        affected_entities: ['R-400'],
        description: 'Research output drop detected.',
        read_only: true,
      },
    ]);
    mockApi.getResearchRiskTrends.mockResolvedValue([
      ...profile.trends,
      {
        dimension: 'grant',
        current_score: 72,
        previous_score: 61,
        trend_direction: 'up',
        severity: 'HIGH',
      },
    ]);
    mockApi.getResearchRiskRecommendations.mockResolvedValue(profile.recommendations);
  });

  it('renders research risk dashboard widgets and heatmap', async () => {
    renderWithClient(<ResearchBrainRiskPage />);

    expect(await screen.findByTestId('research-brain-risk-page')).toBeInTheDocument();
    expect(screen.getByTestId('research-risk-overall-score-widget')).toBeInTheDocument();
    expect(screen.getByTestId('research-risk-heatmap-widget')).toBeInTheDocument();
    expect(screen.getByTestId('publication-risk-widget')).toBeInTheDocument();
    expect(screen.getByTestId('grant-risk-widget')).toBeInTheDocument();
    expect(screen.getByTestId('ethics-risk-widget')).toBeInTheDocument();
    expect(screen.getByTestId('scientometric-risk-widget')).toBeInTheDocument();
    expect(screen.getByTestId('top-critical-risks-widget')).toBeInTheDocument();
  });

  it('renders risk profile, signal inventory, recommendations, and trend analysis', async () => {
    renderWithClient(<ResearchBrainRiskPage />);

    expect(await screen.findByTestId('risk-profile-view')).toBeInTheDocument();
    expect(screen.getByTestId('risk-signal-inventory-view')).toBeInTheDocument();
    expect(screen.getByTestId('risk-recommendations-view')).toBeInTheDocument();
    expect(screen.getByTestId('risk-trend-analysis-view')).toBeInTheDocument();
    expect(screen.getByTestId('risk-signal-inventory-view')).toHaveTextContent(/grant_execution_risk/i);
    expect(screen.getByText(/Escalate near-deadline grants for delivery review./i)).toBeInTheDocument();
  });
});