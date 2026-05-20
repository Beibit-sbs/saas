'use client';

import React from 'react';
import Link from 'next/link';
import { useRectorAssignmentList } from '../hooks';
import { AssignmentStatus } from '../types';
import { LoadingState, ErrorState } from '@/shared/ui/page-states';

export function EscalationQueuePanel() {
  const { data: escalated, isLoading, isError } = useRectorAssignmentList({
    status: AssignmentStatus.ESCALATED,
  });

  return (
    <div data-testid="escalation-queue-panel">
      {/* Required anti-fake notice */}
      <div
        className="mb-3 rounded border border-amber-200 bg-amber-50 px-4 py-2 text-sm text-amber-800"
        data-testid="escalation-manual-confirmation-notice"
      >
        Escalation is manual-confirmation only. No autonomous dispatch.
        Manual confirmation required for all escalation actions.
      </div>

      {isLoading && <LoadingState message="Loading escalation queue..." />}
      {isError && <ErrorState message="Failed to load escalation queue." />}

      {!isLoading && !isError && (!escalated || escalated.length === 0) && (
        <p className="text-sm text-gray-500" data-testid="escalation-queue-empty">
          No escalations pending manual confirmation.
        </p>
      )}

      {!isLoading && !isError && escalated && escalated.length > 0 && (
        <div className="overflow-hidden rounded-lg border border-orange-200 bg-white">
          <table className="min-w-full divide-y divide-gray-100">
            <thead className="bg-orange-50">
              <tr>
                <th className="px-4 py-2 text-left text-xs font-medium text-orange-800 uppercase">Assignment</th>
                <th className="px-4 py-2 text-left text-xs font-medium text-orange-800 uppercase">Priority</th>
                <th className="px-4 py-2 text-left text-xs font-medium text-orange-800 uppercase">Due Date</th>
                <th className="px-4 py-2 text-left text-xs font-medium text-orange-800 uppercase">Confirmation</th>
                <th className="px-4 py-2 text-left text-xs font-medium text-orange-800 uppercase">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {escalated.map((a) => (
                <tr key={a.id} data-testid={`escalation-queue-row-${a.id}`}>
                  <td className="px-4 py-3 text-sm font-medium text-gray-900">{a.title}</td>
                  <td className="px-4 py-3 text-sm text-gray-700">{a.priority}</td>
                  <td className="px-4 py-3 text-sm text-gray-700">
                    {a.due_date ? new Date(a.due_date).toLocaleDateString() : '—'}
                  </td>
                  <td className="px-4 py-3 text-sm">
                    <span
                      className="inline-flex items-center rounded bg-amber-100 px-2 py-0.5 text-xs font-medium text-amber-800 border border-amber-300"
                      data-testid={`escalation-manual-badge-${a.id}`}
                    >
                      Manual confirmation required
                    </span>
                  </td>
                  <td className="px-4 py-3 text-sm">
                    <Link
                      href={`/console/rector-assignments/${a.id}`}
                      className="text-blue-600 hover:underline"
                    >
                      View
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
