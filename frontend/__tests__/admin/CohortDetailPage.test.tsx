import { describe, it, expect, beforeEach, vi } from 'vitest';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';

import type { CohortReadSchema } from '@/shared/hooks/useInterventionCohorts';

const analyzeMutateMock = vi.fn();
const finalizeMutateMock = vi.fn();
const refetchOutcomesMock = vi.fn(async () => ({ data: { items: [], total: 0 } }));

let authState: { user?: { tenantId?: number }; isLoading: boolean } = {
  user: { tenantId: 100 },
  isLoading: false,
};

let cohortState: CohortReadSchema | undefined;

vi.mock('next/link', () => ({
  default: ({ href, children }: { href: string; children: React.ReactNode }) => <a href={href}>{children}</a>,
}));

vi.mock('@/shared/auth/context', () => ({
  useAdminAuth: () => authState,
}));

vi.mock('@/shared/hooks/useInterventionCohorts', () => ({
  useCohortDetail: () => ({
    data: cohortState,
    isLoading: false,
    error: null,
  }),
  useFinalizeExistingCohortMutation: () => ({
    mutate: finalizeMutateMock,
    isPending: false,
  }),
}));

vi.mock('@/shared/hooks/useCohortAnalysis', async () => {
  const actual = await vi.importActual<typeof import('@/shared/hooks/useCohortAnalysis')>(
    '@/shared/hooks/useCohortAnalysis',
  );

  return {
    ...actual,
    useCohortAnalysisMutation: () => ({
      mutate: analyzeMutateMock,
      isPending: false,
    }),
  };
});

vi.mock('@/shared/hooks/useCohortOutcomes', () => ({
  useCohortOutcomesQuery: () => ({
    data: { items: [], total: 0 },
    isLoading: false,
    refetch: refetchOutcomesMock,
    error: null,
  }),
}));

import CohortDetailPage from '@/app/(admin)/console/interventions/cohorts/[id]/page';

const baseCohort: CohortReadSchema = {
  id: 42,
  tenant_id: 100,
  playbook_id: 5,
  cohort_name: 'Spring 2026 Cohort A',
  analysis_window_start: '2026-01-15',
  analysis_window_end: '2026-05-15',
  student_count: 100,
  data_completeness_pct: 0.95,
  status: 'draft',
  created_by: 'system@example.com',
  created_at: '2026-04-01T10:00:00Z',
};

describe('CohortDetailPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    authState = { user: { tenantId: 100 }, isLoading: false };
    cohortState = { ...baseCohort };
  });

  it('shows invalid cohort error for non-numeric id', () => {
    render(<CohortDetailPage params={{ id: 'bad-id' }} />);

    expect(screen.getByText('Invalid cohort')).toBeInTheDocument();
    expect(screen.getByText('The cohort identifier in the URL is not valid.')).toBeInTheDocument();
  });

  it('blocks analysis for draft cohorts with explicit error', async () => {
    render(<CohortDetailPage params={{ id: '42' }} />);

    expect(screen.getByRole('button', { name: 'Run outcomes analysis for this cohort' })).toBeDisabled();
    expect(screen.getByText('Finalize cohort before analysis becomes available.')).toBeInTheDocument();
    expect(analyzeMutateMock).not.toHaveBeenCalled();
  });

  it('shows queued notice after successful analysis handoff', async () => {
    cohortState = { ...baseCohort, status: 'finalized' };
    analyzeMutateMock.mockImplementation((_payload, options) => {
      options?.onSuccess?.({
        cohort_id: 42,
        status: 'analysis_queued',
        detail: 'Effectiveness analysis queued for cohort 42.',
        requested_at: '2026-04-21T12:00:00Z',
      });
    });

    render(<CohortDetailPage params={{ id: '42' }} />);

    fireEvent.click(screen.getByRole('button', { name: 'Run Analysis' }));

    await waitFor(() => {
      expect(screen.getByText('Effectiveness analysis queued for cohort 42.')).toBeInTheDocument();
      expect(screen.getByText('Analysis started')).toBeInTheDocument();
    });
    expect(refetchOutcomesMock).not.toHaveBeenCalled();
  });

  it('shows failure state when analysis request fails', async () => {
    cohortState = { ...baseCohort, status: 'finalized' };
    analyzeMutateMock.mockImplementation((_payload, options) => {
      options?.onError?.(new Error('Failed to start analysis from API'));
    });

    render(<CohortDetailPage params={{ id: '42' }} />);

    fireEvent.click(screen.getByRole('button', { name: 'Run Analysis' }));

    await waitFor(() => {
      expect(screen.getByText('Failed to start analysis from API')).toBeInTheDocument();
      expect(screen.getByText('Failed to load analysis results')).toBeInTheDocument();
    });
  });
});
