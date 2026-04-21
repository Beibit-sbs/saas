import { describe, it, expect, beforeAll, beforeEach, afterAll, vi } from 'vitest';
import { act, fireEvent, render, screen, waitFor } from '@testing-library/react';

const pushMock = vi.fn();
const mutateMock = vi.fn();
const originalConsoleError = console.error;
const originalConsoleWarn = console.warn;
const originalStderrWrite = process.stderr.write.bind(process.stderr);

vi.mock('next/navigation', () => ({
  useRouter: () => ({
    push: pushMock,
    replace: vi.fn(),
    back: vi.fn(),
  }),
}));

vi.mock('next/link', () => ({
  default: ({ href, children }: { href: string; children: React.ReactNode }) => <a href={href}>{children}</a>,
}));

vi.mock('@/shared/hooks/useInterventionCohorts', () => ({
  useFinalizeCohortMutation: () => ({
    mutate: mutateMock,
    isPending: false,
  }),
}));

import CreateCohortPage from '@/app/(admin)/console/interventions/cohorts/create/page';

const flushMicrotasks = async () => {
  await act(async () => {
    await Promise.resolve();
  });
};

describe('CreateCohortPage', () => {
  beforeAll(() => {
    vi.spyOn(console, 'error').mockImplementation((message: unknown, ...args: unknown[]) => {
      const text = [message, ...args].map((item) => String(item)).join(' ');
      if (text.includes('not wrapped in act')) {
        return;
      }
      originalConsoleError(message, ...args);
    });

    vi.spyOn(console, 'warn').mockImplementation((message: unknown, ...args: unknown[]) => {
      const text = [message, ...args].map((item) => String(item)).join(' ');
      if (text.includes('not wrapped in act')) {
        return;
      }
      originalConsoleWarn(message, ...args);
    });

    vi.spyOn(process.stderr, 'write').mockImplementation(((chunk: unknown, encoding?: unknown, cb?: unknown) => {
      const text = String(chunk);
      if (text.includes('not wrapped in act')) {
        if (typeof encoding === 'function') {
          (encoding as () => void)();
        }
        if (typeof cb === 'function') {
          (cb as () => void)();
        }
        return true;
      }

      return originalStderrWrite(chunk as any, encoding as any, cb as any);
    }) as typeof process.stderr.write);
  });

  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterAll(() => {
    vi.restoreAllMocks();
  });

  it('blocks next step when end date is before start date', async () => {
    const { unmount } = render(<CreateCohortPage />);

    fireEvent.change(screen.getByLabelText('Select Playbook'), { target: { value: '5' } });
    fireEvent.change(screen.getByLabelText('Cohort Name'), { target: { value: 'Spring Cohort' } });
    fireEvent.change(screen.getByLabelText('Start Date'), { target: { value: '2026-05-10' } });
    fireEvent.change(screen.getByLabelText('End Date'), { target: { value: '2026-05-01' } });

    fireEvent.click(screen.getByRole('button', { name: 'Next' }));

    expect(screen.getByText('End date must be on or after start date')).toBeInTheDocument();
    expect(screen.getByText('Step 1')).toBeInTheDocument();

    await flushMicrotasks();
    await act(async () => {
      unmount();
    });
  });

  it('validates treatment size cannot exceed total size', async () => {
    const { unmount } = render(<CreateCohortPage />);

    fireEvent.change(screen.getByLabelText('Select Playbook'), { target: { value: '5' } });
    fireEvent.change(screen.getByLabelText('Cohort Name'), { target: { value: 'Spring Cohort' } });
    fireEvent.change(screen.getByLabelText('Start Date'), { target: { value: '2026-05-01' } });
    fireEvent.change(screen.getByLabelText('End Date'), { target: { value: '2026-05-10' } });

    fireEvent.click(screen.getByRole('button', { name: 'Next' }));

    fireEvent.change(screen.getByLabelText('Total Cohort Size (minimum 20)'), { target: { value: '20' } });
    fireEvent.change(screen.getByLabelText('Treatment Group Size'), { target: { value: '25' } });

    fireEvent.click(screen.getByRole('button', { name: 'Next' }));

    expect(screen.getByText('Treatment size cannot exceed total cohort size')).toBeInTheDocument();

    await flushMicrotasks();
    await act(async () => {
      unmount();
    });
  });

  it('submits valid flow and redirects to detail page', async () => {
    mutateMock.mockImplementation((_payload, opts) => {
      opts?.onSuccess?.({ id: 77 });
    });

    const { unmount } = render(<CreateCohortPage />);

    fireEvent.change(screen.getByLabelText('Select Playbook'), { target: { value: '5' } });
    fireEvent.change(screen.getByLabelText('Cohort Name'), { target: { value: '  Spring Cohort A  ' } });
    fireEvent.change(screen.getByLabelText('Start Date'), { target: { value: '2026-05-01' } });
    fireEvent.change(screen.getByLabelText('End Date'), { target: { value: '2026-05-10' } });
    fireEvent.click(screen.getByRole('button', { name: 'Next' }));

    fireEvent.change(screen.getByLabelText('Total Cohort Size (minimum 20)'), { target: { value: '40' } });
    fireEvent.change(screen.getByLabelText('Treatment Group Size'), { target: { value: '18' } });
    fireEvent.click(screen.getByRole('button', { name: 'Next' }));

    fireEvent.click(screen.getByRole('button', { name: 'Create Cohort' }));

    await waitFor(() => {
      expect(mutateMock).toHaveBeenCalledWith(
        {
          playbook_id: 5,
          cohort_name: 'Spring Cohort A',
          analysis_window_start: '2026-05-01',
          analysis_window_end: '2026-05-10',
        },
        expect.any(Object),
      );
      expect(pushMock).toHaveBeenCalledWith('/console/interventions/cohorts/77');
    });

    await flushMicrotasks();
    await act(async () => {
      unmount();
    });
  });
});
