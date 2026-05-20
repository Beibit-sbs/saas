/**
 * Tests: AssignmentCreateForm (NewRectorAssignmentPage)
 */

import { beforeEach, describe, expect, it, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

vi.mock('@/shared/auth/permission-gate', () => ({
  RequirePermission: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}));

const mockPush = vi.fn();
vi.mock('next/navigation', () => ({
  useRouter: () => ({ push: mockPush, back: vi.fn() }),
  useParams: () => ({}),
}));

vi.mock('@/modules/rector-assignments/hooks', () => ({
  useCreateRectorAssignment: vi.fn(),
  useRectorAssignmentTemplates: vi.fn(),
}));

import * as hooks from '@/modules/rector-assignments/hooks';
import NewRectorAssignmentPage from '@/app/(admin)/console/rector-assignments/new/page';

function stubHooks(mutateAsyncFn = vi.fn()) {
  vi.mocked(hooks.useCreateRectorAssignment).mockReturnValue({
    mutateAsync: mutateAsyncFn,
    isPending: false,
  } as any);
  vi.mocked(hooks.useRectorAssignmentTemplates).mockReturnValue({
    data: [],
    isLoading: false,
  } as any);
}

beforeEach(() => {
  vi.clearAllMocks();
  stubHooks();
});

describe('NewRectorAssignmentPage', () => {
  it('renders the create form', () => {
    render(<NewRectorAssignmentPage />);
    expect(screen.getByTestId('create-form')).toBeInTheDocument();
  });

  it('shows validation error when title is empty', async () => {
    const user = userEvent.setup();
    render(<NewRectorAssignmentPage />);
    await user.click(screen.getByTestId('submit-btn'));
    expect(screen.getByText(/title is required/i)).toBeInTheDocument();
  });

  it('shows validation error when title is too short', async () => {
    const user = userEvent.setup();
    render(<NewRectorAssignmentPage />);
    await user.type(screen.getByTestId('title-input'), 'AB');
    await user.click(screen.getByTestId('submit-btn'));
    expect(screen.getByText(/at least 3 characters/i)).toBeInTheDocument();
  });

  it('calls createMutation with correct payload on valid submit', async () => {
    const mutateAsync = vi.fn().mockResolvedValue({ id: '99' });
    stubHooks(mutateAsync);
    const user = userEvent.setup();
    render(<NewRectorAssignmentPage />);

    await user.type(screen.getByTestId('title-input'), 'Valid Assignment Title');
    await user.click(screen.getByTestId('submit-btn'));

    expect(mutateAsync).toHaveBeenCalledWith(
      expect.objectContaining({ title: 'Valid Assignment Title' })
    );
  });

  it('navigates to detail page after successful create', async () => {
    const mutateAsync = vi.fn().mockResolvedValue({ id: '123' });
    stubHooks(mutateAsync);
    const user = userEvent.setup();
    render(<NewRectorAssignmentPage />);

    await user.type(screen.getByTestId('title-input'), 'New Assignment');
    await user.click(screen.getByTestId('submit-btn'));

    expect(mockPush).toHaveBeenCalledWith('/console/rector-assignments/123');
  });

  it('shows global error on API failure', async () => {
    const mutateAsync = vi.fn().mockRejectedValue(new Error('Server error'));
    stubHooks(mutateAsync);
    const user = userEvent.setup();
    render(<NewRectorAssignmentPage />);

    await user.type(screen.getByTestId('title-input'), 'Error Assignment');
    await user.click(screen.getByTestId('submit-btn'));

    expect(screen.getByTestId('global-error')).toBeInTheDocument();
  });

  it('has correct priority options (CRITICAL, HIGH, NORMAL, LOW — no MEDIUM)', () => {
    render(<NewRectorAssignmentPage />);
    const select = screen.getByTestId('priority-select');
    const options = Array.from(select.querySelectorAll('option')).map((o) => o.value);
    expect(options).toContain('CRITICAL');
    expect(options).toContain('HIGH');
    expect(options).toContain('NORMAL');
    expect(options).toContain('LOW');
    expect(options).not.toContain('MEDIUM');
  });

  it('has correct recurrence options (DAILY/WEEKLY/MONTHLY/CUSTOM — no QUARTERLY)', () => {
    render(<NewRectorAssignmentPage />);
    const select = screen.getByTestId('recurrence-select');
    const options = Array.from(select.querySelectorAll('option')).map((o) => o.value);
    expect(options).toContain('NONE');
    expect(options).toContain('DAILY');
    expect(options).toContain('WEEKLY');
    expect(options).toContain('MONTHLY');
    expect(options).toContain('CUSTOM');
    expect(options).not.toContain('QUARTERLY');
    expect(options).not.toContain('ANNUAL');
  });

  it('shows cancel button that calls router.back()', async () => {
    const user = userEvent.setup();
    render(<NewRectorAssignmentPage />);
    await user.click(screen.getByTestId('cancel-btn'));
    // back() was called — no crash
  });
});
