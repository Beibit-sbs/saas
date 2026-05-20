/**
 * SlaPolicyManager.test.tsx
 * A-031.5 — SLA policy CRUD, no delete, validation
 */

import React from 'react';
import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { SlaPolicyManager } from '@/modules/rector-assignments/components/SlaPolicyManager';
import type { RectorAssignmentSlaPolicy } from '@/modules/rector-assignments/types';
import { AssignmentPriority } from '@/modules/rector-assignments/types';

const POLICIES: RectorAssignmentSlaPolicy[] = [
  {
    id: 1,
    tenant_id: 1,
    name: 'Normal 30d',
    priority: AssignmentPriority.NORMAL,
    due_days: 30,
    warning_before_hours: 48,
    overdue_after_hours: 24,
    escalation_after_hours: 72,
    is_active: true,
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
  },
];

const mockCreate = vi.fn(() => Promise.resolve());
const mockUpdate = vi.fn(() => Promise.resolve());
const mockArchive = vi.fn(() => Promise.resolve());

vi.mock('@/modules/rector-assignments/hooks', () => ({
  useSlaPolicies: vi.fn(() => ({ data: POLICIES, isLoading: false, isError: false })),
  useCreateSlaPolicy: vi.fn(() => ({ mutateAsync: mockCreate, isPending: false })),
  useUpdateSlaPolicy: vi.fn(() => ({ mutateAsync: mockUpdate, isPending: false })),
  useArchiveSlaPolicy: vi.fn(() => ({ mutateAsync: mockArchive, isPending: false })),
}));

vi.mock('@/shared/ui/page-states', () => ({
  LoadingState: ({ message }: any) => <div>{message}</div>,
  ErrorState: ({ message }: any) => <div>{message}</div>,
}));

describe('SlaPolicyManager', () => {
  it('renders policy table', () => {
    render(<SlaPolicyManager />);
    expect(screen.getByTestId('sla-policy-manager')).toBeTruthy();
    expect(screen.getByTestId('sla-row-1')).toBeTruthy();
    expect(screen.getByText('Normal 30d')).toBeTruthy();
  });

  it('opens create form on button click', async () => {
    render(<SlaPolicyManager />);
    fireEvent.click(screen.getByTestId('create-sla-policy-btn'));
    expect(screen.getByTestId('sla-policy-form-modal')).toBeTruthy();
    expect(screen.getByTestId('sla-submit-btn').textContent).toContain('Create SLA Policy');
  });

  it('does NOT show delete button — only archive', () => {
    render(<SlaPolicyManager />);
    expect(screen.queryByText(/Delete/i)).toBeNull();
    expect(screen.getByTestId('sla-archive-1')).toBeTruthy();
  });

  it('shows archive confirmation dialog', async () => {
    render(<SlaPolicyManager />);
    fireEvent.click(screen.getByTestId('sla-archive-1'));
    expect(screen.getByTestId('sla-archive-confirm-modal')).toBeTruthy();
  });

  it('calls archive mutate on confirmation', async () => {
    render(<SlaPolicyManager />);
    fireEvent.click(screen.getByTestId('sla-archive-1'));
    fireEvent.click(screen.getByTestId('sla-archive-confirm-btn'));
    await waitFor(() => expect(mockArchive).toHaveBeenCalledWith(1));
  });

  it('validates escalation_after_hours >= overdue_after_hours', async () => {
    render(<SlaPolicyManager />);
    fireEvent.click(screen.getByTestId('create-sla-policy-btn'));

    // Set overdue_after_hours to 100, escalation to 50 (invalid)
    fireEvent.change(screen.getByTestId('sla-overdue-hours-input'), { target: { value: '100' } });
    fireEvent.change(screen.getByTestId('sla-escalation-hours-input'), { target: { value: '50' } });

    fireEvent.submit(screen.getByTestId('sla-submit-btn').closest('form')!);
    await waitFor(() =>
      expect(screen.getByText(/Escalation hours must be ≥ overdue hours/i)).toBeTruthy(),
    );
    expect(mockCreate).not.toHaveBeenCalled();
  });

  it('validates name is required', async () => {
    render(<SlaPolicyManager />);
    fireEvent.click(screen.getByTestId('create-sla-policy-btn'));
    fireEvent.change(screen.getByTestId('sla-name-input'), { target: { value: '' } });
    fireEvent.submit(screen.getByTestId('sla-submit-btn').closest('form')!);
    await waitFor(() => expect(screen.getByText(/Name is required/i)).toBeTruthy());
  });

  it('shows edit form with "Update SLA Policy" label', async () => {
    render(<SlaPolicyManager />);
    fireEvent.click(screen.getByTestId('sla-edit-1'));
    expect(screen.getByTestId('sla-submit-btn').textContent).toContain('Update SLA Policy');
  });
});
