/**
 * EscalationQueuePanel.test.tsx
 * A-031.5 — Manual confirmation badge visible; no autonomous trigger button
 */

import React from 'react';
import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { EscalationQueuePanel } from '@/modules/rector-assignments/components/EscalationQueuePanel';
import { AssignmentStatus, AssignmentPriority } from '@/modules/rector-assignments/types';

const now = new Date().toISOString();

const ESCALATED_ASSIGNMENTS = [
  {
    id: 5,
    title: 'Escalated Report Q1',
    status: AssignmentStatus.ESCALATED,
    priority: AssignmentPriority.HIGH,
    due_date: '2024-03-15T00:00:00Z',
    is_overdue: false,
    created_at: now,
    updated_at: now,
    assignees: [],
    recurrence_type: 'NONE',
  },
  {
    id: 6,
    title: 'Escalated Compliance',
    status: AssignmentStatus.ESCALATED,
    priority: AssignmentPriority.CRITICAL,
    due_date: null,
    is_overdue: true,
    created_at: now,
    updated_at: now,
    assignees: [],
    recurrence_type: 'NONE',
  },
];

vi.mock('@/modules/rector-assignments/hooks', () => ({
  useRectorAssignmentList: vi.fn(() => ({
    data: ESCALATED_ASSIGNMENTS,
    isLoading: false,
    isError: false,
  })),
}));

vi.mock('next/link', () => ({
  default: ({ href, children, ...props }: any) => <a href={href} {...props}>{children}</a>,
}));

vi.mock('@/shared/ui/page-states', () => ({
  LoadingState: ({ message }: any) => <div>{message}</div>,
  ErrorState: ({ message }: any) => <div>{message}</div>,
}));

describe('EscalationQueuePanel', () => {
  it('renders escalated rows', () => {
    render(<EscalationQueuePanel />);
    expect(screen.getByTestId('escalation-queue-panel')).toBeTruthy();
    expect(screen.getByTestId('escalation-queue-row-5')).toBeTruthy();
    expect(screen.getByTestId('escalation-queue-row-6')).toBeTruthy();
  });

  it('shows required header notice about manual-confirmation-only', () => {
    render(<EscalationQueuePanel />);
    expect(
      screen.getByTestId('escalation-manual-confirmation-notice').textContent,
    ).toMatch(/Escalation is manual-confirmation only/i);
    expect(
      screen.getByTestId('escalation-manual-confirmation-notice').textContent,
    ).toMatch(/No autonomous dispatch/i);
  });

  it('shows "Manual confirmation required" badge on each row', () => {
    render(<EscalationQueuePanel />);
    expect(screen.getByTestId('escalation-manual-badge-5').textContent).toMatch(
      /Manual confirmation required/i,
    );
    expect(screen.getByTestId('escalation-manual-badge-6').textContent).toMatch(
      /Manual confirmation required/i,
    );
  });

  it('does NOT show "Send Escalation" button', () => {
    render(<EscalationQueuePanel />);
    expect(screen.queryByText(/Send Escalation/i)).toBeNull();
  });

  it('does NOT show "Trigger Automatically" button', () => {
    render(<EscalationQueuePanel />);
    expect(screen.queryByText(/Trigger Automatically/i)).toBeNull();
  });

  it('shows empty state when no escalations', () => {
    const hooks = await import('@/modules/rector-assignments/hooks');
    vi.mocked(hooks.useRectorAssignmentList).mockReturnValueOnce({
      data: [],
      isLoading: false,
      isError: false,
    } as any);
    render(<EscalationQueuePanel />);
    expect(screen.getByTestId('escalation-queue-empty').textContent).toMatch(
      /No escalations pending manual confirmation/i,
    );
  });
});
