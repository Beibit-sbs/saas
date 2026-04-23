/**
 * Faculty Workload Page — Unit Tests
 * Validates rendering of workload dashboard with all sections
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import FacultyWorkloadPage from '@/app/(admin)/console/workload/page';

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

vi.mock('@/modules/faculty-workload/hooks', () => ({
  useFacultyWorkload: vi.fn(),
  useWorkloadAlerts: vi.fn(),
  useDepartmentWorkload: vi.fn(),
  useWorkloadMetrics: vi.fn(),
  useUpdateFacultyCapacity: vi.fn(),
}));

import * as hooks from '@/modules/faculty-workload/hooks';

const DEFAULT_METRICS = {
  term_id: 'current',
  total_faculty: 42,
  average_utilization_pct: 76.5,
  median_utilization_pct: 75.0,
  min_utilization_pct: 40.0,
  max_utilization_pct: 95.0,
  utilization_std_dev: 15.3,
  alert_count_by_type: {
    underload: 3,
    overload: 5,
    max_credit_exceeded: 2,
  },
  departments: [
    {
      department: 'Computer Science',
      term_id: 'current',
      total_faculty: 12,
      average_utilization_pct: 80.0,
      underload_count: 1,
      overload_count: 2,
      max_credit_exceeded_count: 0,
      fairness_score: 0.82,
      last_updated: '2026-04-21T10:30:00Z',
    },
  ],
};

const DEFAULT_ALERTS = [
  {
    faculty_id: 'f001',
    faculty_name: 'Dr. Smith',
    department: 'Computer Science',
    term_id: 'current',
    alert_type: 'overload' as const,
    total_credit_hours: 18,
    threshold_value: 15,
    severity: 'high' as const,
    created_at: '2026-04-21T10:00:00Z',
  },
];

describe('FacultyWorkloadPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    stubDefaults();
  });

  function stubDefaults() {
    vi.mocked(hooks.useWorkloadMetrics).mockReturnValue({
      data: DEFAULT_METRICS,
      isLoading: false,
      isError: false,
      refetch: vi.fn(),
    } as any);

    vi.mocked(hooks.useWorkloadAlerts).mockReturnValue({
      data: DEFAULT_ALERTS,
      isLoading: false,
      isError: false,
      refetch: vi.fn(),
    } as any);

    vi.mocked(hooks.useDepartmentWorkload).mockReturnValue({
      data: undefined,
      isLoading: false,
      isError: false,
      refetch: vi.fn(),
    } as any);

    vi.mocked(hooks.useUpdateFacultyCapacity).mockReturnValue({
      mutate: vi.fn(),
      isPending: false,
    } as any);
  }

  it('renders page heading with correct title', () => {
    render(<FacultyWorkloadPage />);
    expect(screen.getByText('Faculty Workload Planning')).toBeInTheDocument();
  });

  it('shows loading state when data is loading', () => {
    vi.mocked(hooks.useWorkloadMetrics).mockReturnValue({
      data: undefined,
      isLoading: true,
      isError: false,
      refetch: vi.fn(),
    } as any);

    render(<FacultyWorkloadPage />);
    expect(screen.getByText(/Loading workload data/)).toBeInTheDocument();
  });

  it('renders workload summary cards with metrics', () => {
    render(<FacultyWorkloadPage />);

    const summarySection = screen.getByTestId('workload-summary-section');
    expect(summarySection).toBeInTheDocument();

    expect(screen.getByTestId('total-faculty')).toHaveTextContent('42');
    expect(screen.getByTestId('avg-utilization')).toHaveTextContent('76.5%');
    expect(screen.getByTestId('underload-count')).toHaveTextContent('3');
    expect(screen.getByTestId('overload-count')).toHaveTextContent('5');
  });

  it('renders alerts section with alert list', () => {
    render(<FacultyWorkloadPage />);

    const alertsSection = screen.getByTestId('alerts-section');
    expect(alertsSection).toBeInTheDocument();

    expect(screen.getByText('Dr. Smith')).toBeInTheDocument();
    expect(screen.getByText('Computer Science • 18 credit hours')).toBeInTheDocument();
  });

  it('displays alert badge with correct severity styling', () => {
    render(<FacultyWorkloadPage />);

    const badge = screen.getByText('overload');
    expect(badge).toHaveAttribute('data-variant', 'destructive');
  });

  it('renders utilization distribution statistics', () => {
    render(<FacultyWorkloadPage />);

    const distribution = screen.getByTestId('utilization-distribution');
    expect(distribution).toBeInTheDocument();

    expect(screen.getByText('40.0%')).toBeInTheDocument(); // min
    expect(screen.getByText('75.0%')).toBeInTheDocument(); // median
    expect(screen.getByText('95.0%')).toBeInTheDocument(); // max
    expect(screen.getByText('15.30')).toBeInTheDocument(); // std dev
  });

  it('renders department summary when available', () => {
    vi.mocked(hooks.useDepartmentWorkload).mockReturnValue({
      data: {
        department: 'Computer Science',
        term_id: 'current',
        total_faculty: 12,
        average_utilization_pct: 80.0,
        underload_count: 1,
        overload_count: 2,
        max_credit_exceeded_count: 0,
        fairness_score: 0.82,
        last_updated: '2026-04-21T10:30:00Z',
      },
      isLoading: false,
      isError: false,
      refetch: vi.fn(),
    } as any);

    render(<FacultyWorkloadPage />);

    const deptSummary = screen.getByTestId('department-summary-section');
    expect(deptSummary).toBeInTheDocument();
    expect(screen.getByText('Department: Computer Science')).toBeInTheDocument();
    expect(screen.getByText('80.0%')).toBeInTheDocument();
  });

  it('shows error state when data fetch fails', () => {
    vi.mocked(hooks.useWorkloadMetrics).mockReturnValue({
      data: undefined,
      isLoading: false,
      isError: true,
      refetch: vi.fn(),
    } as any);

    render(<FacultyWorkloadPage />);
    expect(screen.getByText('Failed to load workload data')).toBeInTheDocument();
  });

  it('hides alerts section when no alerts present', () => {
    vi.mocked(hooks.useWorkloadAlerts).mockReturnValue({
      data: [],
      isLoading: false,
      isError: false,
      refetch: vi.fn(),
    } as any);

    render(<FacultyWorkloadPage />);
    expect(screen.queryByTestId('alerts-section')).not.toBeInTheDocument();
  });

  it('renders term selector dropdown', () => {
    render(<FacultyWorkloadPage />);
    const termSelect = screen.getByDisplayValue('Current Term');
    expect(termSelect).toBeInTheDocument();
    expect(termSelect).toHaveValue('current');
  });
});
