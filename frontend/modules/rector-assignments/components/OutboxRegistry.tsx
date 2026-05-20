'use client';

import React, { useState } from 'react';
import { useOutboxEvents, useMarkOutboxEventReady, useCancelOutboxEvent } from '../hooks';
import { OutboxEventStatus, OutboxChannel } from '../types';
import type { OutboxEventFilters } from '../types';
import { OutboxStatusBadge } from './OutboxStatusBadge';
import { PERMISSIONS } from '@/shared/config/permissions';
import { PermissionGate } from '@/shared/auth/permission-gate';
import { LoadingState, ErrorState } from '@/shared/ui/page-states';

function formatDate(iso: string): string {
  try { return new Date(iso).toLocaleString(); } catch { return iso; }
}

export function OutboxRegistry() {
  const [filters, setFilters] = useState<OutboxEventFilters>({});
  const { data, isLoading, isError } = useOutboxEvents(filters);

  return (
    <div data-testid="outbox-registry">
      {/* Required labels */}
      <div
        className="mb-4 rounded border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800"
        data-testid="outbox-dispatch-disabled-notice"
      >
        <strong>Dispatch disabled.</strong> Notification intent records only.
        Live email/SMS dispatch is not enabled for this release.
        Provider delivery is out of scope for this release.
      </div>

      {/* Filters */}
      <div className="mb-4 flex flex-wrap gap-3 bg-white rounded-lg border border-gray-200 px-4 py-3">
        <div>
          <label className="block text-xs font-medium text-gray-600 mb-1">Status</label>
          <select
            className="px-2 py-1 border border-gray-300 rounded text-sm"
            value={filters.status ?? ''}
            onChange={(e) =>
              setFilters((f) => ({
                ...f,
                status: e.target.value ? (e.target.value as OutboxEventStatus) : undefined,
              }))
            }
            data-testid="outbox-status-filter"
          >
            <option value="">All</option>
            <option value={OutboxEventStatus.PENDING}>Intent queued (PENDING)</option>
            <option value={OutboxEventStatus.READY}>Ready</option>
            <option value={OutboxEventStatus.CANCELLED}>Cancelled</option>
          </select>
        </div>

        <div>
          <label className="block text-xs font-medium text-gray-600 mb-1">Channel</label>
          <select
            className="px-2 py-1 border border-gray-300 rounded text-sm"
            value={filters.channel ?? ''}
            onChange={(e) =>
              setFilters((f) => ({
                ...f,
                channel: e.target.value ? (e.target.value as OutboxChannel) : undefined,
              }))
            }
            data-testid="outbox-channel-filter"
          >
            <option value="">All</option>
            <option value={OutboxChannel.IN_APP}>In-App</option>
            <option value={OutboxChannel.EMAIL}>Email</option>
            <option value={OutboxChannel.SMS}>SMS</option>
          </select>
        </div>
      </div>

      {isLoading && <LoadingState message="Loading notification intents..." />}
      {isError && <ErrorState message="Failed to load notification registry." />}

      {!isLoading && !isError && data && (
        <>
          {data.items.length === 0 ? (
            <div
              className="rounded-lg border border-gray-200 bg-white p-10 text-center"
              data-testid="outbox-empty-state"
            >
              <p className="text-gray-500">No notification intents found.</p>
            </div>
          ) : (
            <div className="overflow-hidden rounded-lg border border-gray-200 bg-white">
              <table className="min-w-full divide-y divide-gray-100">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-4 py-2 text-left text-xs font-medium text-gray-600 uppercase">Assignment</th>
                    <th className="px-4 py-2 text-left text-xs font-medium text-gray-600 uppercase">Event Type</th>
                    <th className="px-4 py-2 text-left text-xs font-medium text-gray-600 uppercase">Channel</th>
                    <th className="px-4 py-2 text-left text-xs font-medium text-gray-600 uppercase">Status</th>
                    <th className="px-4 py-2 text-left text-xs font-medium text-gray-600 uppercase">Queued At</th>
                    <PermissionGate permission={PERMISSIONS.RECTOR_ASSIGNMENTS_OUTBOX_MANAGE}>
                      <th className="px-4 py-2 text-left text-xs font-medium text-gray-600 uppercase">Actions</th>
                    </PermissionGate>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {data.items.map((ev) => (
                    <OutboxRow key={ev.id} ev={ev} />
                  ))}
                </tbody>
              </table>
            </div>
          )}

          <p className="mt-3 text-xs text-gray-500">
            PENDING = queued · READY = cleared for dispatch · CANCELLED = withdrawn ·{' '}
            Provider delivery is out of scope for this release.
          </p>
        </>
      )}
    </div>
  );
}

function OutboxRow({ ev }: { ev: { id: number; assignment_id: number; event_type: string; channel: OutboxChannel; status: OutboxEventStatus; created_at: string; retry_count: number } }) {
  const markReady = useMarkOutboxEventReady(ev.assignment_id);
  const cancelEvent = useCancelOutboxEvent(ev.assignment_id);

  return (
    <tr data-testid={`outbox-global-row-${ev.id}`}>
      <td className="px-4 py-3 text-sm text-blue-600">#{ev.assignment_id}</td>
      <td className="px-4 py-3 text-sm text-gray-800">{ev.event_type}</td>
      <td className="px-4 py-3 text-sm text-gray-700">{ev.channel}</td>
      <td className="px-4 py-3">
        <OutboxStatusBadge status={ev.status} showTooltip />
      </td>
      <td className="px-4 py-3 text-sm text-gray-600">{formatDate(ev.created_at)}</td>
      <PermissionGate permission={PERMISSIONS.RECTOR_ASSIGNMENTS_OUTBOX_MANAGE}>
        <td className="px-4 py-3 text-sm space-x-2">
          {ev.status === OutboxEventStatus.PENDING && (
            <>
              <button
                className="text-blue-600 hover:underline disabled:opacity-50"
                onClick={() => markReady.mutate(ev.id)}
                disabled={markReady.isPending}
                data-testid={`global-mark-ready-${ev.id}`}
              >
                Mark Ready
              </button>
              <button
                className="text-red-600 hover:underline disabled:opacity-50"
                onClick={() => cancelEvent.mutate(ev.id)}
                disabled={cancelEvent.isPending}
                data-testid={`global-cancel-${ev.id}`}
              >
                Cancel
              </button>
            </>
          )}
        </td>
      </PermissionGate>
    </tr>
  );
}
