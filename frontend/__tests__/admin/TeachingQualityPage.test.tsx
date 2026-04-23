/**
 * Teaching Quality Page — Unit Tests
 * Validates rendering of quality analytics dashboard with all sections
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import TeachingQualityPage from '@/app/(admin)/console/teaching-quality/page';

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

vi.mock('@/modules/teaching-quality/hooks', () => ({
  useDepartmentQualityDashboard: vi.fn(),
  useQualityMetricsReport: vi.fn(),
  useQualityBenchmarks: vi.fn(),
  useRecordQualityMetric: vi.fn(),
}));

import * as hooks from '@/modules/teaching-quality/hooks';

const DEFAULT_REPORT = {
  term_id: 'current',
  report_generated_at: '2026-04-21T10:00:00Z',
  total_faculty_evaluated: 85,
  average_quality_score: 4.2,
  benchmarks: [
    {
      metric_name: 'Student Satisfaction',
      institutional_average: 4.1,
      departmental_average: 4.3,
      top_quartile: 4.7,
      bottom_quartile: 3.5,
      target_value: 4.0,
    },
  ],
  departments: [
    {
      department: 'Engineering',
      term_id: 'current',
      total_faculty: 28,
      average_quality_score: 4.35,
      above_target_count: 22,
      below_target_count: 6,
      improvement_opportunities: ['Enhance peer collaboration', 'Increase student engagement'],
      last_aggregated: '2026-04-21T10:00:00Z',
    },
  ],
  trending_metrics: [
    {
      metric_name: 'Overall Satisfaction',
      trend: 'up' as const,
      change_pct: 5.2,
    },
  ],
};

describe('TeachingQualityPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    stubDefaults();
  });

  function stubDefaults() {
    vi.mocked(hooks.useQualityMetricsReport).mockReturnValue({
      data: DEFAULT_REPORT,
      isLoading: false,
      isError: false,
      refetch: vi.fn(),
    } as any);

    vi.mocked(hooks.useQualityBenchmarks).mockReturnValue({
      data: DEFAULT_REPORT.benchmarks,
      isLoading: false,
      isError: false,
      refetch: vi.fn(),
    } as any);

    vi.mocked(hooks.useDepartmentQualityDashboard).mockReturnValue({
      data: undefined,
      isLoading: false,
      isError: false,
      refetch: vi.fn(),
    } as any);

    vi.mocked(hooks.useRecordQualityMetric).mockReturnValue({
      mutate: vi.fn(),
      isPending: false,
    } as any);
  }

  it('renders page heading with correct title', () => {
    render(<TeachingQualityPage />);
    expect(screen.getByText('Teaching Quality Analytics')).toBeInTheDocument();
  });

  it('shows loading state when data is loading', () => {
    vi.mocked(hooks.useQualityMetricsReport).mockReturnValue({
      data: undefined,
      isLoading: true,
      isError: false,
      refetch: vi.fn(),
    } as any);

    render(<TeachingQualityPage />);
    expect(screen.getByText(/Loading quality metrics/)).toBeInTheDocument();
  });

  it('renders quality summary cards with metrics', () => {
    render(<TeachingQualityPage />);

    const summarySection = screen.getByTestId('quality-summary-section');
    expect(summarySection).toBeInTheDocument();

    expect(screen.getByTestId('total-faculty-evaluated')).toHaveTextContent('85');
    expect(screen.getByTestId('average-quality-score')).toHaveTextContent('4.20/5.0');
  });

  it('renders benchmarks table with metric data', () => {
    render(<TeachingQualityPage />);

    const benchmarksSection = screen.getByTestId('benchmarks-section');
    expect(benchmarksSection).toBeInTheDocument();

    expect(screen.getByText('Student Satisfaction')).toBeInTheDocument();
    expect(screen.getByText('4.10')).toBeInTheDocument(); // institutional average
    expect(screen.getByText('4.30')).toBeInTheDocument(); // departmental average
  });

  it('renders department dashboard when available', () => {
    vi.mocked(hooks.useDepartmentQualityDashboard).mockReturnValue({
      data: {
        department: 'Engineering',
        term_id: 'current',
        total_faculty: 28,
        average_quality_score: 4.35,
        above_target_count: 22,
        below_target_count: 6,
        improvement_opportunities: ['Enhance peer collaboration'],
        last_aggregated: '2026-04-21T10:00:00Z',
      },
      isLoading: false,
      isError: false,
      refetch: vi.fn(),
    } as any);

    render(<TeachingQualityPage />);

    const deptSection = screen.getByTestId('department-dashboard-section');
    expect(deptSection).toBeInTheDocument();
    expect(screen.getByText('Department: Engineering')).toBeInTheDocument();
    expect(screen.getByText('28')).toBeInTheDocument();
  });

  it('renders trending metrics section', () => {
    render(<TeachingQualityPage />);

    const trendingSection = screen.getByTestId('trending-section');
    expect(trendingSection).toBeInTheDocument();

    expect(screen.getByText('Overall Satisfaction')).toBeInTheDocument();
    expect(screen.getByText('Change: 5.2%')).toBeInTheDocument();
  });

  it('displays trend badge with correct variant for up trend', () => {
    render(<TeachingQualityPage />);

    const badge = screen.getByText('↑ up');
    expect(badge).toHaveAttribute('data-variant', 'default');
  });

  it('shows error state when data fetch fails', () => {
    vi.mocked(hooks.useQualityMetricsReport).mockReturnValue({
      data: undefined,
      isLoading: false,
      isError: true,
      refetch: vi.fn(),
    } as any);

    render(<TeachingQualityPage />);
    expect(screen.getByText('Failed to load quality metrics')).toBeInTheDocument();
  });

  it('renders term selector dropdown', () => {
    render(<TeachingQualityPage />);
    const termSelect = screen.getByDisplayValue('Current Term');
    expect(termSelect).toBeInTheDocument();
    expect(termSelect).toHaveValue('current');
  });

  it('displays improvement opportunities for department', () => {
    vi.mocked(hooks.useDepartmentQualityDashboard).mockReturnValue({
      data: {
        department: 'Engineering',
        term_id: 'current',
        total_faculty: 28,
        average_quality_score: 4.35,
        above_target_count: 22,
        below_target_count: 6,
        improvement_opportunities: ['Enhance peer collaboration', 'Increase student engagement'],
        last_aggregated: '2026-04-21T10:00:00Z',
      },
      isLoading: false,
      isError: false,
      refetch: vi.fn(),
    } as any);

    render(<TeachingQualityPage />);

    expect(screen.getByText('Enhance peer collaboration')).toBeInTheDocument();
    expect(screen.getByText('Increase student engagement')).toBeInTheDocument();
  });
});
