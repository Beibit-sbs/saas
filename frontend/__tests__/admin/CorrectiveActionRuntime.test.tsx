import React from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const { mockApi } = vi.hoisted(() => ({
  mockApi: {
    getCorrectiveActionRuntime: vi.fn(),
  },
}));

vi.mock('@/modules/quality-accreditation/api', () => ({ qualityAccreditationApi: mockApi }));
vi.mock('@/shared/ui/permission-gate', () => ({ RequirePermission: ({ children }: { children: React.ReactNode }) => <>{children}</> }));

import { QualityAccreditationCorrectiveActionRuntimePage } from '@/modules/quality-accreditation/pages';

function renderWithClient(ui: React.ReactNode) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(<QueryClientProvider client={client}>{ui}</QueryClientProvider>);
}

describe('Corrective action runtime', () => {
  beforeEach(() => {
    mockApi.getCorrectiveActionRuntime.mockResolvedValue({
      tenant_id: 1,
      owner_module: 'quality_accreditation',
      runtime_registry: 'CORRECTIVE_ACTION_RUNTIME',
      runtime_mode: 'READ_ONLY_AGGREGATOR',
      generated_at: '2026-06-11T00:00:00Z',
      read_only: true,
      aggregator_only: true,
      corrective_actions: [
        {
          action_id: 'ACT-001',
          action_title: 'Close curriculum evidence gaps',
          accreditation_standard: 'STD-001',
          finding_reference: 'FIND-001',
          owner_unit: 'academic_operations',
          due_date: '2026-06-25T00:00:00Z',
          completion_percentage: 72,
          status: 'ACTIVE',
          readiness_score: 74,
          risk_level: 'MEDIUM',
          overdue_flag: false,
          last_updated: '2026-06-11T00:00:00Z',
          read_only: true,
          aggregator_only: true,
        },
      ],
      action_summary: {
        total_actions: 1,
        completed_actions: 0,
        in_progress_actions: 1,
        overdue_actions: 0,
        average_completion_percentage: 72,
        read_only: true,
        aggregator_only: true,
      },
      readiness_summary: [
        { readiness_band: 'IN_PROGRESS', action_count: 1, average_readiness_score: 74, read_only: true, aggregator_only: true },
      ],
      risk_summary: [
        { risk_level: 'MEDIUM', action_count: 1, read_only: true, aggregator_only: true },
      ],
      overdue_summary: [
        { overdue_state: 'NOT_OVERDUE', action_count: 1, read_only: true, aggregator_only: true },
        { overdue_state: 'OVERDUE', action_count: 0, read_only: true, aggregator_only: true },
      ],
    });
  });

  it('renders corrective action runtime sections and table', async () => {
    renderWithClient(<QualityAccreditationCorrectiveActionRuntimePage />);

    expect(await screen.findByTestId('corrective-action-runtime')).toBeInTheDocument();
    expect(screen.getByTestId('corrective-action-table')).toBeInTheDocument();
    expect(screen.getByTestId('corrective-action-summary')).toBeInTheDocument();
    expect(screen.getByTestId('corrective-action-readiness-summary')).toBeInTheDocument();
    expect(screen.getByTestId('corrective-action-risk-summary')).toBeInTheDocument();
    expect(screen.getByTestId('corrective-action-overdue-summary')).toBeInTheDocument();
    expect(screen.getByText('Close curriculum evidence gaps')).toBeInTheDocument();
  });

  it('integrates with corrective action runtime API client', async () => {
    renderWithClient(<QualityAccreditationCorrectiveActionRuntimePage />);

    expect(await screen.findByRole('heading', { name: 'Corrective Action Runtime', level: 1 })).toBeInTheDocument();
    expect(mockApi.getCorrectiveActionRuntime).toHaveBeenCalled();
  });
});
