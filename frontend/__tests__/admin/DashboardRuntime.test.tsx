import React from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const { mockApi } = vi.hoisted(() => ({
  mockApi: {
    useDashboardRuntime: vi.fn(),
  },
}));

vi.mock('@/modules/quality-accreditation/api', () => ({ qualityAccreditationApi: mockApi }));
vi.mock('@/shared/ui/permission-gate', () => ({ RequirePermission: ({ children }: { children: React.ReactNode }) => <>{children}</> }));

import { QualityAccreditationDashboardRuntimePage } from '@/modules/quality-accreditation/pages';

function renderWithClient(ui: React.ReactNode) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(<QueryClientProvider client={client}>{ui}</QueryClientProvider>);
}

describe('Quality accreditation dashboard runtime', () => {
  beforeEach(() => {
    mockApi.useDashboardRuntime.mockResolvedValue({
      tenant_id: 1,
      owner_module: 'quality_accreditation',
      runtime_registry: 'DASHBOARD_RUNTIME',
      runtime_mode: 'READ_ONLY_AGGREGATOR',
      generated_at: '2026-06-11T00:00:00Z',
      read_only: true,
      aggregator_only: true,
      accreditation_summary: [{ metric_key: 'active_cycles', label: 'Active accreditation cycles', value: 3, status: 'TRACKED', read_only: true, aggregator_only: true }],
      evidence_coverage_summary: [{ metric_key: 'coverage_percent', label: 'Evidence coverage %', value: 82, status: 'WATCH', read_only: true, aggregator_only: true }],
      self_assessment_status: [{ metric_key: 'completed_sections', label: 'Completed self-assessment sections', value: 41, status: 'TRACKED', read_only: true, aggregator_only: true }],
      corrective_action_status: [{ metric_key: 'open_actions', label: 'Open corrective actions', value: 14, status: 'WATCH', read_only: true, aggregator_only: true }],
      improvement_plan_status: [{ metric_key: 'on_track_initiatives', label: 'On-track initiatives', value: 6, status: 'TRACKED', read_only: true, aggregator_only: true }],
      readiness_monitoring_summary: [{ metric_key: 'avg_readiness_score', label: 'Average readiness score', value: 78, status: 'WATCH', read_only: true, aggregator_only: true }],
      audit_findings_summary: [{ metric_key: 'open_findings', label: 'Open audit findings', value: 9, status: 'WATCH', read_only: true, aggregator_only: true }],
      executive_kpi_rollup: [{ kpi_group: 'ACCREDITATION_READINESS', score: 79, threshold: 85, trend: 'UP', read_only: true, aggregator_only: true }],
      compliance_indicators: [{ indicator_name: 'INTERNAL_CONTROL_COMPLIANCE', indicator_value: 84, threshold: 90, status: 'WATCH', read_only: true, aggregator_only: true }],
      accreditation_risk_indicators: [{ risk_name: 'Delayed closure', risk_level: 'HIGH', impacted_area: 'AUDIT_FINDINGS', mitigation_status: 'IN_PROGRESS', read_only: true, aggregator_only: true }],
    });
  });

  it('renders dashboard runtime sections', async () => {
    renderWithClient(<QualityAccreditationDashboardRuntimePage />);

    expect(await screen.findByTestId('dashboard-runtime')).toBeInTheDocument();
    expect(screen.getByTestId('dashboard-accreditation-summary')).toBeInTheDocument();
    expect(screen.getByTestId('dashboard-evidence-coverage-summary')).toBeInTheDocument();
    expect(screen.getByTestId('dashboard-self-assessment-status')).toBeInTheDocument();
    expect(screen.getByTestId('dashboard-corrective-action-status')).toBeInTheDocument();
    expect(screen.getByTestId('dashboard-improvement-plan-status')).toBeInTheDocument();
    expect(screen.getByTestId('dashboard-readiness-monitoring-summary')).toBeInTheDocument();
    expect(screen.getByTestId('dashboard-audit-findings-summary')).toBeInTheDocument();
    expect(screen.getByTestId('dashboard-executive-kpi-rollup')).toBeInTheDocument();
    expect(screen.getByTestId('dashboard-compliance-indicators')).toBeInTheDocument();
    expect(screen.getByTestId('dashboard-accreditation-risk-indicators')).toBeInTheDocument();
  });

  it('integrates with dashboard runtime API contract', async () => {
    renderWithClient(<QualityAccreditationDashboardRuntimePage />);

    expect(await screen.findByRole('heading', { name: 'Dashboard Runtime', level: 1 })).toBeInTheDocument();
    expect(mockApi.useDashboardRuntime).toHaveBeenCalled();
  });
});
