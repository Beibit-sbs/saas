import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

const pushMock = vi.fn();
const mutateMock = vi.fn();

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

describe('CreateCohortPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('blocks next step when end date is before start date', async () => {
    const user = userEvent.setup();
    render(<CreateCohortPage />);

    await user.selectOptions(screen.getByLabelText('Select Playbook'), '5');
    await user.type(screen.getByLabelText('Cohort Name'), 'Spring Cohort');
    await user.type(screen.getByLabelText('Start Date'), '2026-05-10');
    await user.type(screen.getByLabelText('End Date'), '2026-05-01');

    await user.click(screen.getByRole('button', { name: 'Next' }));

    expect(screen.getByText('End date must be on or after start date')).toBeInTheDocument();
    expect(screen.getByText('Step 1')).toBeInTheDocument();
  });

  it('validates treatment size cannot exceed total size', async () => {
    const user = userEvent.setup();
    render(<CreateCohortPage />);

    await user.selectOptions(screen.getByLabelText('Select Playbook'), '5');
    await user.type(screen.getByLabelText('Cohort Name'), 'Spring Cohort');
    await user.type(screen.getByLabelText('Start Date'), '2026-05-01');
    await user.type(screen.getByLabelText('End Date'), '2026-05-10');

    await user.click(screen.getByRole('button', { name: 'Next' }));

    await user.type(screen.getByLabelText('Total Cohort Size (minimum 20)'), '20');
    await user.type(screen.getByLabelText('Treatment Group Size'), '25');

    await user.click(screen.getByRole('button', { name: 'Next' }));

    expect(screen.getByText('Treatment size cannot exceed total cohort size')).toBeInTheDocument();
  });

  it('submits valid flow and redirects to detail page', async () => {
    const user = userEvent.setup();
    mutateMock.mockImplementation((_payload, opts) => {
      opts?.onSuccess?.({ id: 77 });
    });

    render(<CreateCohortPage />);

    await user.selectOptions(screen.getByLabelText('Select Playbook'), '5');
    await user.type(screen.getByLabelText('Cohort Name'), '  Spring Cohort A  ');
    await user.type(screen.getByLabelText('Start Date'), '2026-05-01');
    await user.type(screen.getByLabelText('End Date'), '2026-05-10');
    await user.click(screen.getByRole('button', { name: 'Next' }));

    await user.type(screen.getByLabelText('Total Cohort Size (minimum 20)'), '40');
    await user.type(screen.getByLabelText('Treatment Group Size'), '18');
    await user.click(screen.getByRole('button', { name: 'Next' }));

    await user.click(screen.getByRole('button', { name: 'Create Cohort' }));

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
});
