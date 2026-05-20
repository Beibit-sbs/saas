/**
 * Tests: RectorAssignmentsPage (Dashboard + Registry)
 * CRITICAL: fake_metrics guard tests are mandatory.
 */

import { beforeEach, describe, expect, it, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

vi.mock('@/shared/auth/permission-gate', () => ({
  RequirePermission: ({ children }: { children: React.ReactNode }) => <>{children}</>,
  PermissionGate: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}));

vi.mock('next/navigation', () => ({
  useRouter: () => ({ push: vi.fn(), back: vi.fn() }),
  useParams: () => ({}),
}));

vi.mock('@/modules/rector-assignments/hooks', () => ({
  useRectorAssignmentDashboard: vi.fn(),
  useRectorAssignmentList: vi.fn(),
}));

import * as hooks from '@/modules/rector-assignments/hooks';
import RectorAssignmentsPage from '@/app/(admin)/console/rector-assignments/page';

function stubDashboard(overrides = {}) {
  const base = {
    data: {
      fake_metrics: false,
      data_source: 'computed_from_assignments',
      total_assignments: 42,
      active_count: 10,
      overdue_count: 3,
      escalated_count: 1,
      completed_count: 28,
      due_this_week: 5,
      due_today: 2,
      completion_rate_30d: 0.85,
      average_days_to_complete: 7.2,
      by_status: {},
      by_priority: {},
      by_unit: [],
      top_overdue: [],
      draft_count: 1,
      cancelled_count: 0,
      report_submitted_count: 2,
      returned_count: 1,
      tenant_id: 'test-tenant',
      computed_at: '2024-01-01T00:00:00Z',
    },
    isLoading: false,
    isError: false,
    ...overrides,
  };
  vi.mocked(hooks.useRectorAssignmentDashboard).mockReturnValue(base as any);
}

function stubList(assignments = []) {
  vi.mocked(hooks.useRectorAssignmentList).mockReturnValue({
    data: assignments,
    isLoading: false,
    isError: false,
  } as any);
}

beforeEach(() => {
  vi.clearAllMocks();
  stubDashboard();
  stubList();
});

describe('RectorAssignmentsPage', () => {
  describe('Loading and error states', () => {
    it('shows loading state when dashboard is loading', () => {
      stubDashboard({ data: undefined, isLoading: true, isError: false });
      render(<RectorAssignmentsPage />);
      expect(screen.getAllByText(/loading/i).length).toBeGreaterThan(0);
    });

    it('shows error state when dashboard fetch fails', () => {
      stubDashboard({ data: undefined, isLoading: false, isError: true });
      render(<RectorAssignmentsPage />);
      expect(screen.getByText(/failed to load/i)).toBeInTheDocument();
    });
  });

  describe('fake_metrics guard (MANDATORY)', () => {
    it('shows data-quality-error when fake_metrics is true', () => {
      stubDashboard({
        data: {
          fake_metrics: true,
          data_source: 'computed_from_assignments',
          total_assignments: 999,
          active_count: 99,
          overdue_count: 0,
          escalated_count: 0,
          completed_count: 0,
          due_this_week: 0,
        },
      });
      render(<RectorAssignmentsPage />);
      expect(screen.getByTestId('data-quality-error')).toBeInTheDocument();
      // MUST NOT render any KPI value
      expect(screen.queryByTestId('kpi-total')).not.toBeInTheDocument();
    });

    it('shows data-quality-error when data_source is not computed_from_assignments', () => {
      stubDashboard({
        data: {
          fake_metrics: false,
          data_source: 'mock_data',
          total_assignments: 42,
          active_count: 10,
          overdue_count: 0,
          escalated_count: 0,
          completed_count: 0,
          due_this_week: 0,
        },
      });
      render(<RectorAssignmentsPage />);
      expect(screen.getByTestId('data-quality-error')).toBeInTheDocument();
      expect(screen.queryByTestId('kpi-total')).not.toBeInTheDocument();
    });

    it('does NOT show data-quality-error when both guards pass', () => {
      render(<RectorAssignmentsPage />);
      expect(screen.queryByTestId('data-quality-error')).not.toBeInTheDocument();
    });
  });

  describe('KPI cards (only rendered after guards pass)', () => {
    it('renders all six KPI cards with correct values', () => {
      render(<RectorAssignmentsPage />);
      expect(screen.getByTestId('kpi-total')).toHaveTextContent('42');
      expect(screen.getByTestId('kpi-active')).toHaveTextContent('10');
      expect(screen.getByTestId('kpi-overdue')).toHaveTextContent('3');
      expect(screen.getByTestId('kpi-escalated')).toHaveTextContent('1');
      expect(screen.getByTestId('kpi-completed')).toHaveTextContent('28');
      expect(screen.getByTestId('kpi-due-week')).toHaveTextContent('5');
    });
  });

  describe('Overdue alert', () => {
    it('shows overdue alert when overdue_count > 0', () => {
      render(<RectorAssignmentsPage />);
      expect(screen.getByTestId('overdue-alert-section')).toBeInTheDocument();
    });

    it('does not show overdue alert when overdue_count is 0', () => {
      stubDashboard({
        data: {
          fake_metrics: false,
          data_source: 'computed_from_assignments',
          total_assignments: 5,
          active_count: 5,
          overdue_count: 0,
          escalated_count: 0,
          completed_count: 0,
          due_this_week: 0,
        },
      });
      render(<RectorAssignmentsPage />);
      expect(screen.queryByTestId('overdue-alert-section')).not.toBeInTheDocument();
    });
  });

  describe('Assignment list', () => {
    it('renders empty state when no assignments', () => {
      render(<RectorAssignmentsPage />);
      expect(screen.getByTestId('empty-list')).toBeInTheDocument();
    });

    it('renders assignment rows when list has items', () => {
      stubList([
        {
          id: '1',
          title: 'Test Assignment Alpha',
          priority: 'HIGH',
          status: 'IN_PROGRESS',
          due_date: '2025-12-31',
          is_overdue: false,
        },
      ] as any);
      render(<RectorAssignmentsPage />);
      expect(screen.getByTestId('assignment-row-1')).toBeInTheDocument();
      expect(screen.getByText('Test Assignment Alpha')).toBeInTheDocument();
    });
  });

  describe('Filters', () => {
    it('renders status and priority filter selects', () => {
      render(<RectorAssignmentsPage />);
      expect(screen.getByTestId('status-filter')).toBeInTheDocument();
      expect(screen.getByTestId('priority-filter')).toBeInTheDocument();
    });

    it('renders overdue-only toggle', () => {
      render(<RectorAssignmentsPage />);
      expect(screen.getByTestId('overdue-only-toggle')).toBeInTheDocument();
    });
  });
});
