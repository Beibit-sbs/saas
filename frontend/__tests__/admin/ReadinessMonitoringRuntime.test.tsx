import React from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const { mockApi } = vi.hoisted(() => ({
  mockApi: {
    useReadinessMonitoringRuntime: vi.fn(),
  },
}));

vi.mock('@/modules/quality-accreditation/api', () => ({ qualityAccreditationApi: mockApi }));
vi.mock('@/shared/ui/permission-gate', () => ({ RequirePermission: ({ children }: { children: React.ReactNode }) => <>{children}</> }));

import { QualityAccreditationReadinessMonitoringRuntimePage } from '@/modules/quality-accreditation/pages';

function renderWithClient(ui: React.ReactNode) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(<QueryClientProvider client={client}>{ui}</QueryClientProvider>);
}

describe('Readiness monitoring runtime', () => {
  beforeEach(() => {
    mockApi.useReadinessMonitoringRuntime.mockResolvedValue({
      tenant_id: 1,
      owner_module: 'quality_accreditation',
      runtime_registry: 'READINESS_MONITORING_RUNTIME',
      runtime_mode: 'READ_ONLY_AGGREGATOR',
      generated_at: '2026-06-11T00:00:00Z',
      read_only: true,
      aggregator_only: true,
      readiness_summary: {
        monitored_domains_total: 4,
        domains_on_track: 0,
        domains_at_risk: 1,
        average_readiness_score: 78,
        read_only: true,
        aggregator_only: true,
      },
      readiness_domains: [
        {
          domain_id: 'RD-1',
          domain_name: 'INTERNAL_AUDIT_READINESS',
          readiness_score: 83,
          threshold: 90,
          status: 'WATCH',
          trend: 'UP',
          read_only: true,
          aggregator_only: true,
        },
      ],
      readiness_risks: [
        {
          risk_id: 'RR-1',
          risk_title: 'Delayed closure of high-severity findings',
          risk_level: 'HIGH',
          impacted_domain: 'CLOSURE_TRACKING_READINESS',
          mitigation_status: 'IN_PROGRESS',
          read_only: true,
          aggregator_only: true,
        },
      ],
      remediation_tracking: [
        {
          remediation_id: 'RM-1',
          remediation_title: 'Close unresolved checklist items',
          owner_unit: 'quality_accreditation',
          completion_percentage: 64,
          status: 'IN_PROGRESS',
          due_date: '2026-08-30T00:00:00Z',
          read_only: true,
          aggregator_only: true,
        },
      ],
      readiness_indicators: [
        {
          indicator_name: 'READINESS_SCORE_GLOBAL',
          indicator_value: 78,
          threshold: 85,
          status: 'WATCH',
          read_only: true,
          aggregator_only: true,
        },
      ],
    });
  });

  it('renders readiness monitoring runtime sections', async () => {
    renderWithClient(<QualityAccreditationReadinessMonitoringRuntimePage />);

    expect(await screen.findByTestId('readiness-monitoring-runtime')).toBeInTheDocument();
    expect(screen.getByTestId('readiness-overview-panel')).toBeInTheDocument();
    expect(screen.getByTestId('readiness-domain-panel')).toBeInTheDocument();
    expect(screen.getByTestId('readiness-risk-panel')).toBeInTheDocument();
    expect(screen.getByTestId('readiness-remediation-panel')).toBeInTheDocument();
    expect(screen.getByTestId('readiness-indicators-panel')).toBeInTheDocument();
    expect(screen.getByText('INTERNAL_AUDIT_READINESS')).toBeInTheDocument();
  });

  it('integrates with readiness monitoring runtime API contract', async () => {
    renderWithClient(<QualityAccreditationReadinessMonitoringRuntimePage />);

    expect(await screen.findByRole('heading', { name: 'Readiness Monitoring Runtime', level: 1 })).toBeInTheDocument();
    expect(mockApi.useReadinessMonitoringRuntime).toHaveBeenCalled();
  });
});
