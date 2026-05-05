/**
 * Procurement Workflow Page — Unit Tests
 * Validates rendering of procurement request lifecycle dashboard
 */

import { beforeEach, describe, expect, it, vi } from 'vitest';
import { render, screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import ProcurementWorkflowPage from '@/app/(admin)/console/procurement-workflow/page';

vi.mock('@/shared/auth/permission-gate', () => ({
  RequirePermission: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}));

vi.mock('@/shared/ui/page-header', () => ({
  PageHeader: ({ title }: { title: string }) => <h1>{title}</h1>,
}));

vi.mock('@/shared/ui/page-states', () => ({
  LoadingState: ({ message }: { message: string }) => <div>{message}</div>,
  ErrorState: ({ message }: { message: string }) => <div>{message}</div>,
}));

vi.mock('@/shared/ui/badge', () => ({
  Badge: ({ children, variant }: { children: React.ReactNode; variant?: string }) => (
    <span data-variant={variant}>{children}</span>
  ),
}));

vi.mock('@/modules/procurement-workflow/hooks', () => ({
  useProcurementDashboardSummary: vi.fn(),
  useProcurementList: vi.fn(),
}));

vi.mock('@/modules/platform/kpi/wave1-kpi-bar', () => ({
  Wave1KpiBar: () => null,
}));

import * as hooks from '@/modules/procurement-workflow/hooks';

const DEFAULT_DASHBOARD = {
  total_requests: 18,
  status_breakdown: {
    draft: 2,
    submitted: 3,
    under_review: 4,
    approved: 5,
    rejected: 1,
    ordered: 2,
    fulfilled: 1,
  },
  total_pending_approvals: 7,
  total_ordered_value: 2450000,
  overdue_requests: 2,
  last_updated: '2026-04-22T09:00:00Z',
};

const DEFAULT_REQUESTS = [
  {
    request_id: 'req-001',
    request_number: 'PR-2026-001',
    title: 'Lab Workstations Upgrade',
    requester_name: 'Alice Johnson',
    department_name: 'Engineering',
    status: 'under_review' as const,
    priority: 'high' as const,
    estimated_total: 950000,
    created_at: '2026-04-18T11:00:00Z',
    updated_at: '2026-04-20T14:00:00Z',
  },
  {
    request_id: 'req-002',
    request_number: 'PR-2026-002',
    title: 'Learning Platform Licenses',
    requester_name: 'Bob Smith',
    department_name: 'Academic Affairs',
    status: 'approved' as const,
    priority: 'medium' as const,
    estimated_total: 1500000,
    created_at: '2026-04-19T09:30:00Z',
    updated_at: '2026-04-21T16:00:00Z',
  },
];

describe('ProcurementWorkflowPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    stubDefaults();
  });

  function stubDefaults() {
    vi.mocked(hooks.useProcurementDashboardSummary).mockReturnValue({
      data: DEFAULT_DASHBOARD,
      isLoading: false,
      isError: false,
      refetch: vi.fn(),
    } as any);

    vi.mocked(hooks.useProcurementList).mockReturnValue({
      data: DEFAULT_REQUESTS,
      isLoading: false,
      isError: false,
      refetch: vi.fn(),
    } as any);
  }

  it('renders page heading', () => {
    render(<ProcurementWorkflowPage />);
    expect(screen.getByText('Procurement Workflow')).toBeInTheDocument();
  });

  it('shows loading state when dashboard query is loading', () => {
    vi.mocked(hooks.useProcurementDashboardSummary).mockReturnValue({
      data: undefined,
      isLoading: true,
      isError: false,
      refetch: vi.fn(),
    } as any);

    render(<ProcurementWorkflowPage />);
    expect(screen.getByText(/Loading procurement dashboard/)).toBeInTheDocument();
  });

  it('shows error state when dashboard query fails', () => {
    vi.mocked(hooks.useProcurementDashboardSummary).mockReturnValue({
      data: undefined,
      isLoading: false,
      isError: true,
      refetch: vi.fn(),
    } as any);

    render(<ProcurementWorkflowPage />);
    expect(screen.getByText('Failed to load procurement data')).toBeInTheDocument();
  });

  it('renders dashboard metrics', () => {
    render(<ProcurementWorkflowPage />);

    expect(screen.getByTestId('total-requests')).toHaveTextContent('18');
    expect(screen.getByTestId('pending-approvals')).toHaveTextContent('7');
    expect(screen.getByTestId('ordered-value')).toHaveTextContent('2,450,000');
    expect(screen.getByTestId('overdue-requests')).toHaveTextContent('2');
    expect(screen.getByTestId('approved-count')).toHaveTextContent('5');
  });

  it('shows overdue alert when overdue requests exist', () => {
    render(<ProcurementWorkflowPage />);
    expect(screen.getByTestId('overdue-alert-section')).toBeInTheDocument();
    expect(screen.getByText(/2 overdue procurement requests/)).toBeInTheDocument();
  });

  it('hides overdue alert when overdue count is zero', () => {
    vi.mocked(hooks.useProcurementDashboardSummary).mockReturnValue({
      data: { ...DEFAULT_DASHBOARD, overdue_requests: 0 },
      isLoading: false,
      isError: false,
      refetch: vi.fn(),
    } as any);

    render(<ProcurementWorkflowPage />);
    expect(screen.queryByTestId('overdue-alert-section')).not.toBeInTheDocument();
  });

  it('renders status distribution section', () => {
    render(<ProcurementWorkflowPage />);

    const statusSection = screen.getByTestId('status-distribution-section');
    expect(statusSection).toBeInTheDocument();
    expect(within(statusSection).getByText('Under Review')).toBeInTheDocument();
    expect(within(statusSection).getByText('Fulfilled')).toBeInTheDocument();
  });

  it('renders and updates status filter', async () => {
    const user = userEvent.setup();
    render(<ProcurementWorkflowPage />);

    const statusFilter = screen.getByTestId('status-filter');
    expect(statusFilter).toHaveValue('all');

    await user.selectOptions(statusFilter, 'approved');
    expect(statusFilter).toHaveValue('approved');
  });

  it('renders and updates requester filter', async () => {
    const user = userEvent.setup();
    render(<ProcurementWorkflowPage />);

    const requesterFilter = screen.getByTestId('requester-filter');
    await user.type(requesterFilter, 'user-123');

    expect(requesterFilter).toHaveValue('user-123');
  });

  it('renders requests table rows', () => {
    render(<ProcurementWorkflowPage />);

    expect(screen.getByTestId('request-row-req-001')).toBeInTheDocument();
    expect(screen.getByTestId('request-row-req-002')).toBeInTheDocument();
    expect(screen.getByText('PR-2026-001')).toBeInTheDocument();
    expect(screen.getByText('PR-2026-002')).toBeInTheDocument();
  });

  it('renders status badges with mapped variants', () => {
    render(<ProcurementWorkflowPage />);

    const approvedBadge = screen.getByTestId('request-row-req-002').querySelector('span[data-variant]');
    expect(approvedBadge).toHaveAttribute('data-variant', 'success');

    const reviewBadge = screen.getByTestId('request-row-req-001').querySelector('span[data-variant]');
    expect(reviewBadge).toHaveAttribute('data-variant', 'warning');
  });

  it('renders priority styling markers', () => {
    render(<ProcurementWorkflowPage />);

    const highPriority = screen.getByTestId('priority-req-001');
    expect(highPriority).toHaveClass('text-orange-700');
  });

  it('shows list loading state when list query is loading', () => {
    vi.mocked(hooks.useProcurementList).mockReturnValue({
      data: undefined,
      isLoading: true,
      isError: false,
      refetch: vi.fn(),
    } as any);

    render(<ProcurementWorkflowPage />);
    expect(screen.getByText('Loading procurement requests...')).toBeInTheDocument();
  });

  it('shows empty state when no requests exist', () => {
    vi.mocked(hooks.useProcurementList).mockReturnValue({
      data: [],
      isLoading: false,
      isError: false,
      refetch: vi.fn(),
    } as any);

    render(<ProcurementWorkflowPage />);
    expect(screen.getByText('No procurement requests found')).toBeInTheDocument();
  });

  it('renders last updated footer', () => {
    render(<ProcurementWorkflowPage />);
    expect(screen.getByText(/Last updated:/)).toBeInTheDocument();
  });

  it('renders currency values in request table', () => {
    render(<ProcurementWorkflowPage />);
    expect(screen.getByText(/950,000/)).toBeInTheDocument();
    expect(screen.getByText(/1,500,000/)).toBeInTheDocument();
  });
});
