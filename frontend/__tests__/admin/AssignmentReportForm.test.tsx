/**
 * Tests: AssignmentReportForm (SubmitReportPage)
 */

import { beforeEach, describe, expect, it, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { AssignmentStatus } from '@/modules/rector-assignments/types';

vi.mock('@/shared/auth/permission-gate', () => ({
  RequirePermission: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}));

const mockPush = vi.fn();
vi.mock('next/navigation', () => ({
  useRouter: () => ({ push: mockPush, back: vi.fn() }),
  useParams: () => ({ id: '10' }),
}));

vi.mock('@/modules/rector-assignments/hooks', () => ({
  useRectorAssignmentDetail: vi.fn(),
  useSubmitReport: vi.fn(),
}));

import * as hooks from '@/modules/rector-assignments/hooks';
import SubmitReportPage from '@/app/(admin)/console/my-assignments/[id]/report/page';

function stubDetail(status = AssignmentStatus.IN_PROGRESS) {
  vi.mocked(hooks.useRectorAssignmentDetail).mockReturnValue({
    data: {
      id: '10',
      title: 'Test Assignment',
      status,
      priority: 'NORMAL',
      due_date: null,
      is_overdue: false,
      created_at: '2024-01-01T00:00:00Z',
      recurrence_type: 'NONE',
      description: null,
      assignees: [],
    },
    isLoading: false,
    isError: false,
  } as any);
}

function stubSubmit(mutateAsyncFn = vi.fn()) {
  vi.mocked(hooks.useSubmitReport).mockReturnValue({
    mutateAsync: mutateAsyncFn,
    isPending: false,
  } as any);
}

beforeEach(() => {
  vi.clearAllMocks();
  stubDetail();
  stubSubmit();
});

describe('SubmitReportPage', () => {
  it('shows form for eligible status', () => {
    render(<SubmitReportPage />);
    expect(screen.getByTestId('report-form')).toBeInTheDocument();
  });

  it('blocks form for ineligible status (DRAFT)', () => {
    stubDetail(AssignmentStatus.DRAFT);
    render(<SubmitReportPage />);
    expect(screen.queryByTestId('report-form')).not.toBeInTheDocument();
    expect(screen.getByText(/not available/i)).toBeInTheDocument();
  });

  it('shows validation error when summary is empty', async () => {
    const user = userEvent.setup();
    render(<SubmitReportPage />);
    await user.click(screen.getByTestId('submit-report-btn'));
    expect(screen.getByText(/summary is required/i)).toBeInTheDocument();
  });

  it('shows validation error when summary is too short', async () => {
    const user = userEvent.setup();
    render(<SubmitReportPage />);
    await user.type(screen.getByTestId('summary-input'), 'Too short');
    await user.click(screen.getByTestId('submit-report-btn'));
    expect(screen.getByText(/at least 10 characters/i)).toBeInTheDocument();
  });

  it('submits with valid summary and shows success state', async () => {
    const mutateAsync = vi.fn().mockResolvedValue({});
    stubSubmit(mutateAsync);
    const user = userEvent.setup();
    render(<SubmitReportPage />);

    await user.type(screen.getByTestId('summary-input'), 'This is a detailed execution summary that meets the minimum length requirement.');
    await user.click(screen.getByTestId('submit-report-btn'));

    expect(mutateAsync).toHaveBeenCalled();
    expect(screen.getByTestId('report-submitted-success')).toBeInTheDocument();
  });

  it('shows global error on API failure', async () => {
    const mutateAsync = vi.fn().mockRejectedValue(new Error('Network error'));
    stubSubmit(mutateAsync);
    const user = userEvent.setup();
    render(<SubmitReportPage />);

    await user.type(screen.getByTestId('summary-input'), 'This is a detailed execution summary of the task that was completed.');
    await user.click(screen.getByTestId('submit-report-btn'));

    expect(screen.getByTestId('global-error')).toBeInTheDocument();
  });

  it('allows RETURNED_FOR_REVISION status to submit report', () => {
    stubDetail(AssignmentStatus.RETURNED_FOR_REVISION);
    render(<SubmitReportPage />);
    expect(screen.getByTestId('report-form')).toBeInTheDocument();
  });
});
