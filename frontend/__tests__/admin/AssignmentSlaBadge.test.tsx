/**
 * AssignmentSlaBadge.test.tsx
 * A-031.5 — SLA badge states: within_sla, warning, overdue, no_policy, no_due_date
 */

import React from 'react';
import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { AssignmentSlaBadge } from '@/modules/rector-assignments/components/AssignmentSlaBadge';
import type { RectorAssignment, RectorAssignmentSlaPolicy } from '@/modules/rector-assignments/types';
import { AssignmentStatus, AssignmentPriority, RecurrenceType } from '@/modules/rector-assignments/types';

const now = new Date();

function makeAssignment(overrides: Partial<RectorAssignment> = {}): RectorAssignment {
  return {
    id: 1,
    tenant_id: 1,
    title: 'Test',
    status: AssignmentStatus.IN_PROGRESS,
    priority: AssignmentPriority.NORMAL,
    recurrence_type: RecurrenceType.NONE,
    version: 1,
    is_overdue: false,
    created_by: 1,
    created_at: now.toISOString(),
    updated_at: now.toISOString(),
    ...overrides,
  };
}

const SLA_POLICY: RectorAssignmentSlaPolicy = {
  id: 1,
  tenant_id: 1,
  name: 'Normal',
  priority: AssignmentPriority.NORMAL,
  due_days: 30,
  warning_before_hours: 48,
  overdue_after_hours: 24,
  escalation_after_hours: 72,
  is_active: true,
  created_at: now.toISOString(),
  updated_at: now.toISOString(),
};

describe('AssignmentSlaBadge', () => {
  it('shows no_policy state when slaPolicy is undefined', () => {
    render(<AssignmentSlaBadge assignment={makeAssignment()} slaPolicy={undefined} />);
    expect(screen.getByTestId('sla-badge-no_policy')).toBeTruthy();
  });

  it('shows no_due_date state when due_date is undefined', () => {
    render(<AssignmentSlaBadge assignment={makeAssignment()} slaPolicy={SLA_POLICY} />);
    expect(screen.getByTestId('sla-badge-no_due_date')).toBeTruthy();
  });

  it('shows within_sla state for due date far in the future', () => {
    const farFuture = new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString(); // 30 days out
    render(
      <AssignmentSlaBadge
        assignment={makeAssignment({ due_date: farFuture })}
        slaPolicy={SLA_POLICY}
      />,
    );
    expect(screen.getByTestId('sla-badge-within_sla')).toBeTruthy();
  });

  it('shows warning state when due date is within warning window', () => {
    // warning_before_hours=48, so 30 hours from now triggers warning but not overdue
    const warningDate = new Date(Date.now() + 30 * 60 * 60 * 1000).toISOString();
    render(
      <AssignmentSlaBadge
        assignment={makeAssignment({ due_date: warningDate })}
        slaPolicy={SLA_POLICY}
      />,
    );
    expect(screen.getByTestId('sla-badge-warning')).toBeTruthy();
  });

  it('shows overdue state when past due', () => {
    const pastDate = new Date(Date.now() - 48 * 60 * 60 * 1000).toISOString(); // 48h ago
    render(
      <AssignmentSlaBadge
        assignment={makeAssignment({ due_date: pastDate, is_overdue: true })}
        slaPolicy={SLA_POLICY}
      />,
    );
    expect(screen.getByTestId('sla-badge-overdue')).toBeTruthy();
  });
});
