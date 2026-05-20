'use client';

import React from 'react';
import { OutboxEventStatus } from '../types';

interface OutboxStatusBadgeProps {
  status: OutboxEventStatus;
  /** Show tooltip with "Intent only" for PENDING status */
  showTooltip?: boolean;
}

const BADGE_STYLES: Record<OutboxEventStatus, string> = {
  [OutboxEventStatus.PENDING]: 'bg-gray-100 text-gray-700 border border-gray-300',
  [OutboxEventStatus.READY]: 'bg-blue-100 text-blue-700 border border-blue-300',
  [OutboxEventStatus.CANCELLED]: 'bg-red-100 text-red-700 border border-red-300',
};

const BADGE_LABELS: Record<OutboxEventStatus, string> = {
  [OutboxEventStatus.PENDING]: 'Intent queued',
  [OutboxEventStatus.READY]: 'Ready',
  [OutboxEventStatus.CANCELLED]: 'Cancelled',
};

export function OutboxStatusBadge({ status, showTooltip = false }: OutboxStatusBadgeProps) {
  const style = BADGE_STYLES[status] ?? 'bg-gray-100 text-gray-700';
  const label = BADGE_LABELS[status] ?? status;

  return (
    <span
      className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${style}`}
      title={showTooltip && status === OutboxEventStatus.PENDING ? 'Intent only' : undefined}
      data-testid={`outbox-status-badge-${status.toLowerCase()}`}
    >
      {label}
    </span>
  );
}
