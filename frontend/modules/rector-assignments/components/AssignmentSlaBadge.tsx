'use client';

import React from 'react';
import type { RectorAssignment, RectorAssignmentSlaPolicy } from '../types';

interface AssignmentSlaBadgeProps {
  assignment: RectorAssignment;
  slaPolicy?: RectorAssignmentSlaPolicy;
}

type SlaState = 'no_policy' | 'within_sla' | 'warning' | 'overdue' | 'no_due_date';

function computeSlaState(
  assignment: RectorAssignment,
  slaPolicy?: RectorAssignmentSlaPolicy,
): SlaState {
  if (!slaPolicy) return 'no_policy';
  if (!assignment.due_date) return 'no_due_date';

  const now = Date.now();
  const dueMs = new Date(assignment.due_date).getTime();
  const warningMs = slaPolicy.warning_before_hours * 60 * 60 * 1000;

  if (now > dueMs + slaPolicy.overdue_after_hours * 60 * 60 * 1000) return 'overdue';
  if (now > dueMs - warningMs) return 'warning';
  return 'within_sla';
}

const STATE_STYLES: Record<SlaState, string> = {
  no_policy: 'bg-gray-100 text-gray-600 border border-gray-200',
  within_sla: 'bg-green-100 text-green-700 border border-green-200',
  warning: 'bg-yellow-100 text-yellow-700 border border-yellow-200',
  overdue: 'bg-red-100 text-red-700 border border-red-200',
  no_due_date: 'bg-gray-100 text-gray-500 border border-gray-200',
};

const STATE_LABELS: Record<SlaState, string> = {
  no_policy: 'No SLA',
  within_sla: 'Within SLA',
  warning: 'Due Soon',
  overdue: 'Overdue (SLA)',
  no_due_date: 'No due date',
};

export function AssignmentSlaBadge({ assignment, slaPolicy }: AssignmentSlaBadgeProps) {
  const state = computeSlaState(assignment, slaPolicy);

  return (
    <span
      className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${STATE_STYLES[state]}`}
      data-testid={`sla-badge-${state}`}
      title={slaPolicy ? `SLA policy: ${slaPolicy.name}` : 'No SLA policy matched'}
    >
      {STATE_LABELS[state]}
    </span>
  );
}
