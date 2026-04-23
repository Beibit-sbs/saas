/**
 * Syllabus Governance Page — Unit Tests
 * Validates rendering of syllabus lifecycle and approval workflow dashboard
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import SyllabusGovernancePage from '@/app/(admin)/console/syllabus-governance/page';

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

vi.mock('@/modules/syllabus-governance/hooks', () => ({
  useSyllabusDashboardSummary: vi.fn(),
  useSyllabusList: vi.fn(),
  useApprovalWorkflow: vi.fn(),
}));

import * as hooks from '@/modules/syllabus-governance/hooks';

const DEFAULT_DASHBOARD = {
  total_syllabi: 124,
  status_breakdown: {
    draft: 15,
    under_review: 8,
    approved: 32,
    published: 65,
    archived: 4,
  },
  pending_approvals: 8,
  expiring_syllabi: 3,
  last_updated: '2026-04-21T10:00:00Z',
};

const DEFAULT_SYLLABI = [
  {
    syllabi_id: 'syll-001',
    course_code: 'CS101',
    course_title: 'Introduction to Computer Science',
    faculty_name: 'Dr. Smith',
    status: 'published' as const,
    term_id: 'Spring2026',
    updated_at: '2026-04-21T09:00:00Z',
  },
  {
    syllabi_id: 'syll-002',
    course_code: 'MATH201',
    course_title: 'Calculus II',
    faculty_name: 'Dr. Johnson',
    status: 'under_review' as const,
    term_id: 'Spring2026',
    updated_at: '2026-04-20T14:30:00Z',
  },
];

describe('SyllabusGovernancePage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    stubDefaults();
  });

  function stubDefaults() {
    vi.mocked(hooks.useSyllabusDashboardSummary).mockReturnValue({
      data: DEFAULT_DASHBOARD,
      isLoading: false,
      isError: false,
      refetch: vi.fn(),
    } as any);

    vi.mocked(hooks.useSyllabusList).mockReturnValue({
      data: DEFAULT_SYLLABI,
      isLoading: false,
      isError: false,
      refetch: vi.fn(),
    } as any);

    vi.mocked(hooks.useApprovalWorkflow).mockReturnValue({
      data: undefined,
      isLoading: false,
      isError: false,
      refetch: vi.fn(),
    } as any);
  }

  it('renders page heading with correct title', () => {
    render(<SyllabusGovernancePage />);
    expect(screen.getByText('Syllabus Governance')).toBeInTheDocument();
  });

  it('shows loading state when data is loading', () => {
    vi.mocked(hooks.useSyllabusDashboardSummary).mockReturnValue({
      data: undefined,
      isLoading: true,
      isError: false,
      refetch: vi.fn(),
    } as any);

    render(<SyllabusGovernancePage />);
    expect(screen.getByText(/Loading syllabus governance dashboard/)).toBeInTheDocument();
  });

  it('renders dashboard summary cards with correct metrics', () => {
    render(<SyllabusGovernancePage />);

    const summarySection = screen.getByTestId('dashboard-summary-section');
    expect(summarySection).toBeInTheDocument();

    expect(screen.getByTestId('total-syllabi')).toHaveTextContent('124');
    expect(screen.getByTestId('published-count')).toHaveTextContent('65');
    expect(screen.getByTestId('under-review-count')).toHaveTextContent('8');
    expect(screen.getByTestId('draft-count')).toHaveTextContent('15');
    expect(screen.getByTestId('pending-approvals')).toHaveTextContent('8');
  });

  it('renders alerts section when there are expiring syllabi', () => {
    render(<SyllabusGovernancePage />);

    const alertsSection = screen.getByTestId('alerts-section');
    expect(alertsSection).toBeInTheDocument();

    expect(screen.getByText(/3 syllabi are expiring soon/)).toBeInTheDocument();
  });

  it('renders status and department filter dropdowns', () => {
    render(<SyllabusGovernancePage />);

    const filtersSection = screen.getByTestId('filters-section');
    expect(filtersSection).toBeInTheDocument();

    const statusFilter = screen.getByTestId('status-filter');
    expect(statusFilter).toBeInTheDocument();
    expect(statusFilter).toHaveValue('all');

    const departmentFilter = screen.getByTestId('department-filter');
    expect(departmentFilter).toBeInTheDocument();
  });

  it('renders syllabi list table with data', () => {
    render(<SyllabusGovernancePage />);

    const listSection = screen.getByTestId('syllabi-list-section');
    expect(listSection).toBeInTheDocument();

    expect(screen.getByText('CS101')).toBeInTheDocument();
    expect(screen.getByText('Introduction to Computer Science')).toBeInTheDocument();
    expect(screen.getByText('Dr. Smith')).toBeInTheDocument();

    expect(screen.getByText('MATH201')).toBeInTheDocument();
    expect(screen.getByText('Calculus II')).toBeInTheDocument();
    expect(screen.getByText('Dr. Johnson')).toBeInTheDocument();
  });

  it('displays status badges with appropriate variants', () => {
    render(<SyllabusGovernancePage />);

    const publishedBadge = screen.getByTestId('syllabus-row-syll-001').querySelector('span[data-variant]');
    expect(publishedBadge).toHaveAttribute('data-variant', 'success');

    const reviewBadge = screen.getByTestId('syllabus-row-syll-002').querySelector('span[data-variant]');
    expect(reviewBadge).toHaveAttribute('data-variant', 'warning');
  });

  it('displays last updated timestamp', () => {
    render(<SyllabusGovernancePage />);

    const lastUpdated = screen.getByText(/Last updated:/);
    expect(lastUpdated).toBeInTheDocument();
  });

  it('shows error state when data fetch fails', () => {
    vi.mocked(hooks.useSyllabusDashboardSummary).mockReturnValue({
      data: undefined,
      isLoading: false,
      isError: true,
      refetch: vi.fn(),
    } as any);

    render(<SyllabusGovernancePage />);
    expect(screen.getByText('Failed to load syllabus dashboard')).toBeInTheDocument();
  });

  it('allows changing status filter', async () => {
    const user = userEvent.setup();
    const mockRefetch = vi.fn();

    vi.mocked(hooks.useSyllabusList).mockReturnValue({
      data: DEFAULT_SYLLABI,
      isLoading: false,
      isError: false,
      refetch: mockRefetch,
    } as any);

    render(<SyllabusGovernancePage />);

    const statusFilter = screen.getByTestId('status-filter');
    await user.selectOptions(statusFilter, 'published');

    expect(statusFilter).toHaveValue('published');
  });

  it('allows filtering by department', async () => {
    const user = userEvent.setup();
    render(<SyllabusGovernancePage />);

    const departmentFilter = screen.getByTestId('department-filter');
    await user.type(departmentFilter, 'Engineering');

    expect(departmentFilter).toHaveValue('Engineering');
  });

  it('shows empty state when no syllabi are found', () => {
    vi.mocked(hooks.useSyllabusList).mockReturnValue({
      data: [],
      isLoading: false,
      isError: false,
      refetch: vi.fn(),
    } as any);

    render(<SyllabusGovernancePage />);
    expect(screen.getByText('No syllabi found')).toBeInTheDocument();
  });

  it('renders course codes and titles correctly', () => {
    render(<SyllabusGovernancePage />);

    // Verify course code and title are both displayed
    expect(screen.getByText('CS101')).toBeInTheDocument();
    expect(screen.getByText('Introduction to Computer Science')).toBeInTheDocument();

    expect(screen.getByText('MATH201')).toBeInTheDocument();
    expect(screen.getByText('Calculus II')).toBeInTheDocument();
  });
});
