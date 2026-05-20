/**
 * Tests: ExecutorAssignmentsPage (My Assignments)
 */

import { beforeEach, describe, expect, it, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { AssignmentStatus } from '@/modules/rector-assignments/types';

vi.mock('@/shared/auth/permission-gate', () => ({
  RequirePermission: ({ children }: { children: React.ReactNode }) => <>{children}</>,
  PermissionGate: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}));

vi.mock('next/navigation', () => ({
  useRouter: () => ({ push: vi.fn() }),
  useParams: () => ({}),
}));

vi.mock('@/modules/rector-assignments/hooks', () => ({
  useMyRectorAssignments: vi.fn(),
}));

import * as hooks from '@/modules/rector-assignments/hooks';
import MyAssignmentsPage from '@/app/(admin)/console/my-assignments/page';

function stubMyAssignments(assignments: unknown[] = []) {
  vi.mocked(hooks.useMyRectorAssignments).mockReturnValue({
    data: assignments,
    isLoading: false,
    isError: false,
  } as any);
}

beforeEach(() => {
  vi.clearAllMocks();
  stubMyAssignments();
});

describe('MyAssignmentsPage (Executor Inbox)', () => {
  it('shows loading state', () => {
    vi.mocked(hooks.useMyRectorAssignments).mockReturnValue({ data: undefined, isLoading: true, isError: false } as any);
    render(<MyAssignmentsPage />);
    expect(screen.getAllByText(/loading/i).length).toBeGreaterThan(0);
  });

  it('shows error state', () => {
    vi.mocked(hooks.useMyRectorAssignments).mockReturnValue({ data: undefined, isLoading: false, isError: true } as any);
    render(<MyAssignmentsPage />);
    expect(screen.getByText(/failed to load/i)).toBeInTheDocument();
  });

  it('shows empty state when no assignments', () => {
    render(<MyAssignmentsPage />);
    expect(screen.getByTestId('empty-my-assignments')).toBeInTheDocument();
  });

  it('renders assignment rows', () => {
    stubMyAssignments([
      {
        id: '5',
        title: 'My Task A',
        priority: 'HIGH',
        status: AssignmentStatus.IN_PROGRESS,
        due_date: '2025-12-31',
        is_overdue: false,
      },
    ]);
    render(<MyAssignmentsPage />);
    expect(screen.getByTestId('my-assignment-row-5')).toBeInTheDocument();
    expect(screen.getByText('My Task A')).toBeInTheDocument();
  });

  it('shows Submit Report link for eligible status', () => {
    stubMyAssignments([
      {
        id: '6',
        title: 'Eligible Task',
        priority: 'NORMAL',
        status: AssignmentStatus.IN_PROGRESS,
        due_date: null,
        is_overdue: false,
      },
    ]);
    render(<MyAssignmentsPage />);
    expect(screen.getByTestId('submit-report-6')).toBeInTheDocument();
  });

  it('shows urgent alert when an assignment is overdue', () => {
    stubMyAssignments([
      {
        id: '7',
        title: 'Overdue Task',
        priority: 'HIGH',
        status: AssignmentStatus.OVERDUE,
        due_date: '2024-01-01',
        is_overdue: true,
      },
    ]);
    render(<MyAssignmentsPage />);
    expect(screen.getByTestId('urgent-alert')).toBeInTheDocument();
  });

  it('does not show urgent alert when all assignments are current', () => {
    stubMyAssignments([
      {
        id: '8',
        title: 'Normal Task',
        priority: 'NORMAL',
        status: AssignmentStatus.IN_PROGRESS,
        due_date: '2026-01-01',
        is_overdue: false,
      },
    ]);
    render(<MyAssignmentsPage />);
    expect(screen.queryByTestId('urgent-alert')).not.toBeInTheDocument();
  });
});
