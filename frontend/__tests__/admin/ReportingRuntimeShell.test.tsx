import React from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const { mockApi } = vi.hoisted(() => ({
  mockApi: {
    getRuntimeShell: vi.fn(),
  },
}));

vi.mock('@/modules/reporting-runtime/api', () => ({ reportingRuntimeApi: mockApi }));
vi.mock('@/shared/ui/permission-gate', () => ({ RequirePermission: ({ children }: { children: React.ReactNode }) => <>{children}</> }));

import { ReportingRuntimeShellPage } from '@/modules/reporting-runtime/page';

function renderWithClient(ui: React.ReactNode) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(<QueryClientProvider client={client}>{ui}</QueryClientProvider>);
}

describe('Reporting Runtime Shell', () => {
  beforeEach(() => {
    mockApi.getRuntimeShell.mockResolvedValue({
      tenant_id: 1,
      reporting_center_name: 'Reporting Brain Runtime Shell',
      active_reporting_cycles: 6,
      active_submissions: 8,
      active_deadlines: 9,
      provider_readiness: {
        owner_module: 'regulatory_reporting_integration',
        provider_status_counts: { NOT_CONNECTED: 1, READY: 3, PENDING: 1 },
        provider_readiness: 'NON_LIVE_PROFILE_ONLY',
        blocker_count: 2,
        warning_count: 1,
        live_integrations_enabled: false,
        sync_enabled: false,
        submission_execution_enabled: false,
        source_modules: ['regulatory_reporting_integration', 'provider_readiness'],
        read_only: true,
      },
      compliance_score: 78,
      generated_at: '2026-06-10T00:00:00Z',
      read_only: true,
      auditability_preserved: true,
      overview: {
        reporting_center_name: 'Reporting Brain Runtime Shell',
        owner_module: 'reporting_runtime',
        active_reporting_cycles: 6,
        active_submissions: 8,
        active_deadlines: 9,
        source_modules: ['reporting_runtime', 'analytics', 'executive_governance'],
        read_only: true,
      },
      compliance: {
        owner_module: 'reporting_runtime',
        compliance_score: 78,
        risk_band: 'MEDIUM',
        source_modules: ['reporting_runtime', 'brain_core', 'executive_governance'],
        read_only: true,
      },
      deadlines: {
        owner_module: 'reporting_runtime',
        active_deadlines: 9,
        overdue_deadlines: 2,
        upcoming_deadlines: 7,
        deadline_signals: ['report_overdue', 'ministry_deadline_risk', 'submission_risk'],
        source_modules: ['reporting_runtime', 'brain_core', 'executive_governance'],
        read_only: true,
      },
      reporting_status: {
        open_items: 4,
        in_review_items: 3,
        blocked_items: 2,
        read_only: true,
      },
      widgets: [
        'Reporting Overview',
        'Provider Readiness',
        'Compliance Summary',
        'Reporting Deadlines',
        'Reporting Status',
      ],
      rbac_roles: ['reporting_admin', 'vice_rector', 'quality_manager', 'auditor', 'analyst'],
    });
  });

  it('renders runtime shell sections', async () => {
    renderWithClient(<ReportingRuntimeShellPage />);

    expect(await screen.findByTestId('reporting-runtime-shell')).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: 'Reporting Overview' })).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: 'Provider Readiness' })).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: 'Compliance Summary' })).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: 'Reporting Deadlines' })).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: 'Reporting Status' })).toBeInTheDocument();
  });

  it('renders read-only runtime values', async () => {
    renderWithClient(<ReportingRuntimeShellPage />);

    expect(await screen.findByText('Reporting Runtime Shell')).toBeInTheDocument();
    expect(screen.getByText('6')).toBeInTheDocument();
    expect(screen.getByText('8')).toBeInTheDocument();
    expect(screen.getByText('9')).toBeInTheDocument();
    expect(screen.getByText(/NOT_CONNECTED=1, READY=3, PENDING=1/i)).toBeInTheDocument();
    expect(screen.getByText(/read_only=true/i)).toBeInTheDocument();
  });
});
