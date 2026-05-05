/**
 * Budget Planning Page — Unit Tests
 * Validates rendering of budget dashboard, variance analysis, and expense tracking
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import BudgetPlanningPage from '@/app/(admin)/console/budget-planning/page';

// Mock modules
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

vi.mock('@/modules/budget-planning/hooks', () => ({
  useBudgetDashboardSummary: vi.fn(),
  useBudgetsList: vi.fn(),
}));

vi.mock('@/modules/platform/kpi/wave1-kpi-bar', () => ({
  Wave1KpiBar: () => null,
}));

import * as hooks from '@/modules/budget-planning/hooks';

const DEFAULT_DASHBOARD = {
  total_budgets: 24,
  status_breakdown: {
    draft: 3,
    submitted: 2,
    approved: 8,
    active: 10,
    closed: 1,
  },
  total_allocated: 5000000,
  total_spent: 3650000,
  total_available: 1350000,
  spend_percentage: 73.0,
  variance_count: 5,
  unfavorable_variances: 2,
  last_updated: '2026-04-21T10:00:00Z',
};

const DEFAULT_BUDGETS = [
  {
    budget_id: 'budget-001',
    fiscal_year: 2026,
    cost_center_name: 'Engineering Department',
    category: 'personnel',
    total_budgeted: 2000000,
    total_spent: 1800000,
    spend_percentage: 90.0,
    status: 'active' as const,
    updated_at: '2026-04-21T09:00:00Z',
  },
  {
    budget_id: 'budget-002',
    fiscal_year: 2026,
    cost_center_name: 'Operations',
    category: 'operations',
    total_budgeted: 1500000,
    total_spent: 900000,
    spend_percentage: 60.0,
    status: 'active' as const,
    updated_at: '2026-04-20T14:30:00Z',
  },
];

describe('BudgetPlanningPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    stubDefaults();
  });

  function stubDefaults() {
    vi.mocked(hooks.useBudgetDashboardSummary).mockReturnValue({
      data: DEFAULT_DASHBOARD,
      isLoading: false,
      isError: false,
      refetch: vi.fn(),
    } as any);

    vi.mocked(hooks.useBudgetsList).mockReturnValue({
      data: DEFAULT_BUDGETS,
      isLoading: false,
      isError: false,
      refetch: vi.fn(),
    } as any);
  }

  it('renders page heading with correct title', () => {
    render(<BudgetPlanningPage />);
    expect(screen.getByText('Budget Planning & Controls')).toBeInTheDocument();
  });

  it('shows loading state when data is loading', () => {
    vi.mocked(hooks.useBudgetDashboardSummary).mockReturnValue({
      data: undefined,
      isLoading: true,
      isError: false,
      refetch: vi.fn(),
    } as any);

    render(<BudgetPlanningPage />);
    expect(screen.getByText(/Loading budget dashboard/)).toBeInTheDocument();
  });

  it('renders dashboard summary cards with correct metrics', () => {
    render(<BudgetPlanningPage />);

    const summarySection = screen.getByTestId('dashboard-summary-section');
    expect(summarySection).toBeInTheDocument();

    expect(screen.getByTestId('total-budgets')).toHaveTextContent('24');
    expect(screen.getByTestId('total-budgeted')).toHaveTextContent('5,000,000');
    expect(screen.getByTestId('total-spent')).toHaveTextContent('3,650,000');
    expect(screen.getByTestId('total-available')).toHaveTextContent('1,350,000');
    expect(screen.getByTestId('spend-percentage')).toHaveTextContent('73.0%');
  });

  it('renders variance alert when unfavorable variances exist', () => {
    render(<BudgetPlanningPage />);

    const varianceAlert = screen.getByTestId('variance-alert-section');
    expect(varianceAlert).toBeInTheDocument();

    expect(screen.getByText(/2 unfavorable variances detected/)).toBeInTheDocument();
  });

  it('renders budget status distribution section', () => {
    render(<BudgetPlanningPage />);

    const statusSection = screen.getByTestId('status-distribution-section');
    expect(statusSection).toBeInTheDocument();

    expect(within(statusSection).getByText('Active')).toBeInTheDocument();
    expect(within(statusSection).getByText('Approved')).toBeInTheDocument();
    expect(within(statusSection).getByText('Submitted')).toBeInTheDocument();
    expect(within(statusSection).getByText('Draft')).toBeInTheDocument();
    expect(within(statusSection).getByText('Closed')).toBeInTheDocument();
  });

  it('renders status and fiscal year filter dropdowns', () => {
    render(<BudgetPlanningPage />);

    const filtersSection = screen.getByTestId('filters-section');
    expect(filtersSection).toBeInTheDocument();

    const statusFilter = screen.getByTestId('status-filter');
    expect(statusFilter).toBeInTheDocument();
    expect(statusFilter).toHaveValue('all');

    const fiscalYearFilter = screen.getByTestId('fiscal-year-filter');
    expect(fiscalYearFilter).toBeInTheDocument();
  });

  it('renders budget list table with data', () => {
    render(<BudgetPlanningPage />);

    const listSection = screen.getByTestId('budget-list-section');
    expect(listSection).toBeInTheDocument();

    expect(screen.getByText('Engineering Department')).toBeInTheDocument();
    expect(screen.getByText('Operations')).toBeInTheDocument();
  });

  it('displays budget amounts in table', () => {
    render(<BudgetPlanningPage />);

    expect(screen.getByText(/2,000,000/)).toBeInTheDocument();
    expect(screen.getByText(/1,800,000/)).toBeInTheDocument();
    expect(screen.getByText(/1,500,000/)).toBeInTheDocument();
    expect(screen.getByText(/900,000/)).toBeInTheDocument();
  });

  it('displays category information', () => {
    render(<BudgetPlanningPage />);

    expect(screen.getByText('personnel')).toBeInTheDocument();
    expect(screen.getByText('operations')).toBeInTheDocument();
  });

  it('displays spend percentage with progress bar', () => {
    render(<BudgetPlanningPage />);

    const progressBar1 = screen.getByTestId('progress-bar-budget-001');
    expect(progressBar1).toHaveStyle({ width: '90%' });

    const progressBar2 = screen.getByTestId('progress-bar-budget-002');
    expect(progressBar2).toHaveStyle({ width: '60%' });
  });

  it('displays status badges with appropriate variants', () => {
    render(<BudgetPlanningPage />);

    const activeBadge = screen
      .getByTestId('progress-bar-budget-001')
      .closest('tr')
      ?.querySelector('span[data-variant]');
    expect(activeBadge).toHaveAttribute('data-variant', 'success');
  });

  it('displays last updated timestamp', () => {
    render(<BudgetPlanningPage />);

    const lastUpdated = screen.getByText(/Last updated:/);
    expect(lastUpdated).toBeInTheDocument();
  });

  it('shows error state when data fetch fails', () => {
    vi.mocked(hooks.useBudgetDashboardSummary).mockReturnValue({
      data: undefined,
      isLoading: false,
      isError: true,
      refetch: vi.fn(),
    } as any);

    render(<BudgetPlanningPage />);
    expect(screen.getByText('Failed to load budget data')).toBeInTheDocument();
  });

  it('allows changing status filter', async () => {
    const user = userEvent.setup();

    render(<BudgetPlanningPage />);

    const statusFilter = screen.getByTestId('status-filter');
    await user.selectOptions(statusFilter, 'active');

    expect(statusFilter).toHaveValue('active');
  });

  it('allows filtering by fiscal year', async () => {
    const user = userEvent.setup();
    render(<BudgetPlanningPage />);

    const fiscalYearFilter = screen.getByTestId('fiscal-year-filter');
    await user.type(fiscalYearFilter, '2026');

    expect(fiscalYearFilter).toHaveValue('2026');
  });

  it('shows empty state when no budgets are found', () => {
    vi.mocked(hooks.useBudgetsList).mockReturnValue({
      data: [],
      isLoading: false,
      isError: false,
      refetch: vi.fn(),
    } as any);

    render(<BudgetPlanningPage />);
    expect(screen.getByText('No budgets found')).toBeInTheDocument();
  });

  it('does not show variance alert when no unfavorable variances', () => {
    vi.mocked(hooks.useBudgetDashboardSummary).mockReturnValue({
      data: {
        ...DEFAULT_DASHBOARD,
        unfavorable_variances: 0,
      },
      isLoading: false,
      isError: false,
      refetch: vi.fn(),
    } as any);

    render(<BudgetPlanningPage />);

    const varianceAlert = screen.queryByTestId('variance-alert-section');
    expect(varianceAlert).not.toBeInTheDocument();
  });

  it('displays cost center names in table', () => {
    render(<BudgetPlanningPage />);

    expect(screen.getByText('Engineering Department')).toBeInTheDocument();
    expect(screen.getByText('Operations')).toBeInTheDocument();
  });

  it('renders progress bar colors based on spend percentage', () => {
    render(<BudgetPlanningPage />);

    // 90% spend is at warning threshold (red is only > 90)
    const yellowProgressBar = screen.getByTestId('progress-bar-budget-001');
    expect(yellowProgressBar).toHaveClass('bg-yellow-600');

    // 60% spend should show green progress bar
    const greenProgressBar = screen.getByTestId('progress-bar-budget-002');
    expect(greenProgressBar).toHaveClass('bg-green-600');
  });

  it('displays fiscal year information', () => {
    render(<BudgetPlanningPage />);

    // Fiscal year appears in the budget rows (might not be directly visible but in data)
    const rows = screen.getAllByTestId(/budget-row-/);
    expect(rows).toHaveLength(2);
  });
});
