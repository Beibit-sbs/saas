/**
 * Tests: AssignmentDetailPage
 */

import { beforeEach, describe, expect, it, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { AssignmentStatus } from '@/modules/rector-assignments/types';

vi.mock('@/shared/auth/permission-gate', () => ({
  RequirePermission: ({ children }: { children: React.ReactNode }) => <>{children}</>,
  PermissionGate: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}));

vi.mock('next/navigation', () => ({
  useRouter: () => ({ push: vi.fn(), back: vi.fn() }),
  useParams: () => ({ id: '42' }),
}));

vi.mock('@/modules/rector-assignments/hooks', () => ({
  useRectorAssignmentDetail: vi.fn(),
  useAssignmentStatusHistory: vi.fn(),
  useAssignmentComments: vi.fn(),
  useAssignmentEvidence: vi.fn(),
  useAssignmentReports: vi.fn(),
  useAssignmentAudit: vi.fn(),
  useAssignAssignment: vi.fn(),
  useAcceptAssignment: vi.fn(),
  useReturnAssignment: vi.fn(),
  useCompleteAssignment: vi.fn(),
  useEscalateAssignment: vi.fn(),
  useCancelAssignment: vi.fn(),
  useArchiveAssignment: vi.fn(),
  useAddComment: vi.fn(),
}));

import * as hooks from '@/modules/rector-assignments/hooks';
import AssignmentDetailPage from '@/app/(admin)/console/rector-assignments/[id]/page';

function noopMutation() {
  return { mutate: vi.fn(), mutateAsync: vi.fn(), isPending: false };
}

function stubDetail(statusOverride: AssignmentStatus = AssignmentStatus.IN_PROGRESS, extra = {}) {
  vi.mocked(hooks.useRectorAssignmentDetail).mockReturnValue({
    data: {
      id: '42',
      title: 'Test Assignment',
      description: 'A description',
      status: statusOverride,
      priority: 'NORMAL',
      due_date: '2025-12-31',
      is_overdue: false,
      created_at: '2024-01-01T00:00:00Z',
      recurrence_type: 'NONE',
      assignees: [],
      ...extra,
    },
    isLoading: false,
    isError: false,
  } as any);
}

beforeEach(() => {
  vi.clearAllMocks();
  stubDetail();
  vi.mocked(hooks.useAssignmentStatusHistory).mockReturnValue({ data: [], isLoading: false, isError: false } as any);
  vi.mocked(hooks.useAssignmentComments).mockReturnValue({ data: [], isLoading: false, isError: false } as any);
  vi.mocked(hooks.useAssignmentEvidence).mockReturnValue({ data: [], isLoading: false, isError: false } as any);
  vi.mocked(hooks.useAssignmentReports).mockReturnValue({ data: [], isLoading: false, isError: false } as any);
  vi.mocked(hooks.useAssignmentAudit).mockReturnValue({ data: [], isLoading: false, isError: false } as any);
  vi.mocked(hooks.useAssignAssignment).mockReturnValue(noopMutation() as any);
  vi.mocked(hooks.useAcceptAssignment).mockReturnValue(noopMutation() as any);
  vi.mocked(hooks.useReturnAssignment).mockReturnValue(noopMutation() as any);
  vi.mocked(hooks.useCompleteAssignment).mockReturnValue(noopMutation() as any);
  vi.mocked(hooks.useEscalateAssignment).mockReturnValue(noopMutation() as any);
  vi.mocked(hooks.useCancelAssignment).mockReturnValue(noopMutation() as any);
  vi.mocked(hooks.useArchiveAssignment).mockReturnValue(noopMutation() as any);
  vi.mocked(hooks.useAddComment).mockReturnValue(noopMutation() as any);
});

describe('AssignmentDetailPage', () => {
  it('shows loading state', () => {
    vi.mocked(hooks.useRectorAssignmentDetail).mockReturnValue({ data: undefined, isLoading: true, isError: false } as any);
    render(<AssignmentDetailPage />);
    expect(screen.getAllByText(/loading/i).length).toBeGreaterThan(0);
  });

  it('shows error state when fetch fails', () => {
    vi.mocked(hooks.useRectorAssignmentDetail).mockReturnValue({ data: undefined, isLoading: false, isError: true } as any);
    render(<AssignmentDetailPage />);
    expect(screen.getByText(/failed to load/i)).toBeInTheDocument();
  });

  it('renders assignment title and status badge', () => {
    render(<AssignmentDetailPage />);
    expect(screen.getByRole('heading', { name: 'Test Assignment' })).toBeInTheDocument();
    expect(screen.getByTestId('status-badge')).toBeInTheDocument();
  });

  it('renders all six tab buttons', () => {
    render(<AssignmentDetailPage />);
    expect(screen.getByTestId('tab-overview')).toBeInTheDocument();
    expect(screen.getByTestId('tab-reports')).toBeInTheDocument();
    expect(screen.getByTestId('tab-evidence')).toBeInTheDocument();
    expect(screen.getByTestId('tab-comments')).toBeInTheDocument();
    expect(screen.getByTestId('tab-history')).toBeInTheDocument();
    expect(screen.getByTestId('tab-audit')).toBeInTheDocument();
  });

  it('shows accept button when status is ASSIGNED', () => {
    stubDetail(AssignmentStatus.ASSIGNED);
    render(<AssignmentDetailPage />);
    expect(screen.getByTestId('accept-btn')).toBeInTheDocument();
  });

  it('shows return button when status is REPORT_SUBMITTED', () => {
    stubDetail(AssignmentStatus.REPORT_SUBMITTED);
    render(<AssignmentDetailPage />);
    expect(screen.getByTestId('return-btn')).toBeInTheDocument();
    expect(screen.getByTestId('complete-btn')).toBeInTheDocument();
  });

  it('shows cancel button when status is IN_PROGRESS', () => {
    render(<AssignmentDetailPage />);
    expect(screen.getByTestId('cancel-btn')).toBeInTheDocument();
  });

  it('does not show accept button when status is IN_PROGRESS', () => {
    render(<AssignmentDetailPage />);
    expect(screen.queryByTestId('accept-btn')).not.toBeInTheDocument();
  });

  it('shows archive button when status is COMPLETED', () => {
    stubDetail(AssignmentStatus.COMPLETED);
    render(<AssignmentDetailPage />);
    expect(screen.getByTestId('archive-btn')).toBeInTheDocument();
  });

  it('switches to comments tab and renders comment form', async () => {
    const user = userEvent.setup();
    render(<AssignmentDetailPage />);
    await user.click(screen.getByTestId('tab-comments'));
    expect(screen.getByTestId('comment-input')).toBeInTheDocument();
  });

  it('switches to history tab', async () => {
    const user = userEvent.setup();
    render(<AssignmentDetailPage />);
    await user.click(screen.getByTestId('tab-history'));
    expect(screen.getByTestId('panel-history')).toBeInTheDocument();
  });
});
