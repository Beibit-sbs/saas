/**
 * OutboxRegistry.test.tsx
 * A-031.5 — Global outbox registry with filters and guards
 */

import React from 'react';
import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { OutboxRegistry } from '@/modules/rector-assignments/components/OutboxRegistry';
import type { RectorAssignmentOutboxEvent } from '@/modules/rector-assignments/types';
import { OutboxEventStatus, OutboxChannel } from '@/modules/rector-assignments/types';

const EVENTS: RectorAssignmentOutboxEvent[] = [
  {
    id: 10,
    tenant_id: 1,
    assignment_id: 1,
    event_type: 'ASSIGNMENT_OVERDUE',
    status: OutboxEventStatus.PENDING,
    channel: OutboxChannel.EMAIL,
    recipient_user_id: 11,
    retry_count: 0,
    created_at: '2024-03-01T08:00:00Z',
    updated_at: '2024-03-01T08:00:00Z',
  },
  {
    id: 11,
    tenant_id: 1,
    assignment_id: 2,
    event_type: 'ASSIGNMENT_APPROACHING_DEADLINE',
    status: OutboxEventStatus.READY,
    channel: OutboxChannel.SMS,
    recipient_user_id: 22,
    retry_count: 0,
    created_at: '2024-03-02T09:00:00Z',
    updated_at: '2024-03-02T09:00:00Z',
  },
];

vi.mock('@/modules/rector-assignments/hooks', () => ({
  useOutboxEvents: vi.fn(() => ({
    data: { items: EVENTS, total: 2, page: 1, page_size: 50 },
    isLoading: false,
    isError: false,
  })),
  useMarkOutboxEventReady: vi.fn(() => ({ mutateAsync: vi.fn(), isPending: false })),
  useCancelOutboxEvent: vi.fn(() => ({ mutateAsync: vi.fn(), isPending: false })),
}));

vi.mock('@/shared/auth/permission-gate', () => ({
  RequirePermission: ({ children }: any) => <>{children}</>,
  PermissionGate: ({ children }: any) => <>{children}</>,
}));

vi.mock('@/shared/config/permissions', () => ({
  PERMISSIONS: {
    RECTOR_ASSIGNMENTS_OUTBOX_READ: 'admin.rector_assignments.outbox.read',
    RECTOR_ASSIGNMENTS_OUTBOX_MANAGE: 'admin.rector_assignments.outbox.manage',
  },
}));

describe('OutboxRegistry', () => {
  it('renders event rows', () => {
    render(<OutboxRegistry />);
    expect(screen.getByTestId('outbox-registry')).toBeTruthy();
    expect(screen.getByTestId('outbox-global-row-10')).toBeTruthy();
    expect(screen.getByTestId('outbox-global-row-11')).toBeTruthy();
  });

  it('shows "Dispatch disabled" label', () => {
    render(<OutboxRegistry />);
    expect(screen.getByText(/Dispatch disabled/i)).toBeTruthy();
  });

  it('shows required "Live email/SMS dispatch is not enabled" text', () => {
    render(<OutboxRegistry />);
    expect(screen.getByText(/Live email\/SMS dispatch is not enabled/i)).toBeTruthy();
  });

  it('shows provider out of scope notice', () => {
    render(<OutboxRegistry />);
    expect(screen.getByTestId('outbox-dispatch-disabled-notice').textContent).toMatch(/Provider delivery is out of scope/i);
  });

  it('does NOT show "Send Now" button', () => {
    render(<OutboxRegistry />);
    expect(screen.queryByText(/Send Now/i)).toBeNull();
  });

  it('shows status legend', () => {
    render(<OutboxRegistry />);
    expect(screen.getByText(/PENDING = queued/i)).toBeTruthy();
  });

  it('shows Mark Ready button for PENDING events', () => {
    render(<OutboxRegistry />);
    expect(screen.getByTestId('global-mark-ready-10')).toBeTruthy();
  });

  it('does NOT show Mark Ready for READY events', () => {
    render(<OutboxRegistry />);
    expect(screen.queryByTestId('mark-ready-11')).toBeNull();
  });
});
