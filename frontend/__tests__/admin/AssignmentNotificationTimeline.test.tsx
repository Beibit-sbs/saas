/**
 * AssignmentNotificationTimeline.test.tsx
 * A-031.5 — Notification timeline for individual assignment
 */

import React from 'react';
import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { AssignmentNotificationTimeline } from '@/modules/rector-assignments/components/AssignmentNotificationTimeline';
import type { RectorAssignmentOutboxEvent } from '@/modules/rector-assignments/types';
import { OutboxEventStatus, OutboxChannel } from '@/modules/rector-assignments/types';

const PENDING_EVENT: RectorAssignmentOutboxEvent = {
  id: 1,
  assignment_id: 42,
  event_type: 'ASSIGNMENT_APPROACHING_DEADLINE',
  status: OutboxEventStatus.PENDING,
  channel: OutboxChannel.IN_APP,
  recipient_user_id: 99,
  created_at: '2024-03-01T10:00:00Z',
};

const READY_EVENT: RectorAssignmentOutboxEvent = {
  ...PENDING_EVENT,
  id: 2,
  status: OutboxEventStatus.READY,
};

const CANCELLED_EVENT: RectorAssignmentOutboxEvent = {
  ...PENDING_EVENT,
  id: 3,
  status: OutboxEventStatus.CANCELLED,
};

vi.mock('@/modules/rector-assignments/hooks', () => ({
  useAssignmentOutboxEvents: vi.fn(() => ({
    data: [PENDING_EVENT, READY_EVENT, CANCELLED_EVENT],
    isLoading: false,
    isError: false,
  })),
  useMarkOutboxEventReady: vi.fn(() => ({ mutateAsync: vi.fn(), isPending: false })),
  useCancelOutboxEvent: vi.fn(() => ({ mutateAsync: vi.fn(), isPending: false })),
}));

describe('AssignmentNotificationTimeline', () => {
  it('renders outbox event rows', () => {
    render(<AssignmentNotificationTimeline assignmentId={42} canManage={false} />);
    expect(screen.getByTestId('notification-timeline')).toBeTruthy();
    expect(screen.getByTestId('outbox-event-1')).toBeTruthy();
    expect(screen.getByTestId('outbox-event-2')).toBeTruthy();
    expect(screen.getByTestId('outbox-event-3')).toBeTruthy();
  });

  it('shows required dispatch disabled notice', () => {
    render(<AssignmentNotificationTimeline assignmentId={42} canManage={false} />);
    expect(
      screen.getByText(/Live email\/SMS dispatch is not enabled/i),
    ).toBeTruthy();
  });

  it('does NOT show Send Now or Dispatch buttons', () => {
    render(<AssignmentNotificationTimeline assignmentId={42} canManage={true} />);
    expect(screen.queryByText(/Send Now/i)).toBeNull();
    expect(screen.queryByText(/^Dispatch$/i)).toBeNull();
  });

  it('shows Mark Ready and Cancel buttons for PENDING events when canManage=true', () => {
    render(<AssignmentNotificationTimeline assignmentId={42} canManage={true} />);
    expect(screen.getByTestId('mark-ready-1')).toBeTruthy();
    expect(screen.getByTestId('cancel-event-1')).toBeTruthy();
  });

  it('does NOT show action buttons for READY or CANCELLED events', () => {
    render(<AssignmentNotificationTimeline assignmentId={42} canManage={true} />);
    expect(screen.queryByTestId('mark-ready-2')).toBeNull();
    expect(screen.queryByTestId('mark-ready-3')).toBeNull();
  });

  it('hides action buttons when canManage=false', () => {
    render(<AssignmentNotificationTimeline assignmentId={42} canManage={false} />);
    expect(screen.queryByTestId('mark-ready-1')).toBeNull();
    expect(screen.queryByTestId('cancel-event-1')).toBeNull();
  });

  it('shows loading skeleton', () => {
    const hooks = await import('@/modules/rector-assignments/hooks');
    vi.mocked(hooks.useAssignmentOutboxEvents).mockReturnValueOnce({
      data: undefined,
      isLoading: true,
      isError: false,
    } as any);
    render(<AssignmentNotificationTimeline assignmentId={42} canManage={false} />);
    expect(screen.getByTestId('notification-timeline-loading')).toBeTruthy();
  });
});
