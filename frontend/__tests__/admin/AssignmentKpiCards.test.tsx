/**
 * Tests: Assignment KPI Cards — specifically the fake_metrics guard.
 * These tests verify that KPI values are NEVER shown when fake_metrics=true
 * or when data_source is not "computed_from_assignments".
 */

import { describe, expect, it, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';

vi.mock('@/shared/auth/permission-gate', () => ({
  RequirePermission: ({ children }: { children: React.ReactNode }) => <>{children}</>,
  PermissionGate: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}));

vi.mock('next/navigation', () => ({
  useRouter: () => ({ push: vi.fn() }),
  useParams: () => ({}),
}));

vi.mock('@/modules/rector-assignments/hooks', () => ({
  useRectorAssignmentDashboard: vi.fn(),
  useRectorAssignmentList: vi.fn(),
}));

import * as hooks from '@/modules/rector-assignments/hooks';
import RectorAssignmentsPage from '@/app/(admin)/console/rector-assignments/page';

function makeDashboard(fake_metrics: boolean, data_source: string) {
  return {
    data: {
      fake_metrics,
      data_source,
      total_assignments: 100,
      active_count: 20,
      overdue_count: 5,
      escalated_count: 2,
      completed_count: 73,
      due_this_week: 8,
      due_today: 3,
      completion_rate_30d: 0.9,
      average_days_to_complete: 6,
      by_status: {},
      by_priority: {},
      by_unit: [],
      top_overdue: [],
      draft_count: 0,
      cancelled_count: 0,
      report_submitted_count: 0,
      returned_count: 0,
      tenant_id: 't1',
      computed_at: '2024-01-01T00:00:00Z',
    },
    isLoading: false,
    isError: false,
  };
}

beforeEach(() => {
  vi.clearAllMocks();
  vi.mocked(hooks.useRectorAssignmentList).mockReturnValue({ data: [], isLoading: false, isError: false } as any);
});

describe('KPI anti-fake guard', () => {
  it('GUARD: fake_metrics=true → shows DataQualityError, hides all KPI values', () => {
    vi.mocked(hooks.useRectorAssignmentDashboard).mockReturnValue(makeDashboard(true, 'computed_from_assignments') as any);
    render(<RectorAssignmentsPage />);
    expect(screen.getByTestId('data-quality-error')).toBeInTheDocument();
    expect(screen.queryByTestId('kpi-total')).not.toBeInTheDocument();
    expect(screen.queryByTestId('kpi-active')).not.toBeInTheDocument();
    expect(screen.queryByTestId('kpi-overdue')).not.toBeInTheDocument();
    expect(screen.queryByTestId('kpi-escalated')).not.toBeInTheDocument();
    expect(screen.queryByTestId('kpi-completed')).not.toBeInTheDocument();
    expect(screen.queryByTestId('kpi-due-week')).not.toBeInTheDocument();
  });

  it('GUARD: data_source="hardcoded" → shows DataQualityError, hides all KPI values', () => {
    vi.mocked(hooks.useRectorAssignmentDashboard).mockReturnValue(makeDashboard(false, 'hardcoded') as any);
    render(<RectorAssignmentsPage />);
    expect(screen.getByTestId('data-quality-error')).toBeInTheDocument();
    expect(screen.queryByTestId('kpi-cards-section')).not.toBeInTheDocument();
  });

  it('GUARD: data_source="test_seed" → shows DataQualityError', () => {
    vi.mocked(hooks.useRectorAssignmentDashboard).mockReturnValue(makeDashboard(false, 'test_seed') as any);
    render(<RectorAssignmentsPage />);
    expect(screen.getByTestId('data-quality-error')).toBeInTheDocument();
  });

  it('PASS: fake_metrics=false AND data_source=computed_from_assignments → KPIs visible', () => {
    vi.mocked(hooks.useRectorAssignmentDashboard).mockReturnValue(makeDashboard(false, 'computed_from_assignments') as any);
    render(<RectorAssignmentsPage />);
    expect(screen.queryByTestId('data-quality-error')).not.toBeInTheDocument();
    expect(screen.getByTestId('kpi-total')).toBeInTheDocument();
    expect(screen.getByTestId('kpi-total')).toHaveTextContent('100');
  });

  it('GUARD: both fake_metrics=true AND wrong data_source → shows DataQualityError once', () => {
    vi.mocked(hooks.useRectorAssignmentDashboard).mockReturnValue(makeDashboard(true, 'mock_fallback') as any);
    render(<RectorAssignmentsPage />);
    const errors = screen.getAllByTestId('data-quality-error');
    expect(errors).toHaveLength(1);
  });
});
