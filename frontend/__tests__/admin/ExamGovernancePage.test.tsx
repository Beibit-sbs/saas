/**
 * Exam Governance Page — Unit Tests
 * Validates rendering of exam scheduling, proctoring, and accessibility dashboard
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import ExamGovernancePage from '@/app/(admin)/console/exam-governance/page';

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

vi.mock("@/modules/platform/kpi/wave1-kpi-bar", () => ({
  Wave1KpiBar: () => <div data-testid="wave1-kpi-bar-mock" />,
}));

vi.mock("@/shared/auth/context", () => ({
  useAdminAuth: () => ({
    adminToken: "test-admin-token",
    isAuthenticated: true,
    isLoading: false,
    login: vi.fn(),
    logout: vi.fn(),
  }),
}));

vi.mock('@/modules/exam-governance/hooks', () => ({
  useExamDashboardSummary: vi.fn(),
  useExamsList: vi.fn(),
  useExamStatistics: vi.fn(),
}));

import * as hooks from '@/modules/exam-governance/hooks';

const DEFAULT_DASHBOARD = {
  total_exams: 48,
  status_breakdown: {
    scheduled: 12,
    in_progress: 2,
    completed: 32,
    cancelled: 2,
  },
  upcoming_exams_count: 6,
  proctors_needed: 4,
  students_with_accommodations: 23,
  last_updated: '2026-04-21T10:00:00Z',
};

const DEFAULT_EXAMS = [
  {
    exam_id: 'exam-001',
    course_code: 'CS101',
    course_title: 'Introduction to Computer Science',
    faculty_name: 'Dr. Smith',
    exam_type: 'midterm',
    scheduled_date: '2026-04-25T09:00:00Z',
    status: 'scheduled' as const,
    registered_count: 45,
    updated_at: '2026-04-21T09:00:00Z',
  },
  {
    exam_id: 'exam-002',
    course_code: 'MATH201',
    course_title: 'Calculus II',
    faculty_name: 'Dr. Johnson',
    exam_type: 'final',
    scheduled_date: '2026-05-10T14:00:00Z',
    status: 'scheduled' as const,
    registered_count: 38,
    updated_at: '2026-04-20T14:30:00Z',
  },
];

describe('ExamGovernancePage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    stubDefaults();
  });

  function stubDefaults() {
    vi.mocked(hooks.useExamDashboardSummary).mockReturnValue({
      data: DEFAULT_DASHBOARD,
      isLoading: false,
      isError: false,
      refetch: vi.fn(),
    } as any);

    vi.mocked(hooks.useExamsList).mockReturnValue({
      data: DEFAULT_EXAMS,
      isLoading: false,
      isError: false,
      refetch: vi.fn(),
    } as any);

    vi.mocked(hooks.useExamStatistics).mockReturnValue({
      data: undefined,
      isLoading: false,
      isError: false,
      refetch: vi.fn(),
    } as any);
  }

  it('renders page heading with correct title', () => {
    render(<ExamGovernancePage />);
    expect(screen.getByText('Exam Governance')).toBeInTheDocument();
  });

  it('shows loading state when data is loading', () => {
    vi.mocked(hooks.useExamDashboardSummary).mockReturnValue({
      data: undefined,
      isLoading: true,
      isError: false,
      refetch: vi.fn(),
    } as any);

    render(<ExamGovernancePage />);
    expect(screen.getByText(/Loading exam governance dashboard/)).toBeInTheDocument();
  });

  it('renders dashboard summary cards with correct metrics', () => {
    render(<ExamGovernancePage />);

    const summarySection = screen.getByTestId('dashboard-summary-section');
    expect(summarySection).toBeInTheDocument();

    expect(screen.getByTestId('total-exams')).toHaveTextContent('48');
    expect(screen.getByTestId('scheduled-count')).toHaveTextContent('12');
    expect(screen.getByTestId('in-progress-count')).toHaveTextContent('2');
    expect(screen.getByTestId('completed-count')).toHaveTextContent('32');
    expect(screen.getByTestId('proctors-needed')).toHaveTextContent('4');
  });

  it('renders accessibility accommodations alert', () => {
    render(<ExamGovernancePage />);

    const accommodationsAlert = screen.getByTestId('accommodations-alert-section');
    expect(accommodationsAlert).toBeInTheDocument();

    expect(screen.getByText(/23 students with registered accessibility accommodations/)).toBeInTheDocument();
  });

  it('renders upcoming exams alert', () => {
    render(<ExamGovernancePage />);

    const upcomingAlert = screen.getByTestId('upcoming-exams-alert-section');
    expect(upcomingAlert).toBeInTheDocument();

    expect(screen.getByText(/6 exams scheduled in the next 7 days/)).toBeInTheDocument();
  });

  it('renders status and term filter dropdowns', () => {
    render(<ExamGovernancePage />);

    const filtersSection = screen.getByTestId('filters-section');
    expect(filtersSection).toBeInTheDocument();

    const statusFilter = screen.getByTestId('status-filter');
    expect(statusFilter).toBeInTheDocument();
    expect(statusFilter).toHaveValue('all');

    const termFilter = screen.getByTestId('term-filter');
    expect(termFilter).toBeInTheDocument();
  });

  it('renders exams list table with data', () => {
    render(<ExamGovernancePage />);

    const listSection = screen.getByTestId('exams-list-section');
    expect(listSection).toBeInTheDocument();

    expect(screen.getByText('CS101')).toBeInTheDocument();
    expect(screen.getByText('Introduction to Computer Science')).toBeInTheDocument();
    expect(screen.getByText('Dr. Smith')).toBeInTheDocument();

    expect(screen.getByText('MATH201')).toBeInTheDocument();
    expect(screen.getByText('Calculus II')).toBeInTheDocument();
    expect(screen.getByText('Dr. Johnson')).toBeInTheDocument();
  });

  it('displays exam types correctly', () => {
    render(<ExamGovernancePage />);

    expect(screen.getByText('midterm')).toBeInTheDocument();
    expect(screen.getByText('final')).toBeInTheDocument();
  });

  it('displays registration counts', () => {
    render(<ExamGovernancePage />);

    const row1 = screen.getByTestId('exam-row-exam-001');
    expect(row1).toHaveTextContent('45');

    const row2 = screen.getByTestId('exam-row-exam-002');
    expect(row2).toHaveTextContent('38');
  });

  it('displays status badges with appropriate variants', () => {
    render(<ExamGovernancePage />);

    const scheduledBadge = screen.getByTestId('exam-row-exam-001').querySelector('span[data-variant]');
    expect(scheduledBadge).toHaveAttribute('data-variant', 'info');
  });

  it('displays last updated timestamp', () => {
    render(<ExamGovernancePage />);

    const lastUpdated = screen.getByText(/Last updated:/);
    expect(lastUpdated).toBeInTheDocument();
  });

  it('shows error state when data fetch fails', () => {
    vi.mocked(hooks.useExamDashboardSummary).mockReturnValue({
      data: undefined,
      isLoading: false,
      isError: true,
      refetch: vi.fn(),
    } as any);

    render(<ExamGovernancePage />);
    expect(screen.getByText('Failed to load exam dashboard')).toBeInTheDocument();
  });

  it('allows changing status filter', async () => {
    const user = userEvent.setup();

    render(<ExamGovernancePage />);

    const statusFilter = screen.getByTestId('status-filter');
    await user.selectOptions(statusFilter, 'completed');

    expect(statusFilter).toHaveValue('completed');
  });

  it('allows filtering by term', async () => {
    const user = userEvent.setup();
    render(<ExamGovernancePage />);

    const termFilter = screen.getByTestId('term-filter');
    await user.type(termFilter, 'Spring2026');

    expect(termFilter).toHaveValue('Spring2026');
  });

  it('shows empty state when no exams are found', () => {
    vi.mocked(hooks.useExamsList).mockReturnValue({
      data: [],
      isLoading: false,
      isError: false,
      refetch: vi.fn(),
    } as any);

    render(<ExamGovernancePage />);
    expect(screen.getByText('No exams found')).toBeInTheDocument();
  });

  it('renders course codes and titles correctly in table', () => {
    render(<ExamGovernancePage />);

    // Verify course code and title are both displayed
    expect(screen.getByText('CS101')).toBeInTheDocument();
    expect(screen.getByText('Introduction to Computer Science')).toBeInTheDocument();

    expect(screen.getByText('MATH201')).toBeInTheDocument();
    expect(screen.getByText('Calculus II')).toBeInTheDocument();
  });

  it('does not show accommodations alert when count is zero', () => {
    vi.mocked(hooks.useExamDashboardSummary).mockReturnValue({
      data: {
        ...DEFAULT_DASHBOARD,
        students_with_accommodations: 0,
      },
      isLoading: false,
      isError: false,
      refetch: vi.fn(),
    } as any);

    render(<ExamGovernancePage />);

    const accommodationsAlert = screen.queryByTestId('accommodations-alert-section');
    expect(accommodationsAlert).not.toBeInTheDocument();
  });

  it('does not show upcoming exams alert when count is zero', () => {
    vi.mocked(hooks.useExamDashboardSummary).mockReturnValue({
      data: {
        ...DEFAULT_DASHBOARD,
        upcoming_exams_count: 0,
      },
      isLoading: false,
      isError: false,
      refetch: vi.fn(),
    } as any);

    render(<ExamGovernancePage />);

    const upcomingAlert = screen.queryByTestId('upcoming-exams-alert-section');
    expect(upcomingAlert).not.toBeInTheDocument();
  });
});
