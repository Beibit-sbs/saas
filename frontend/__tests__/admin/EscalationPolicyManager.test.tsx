/**
 * EscalationPolicyManager.test.tsx
 * A-031.5 — Escalation policy CRUD: require_manual_confirmation defaults true, archive not delete
 */

import React from 'react';
import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { EscalationPolicyManager } from '@/modules/rector-assignments/components/EscalationPolicyManager';
import type { RectorAssignmentEscalationPolicy } from '@/modules/rector-assignments/types';
import { AssignmentPriority, EscalateToRole } from '@/modules/rector-assignments/types';

const POLICIES: RectorAssignmentEscalationPolicy[] = [
  {
    id: 1,
    assignment_priority: AssignmentPriority.HIGH,
    escalation_level: 2,
    escalate_to_role: EscalateToRole.PRORECTOR,
    escalate_after_hours: 48,
    require_manual_confirmation: true,
    archived_at: null,
    created_at: '2024-01-01T00:00:00Z',
  },
];

const mockCreate = vi.fn(() => Promise.resolve());
const mockUpdate = vi.fn(() => Promise.resolve());
const mockArchive = vi.fn(() => Promise.resolve());

vi.mock('@/modules/rector-assignments/hooks', () => ({
  useEscalationPolicies: vi.fn(() => ({ data: POLICIES, isLoading: false, isError: false })),
  useCreateEscalationPolicy: vi.fn(() => ({ mutateAsync: mockCreate, isPending: false })),
  useUpdateEscalationPolicy: vi.fn(() => ({ mutateAsync: mockUpdate, isPending: false })),
  useArchiveEscalationPolicy: vi.fn(() => ({ mutateAsync: mockArchive, isPending: false })),
}));

vi.mock('@/shared/ui/page-states', () => ({
  LoadingState: ({ message }: any) => <div>{message}</div>,
  ErrorState: ({ message }: any) => <div>{message}</div>,
}));

describe('EscalationPolicyManager', () => {
  it('renders policy table with manual confirmation badge', () => {
    render(<EscalationPolicyManager />);
    expect(screen.getByTestId('escalation-policy-manager')).toBeTruthy();
    expect(screen.getByTestId('ep-manual-badge-1')).toBeTruthy();
    expect(screen.getByTestId('ep-manual-badge-1').textContent).toMatch(/Manual confirmation required/i);
  });

  it('shows manual notice in header', () => {
    render(<EscalationPolicyManager />);
    expect(screen.getByTestId('escalation-manual-notice').textContent).toMatch(
      /Manual confirmation required/i,
    );
  });

  it('require_manual_confirmation checkbox defaults to checked in create form', () => {
    render(<EscalationPolicyManager />);
    fireEvent.click(screen.getByTestId('create-escalation-policy-btn'));
    const checkbox = screen.getByTestId('ep-manual-confirm-checkbox') as HTMLInputElement;
    expect(checkbox.checked).toBe(true);
  });

  it('shows "Require manual confirmation before escalation" label in form', () => {
    render(<EscalationPolicyManager />);
    fireEvent.click(screen.getByTestId('create-escalation-policy-btn'));
    expect(
      screen.getByText(/Require manual confirmation before escalation/i),
    ).toBeTruthy();
  });

  it('shows "Escalation will not be sent automatically" in form', () => {
    render(<EscalationPolicyManager />);
    fireEvent.click(screen.getByTestId('create-escalation-policy-btn'));
    expect(
      screen.getByText(/Escalation will not be sent automatically/i),
    ).toBeTruthy();
  });

  it('does NOT show a Trigger Now button', () => {
    render(<EscalationPolicyManager />);
    expect(screen.queryByText(/Trigger Now/i)).toBeNull();
  });

  it('does NOT show a Delete button — only Archive', () => {
    render(<EscalationPolicyManager />);
    expect(screen.queryByText(/Delete/i)).toBeNull();
    expect(screen.getByTestId('ep-archive-1')).toBeTruthy();
  });

  it('shows archive confirmation dialog', () => {
    render(<EscalationPolicyManager />);
    fireEvent.click(screen.getByTestId('ep-archive-1'));
    expect(screen.getByTestId('ep-archive-confirm-modal')).toBeTruthy();
  });

  it('calls archive mutation with policy ID on confirm', async () => {
    render(<EscalationPolicyManager />);
    fireEvent.click(screen.getByTestId('ep-archive-1'));
    fireEvent.click(screen.getByTestId('ep-archive-confirm-btn'));
    await waitFor(() => expect(mockArchive).toHaveBeenCalledWith(1));
  });

  it('validates escalation level 1-4', async () => {
    render(<EscalationPolicyManager />);
    fireEvent.click(screen.getByTestId('create-escalation-policy-btn'));
    fireEvent.change(screen.getByTestId('ep-level-input'), { target: { value: '5' } });
    fireEvent.submit(screen.getByTestId('ep-submit-btn').closest('form')!);
    await waitFor(() =>
      expect(screen.getByText(/Escalation level must be between 1 and 4/i)).toBeTruthy(),
    );
  });

  it('shows edit form with "Update Escalation Policy" label', () => {
    render(<EscalationPolicyManager />);
    fireEvent.click(screen.getByTestId('ep-edit-1'));
    expect(screen.getByTestId('ep-submit-btn').textContent).toContain('Update Escalation Policy');
  });
});
