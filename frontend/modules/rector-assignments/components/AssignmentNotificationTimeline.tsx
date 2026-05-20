'use client';

import React from 'react';
import { useAssignmentOutboxEvents, useMarkOutboxEventReady, useCancelOutboxEvent } from '../hooks';
import { OutboxEventStatus } from '../types';
import { OutboxStatusBadge } from './OutboxStatusBadge';

interface AssignmentNotificationTimelineProps {
  assignmentId: string | number;
  canManage: boolean;
}

function formatDate(iso: string): string {
  try { return new Date(iso).toLocaleString(); } catch { return iso; }
}

export function AssignmentNotificationTimeline({
  assignmentId,
  canManage,
}: AssignmentNotificationTimelineProps) {
  const { data: events, isLoading, isError } = useAssignmentOutboxEvents(assignmentId);
  const markReady = useMarkOutboxEventReady(assignmentId);
  const cancelEvent = useCancelOutboxEvent(assignmentId);

  return (
    <div data-testid="notification-timeline">
      {/* Required anti-fake notice */}
      <div
        className="mb-3 rounded border border-amber-200 bg-amber-50 px-4 py-2 text-sm text-amber-800"
        data-testid="dispatch-disabled-notice"
      >
        <strong>Live email/SMS dispatch is not enabled.</strong> Intent only.
      </div>

      {isLoading && (
        <div className="space-y-2">
          {[0, 1, 2].map((i) => (
            <div key={i} className="h-14 rounded bg-gray-100 animate-pulse" />
          ))}
        </div>
      )}

      {isError && (
        <p className="text-sm text-red-600" data-testid="outbox-error">
          Failed to load notification intents.
        </p>
      )}

      {!isLoading && !isError && (!events || events.length === 0) && (
        <p className="text-sm text-gray-500" data-testid="outbox-empty">
          No notification intents for this assignment.
        </p>
      )}

      {!isLoading && !isError && events && events.length > 0 && (
        <div className="overflow-hidden rounded-lg border border-gray-200 bg-white">
          <table className="min-w-full divide-y divide-gray-100">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-2 text-left text-xs font-medium text-gray-600 uppercase">
                  Event Type
                </th>
                <th className="px-4 py-2 text-left text-xs font-medium text-gray-600 uppercase">
                  Channel
                </th>
                <th className="px-4 py-2 text-left text-xs font-medium text-gray-600 uppercase">
                  Status
                </th>
                <th className="px-4 py-2 text-left text-xs font-medium text-gray-600 uppercase">
                  Retries
                </th>
                <th className="px-4 py-2 text-left text-xs font-medium text-gray-600 uppercase">
                  Queued At
                </th>
                {canManage && (
                  <th className="px-4 py-2 text-left text-xs font-medium text-gray-600 uppercase">
                    Actions
                  </th>
                )}
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {events.map((ev) => (
                <tr key={ev.id} data-testid={`outbox-row-${ev.id}`}>
                  <td className="px-4 py-3 text-sm text-gray-800">{ev.event_type}</td>
                  <td className="px-4 py-3 text-sm text-gray-700">{ev.channel}</td>
                  <td className="px-4 py-3">
                    <OutboxStatusBadge status={ev.status} showTooltip />
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-600">{ev.retry_count}</td>
                  <td className="px-4 py-3 text-sm text-gray-600">{formatDate(ev.created_at)}</td>
                  {canManage && (
                    <td className="px-4 py-3 text-sm space-x-2">
                      {ev.status === OutboxEventStatus.PENDING && (
                        <>
                          <button
                            className="text-blue-600 hover:underline disabled:opacity-50"
                            onClick={() => markReady.mutate(ev.id)}
                            disabled={markReady.isPending}
                            data-testid={`mark-ready-${ev.id}`}
                          >
                            Mark Ready
                          </button>
                          <button
                            className="text-red-600 hover:underline disabled:opacity-50"
                            onClick={() => cancelEvent.mutate(ev.id)}
                            disabled={cancelEvent.isPending}
                            data-testid={`cancel-event-${ev.id}`}
                          >
                            Cancel
                          </button>
                        </>
                      )}
                    </td>
                  )}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
