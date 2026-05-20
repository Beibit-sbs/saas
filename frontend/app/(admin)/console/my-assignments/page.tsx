'use client';

/**
 * Executor Inbox — My Assignments
 * Shows assignments assigned to the current user.
 */

import React from 'react';
import Link from 'next/link';
import { useMyRectorAssignments } from '@/modules/rector-assignments/hooks';
import {
  STATUS_LABELS,
  STATUS_BADGE_VARIANTS,
  canSubmitReportByStatus,
} from '@/modules/rector-assignments/status';
import { PERMISSIONS } from '@/shared/config/permissions';
import { RequirePermission } from '@/shared/auth/permission-gate';
import { PageHeader } from '@/shared/ui/page-header';
import { LoadingState, ErrorState } from '@/shared/ui/page-states';
import { Badge } from '@/shared/ui/badge';

export default function MyAssignmentsPage() {
  const { data: assignments, isLoading, isError } = useMyRectorAssignments();

  if (isLoading) return <LoadingState message="Loading your assignments..." />;
  if (isError) return <ErrorState message="Failed to load your assignments." />;

  const urgentCount = assignments?.filter((a) => a.is_overdue || a.priority === 'CRITICAL').length ?? 0;

  return (
    <RequirePermission permission={PERMISSIONS.RECTOR_ASSIGNMENTS_LIST}>
      <div className="min-h-screen bg-gray-50">
        <PageHeader title="My Assignments" />

        <div className="max-w-5xl mx-auto px-4 py-6 space-y-6">
          {urgentCount > 0 && (
            <div
              className="rounded-lg border border-red-200 bg-red-50 p-4"
              role="alert"
              data-testid="urgent-alert"
            >
              <p className="text-sm text-red-800">
                {urgentCount} assignment{urgentCount !== 1 ? 's' : ''} require urgent attention.
              </p>
            </div>
          )}

          {assignments && assignments.length > 0 ? (
            <div className="bg-white rounded-lg shadow overflow-hidden">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th scope="col" className="px-5 py-3 text-left text-xs font-medium text-gray-600 uppercase">Title</th>
                    <th scope="col" className="px-5 py-3 text-left text-xs font-medium text-gray-600 uppercase">Priority</th>
                    <th scope="col" className="px-5 py-3 text-left text-xs font-medium text-gray-600 uppercase">Due Date</th>
                    <th scope="col" className="px-5 py-3 text-left text-xs font-medium text-gray-600 uppercase">Status</th>
                    <th scope="col" className="px-5 py-3 text-left text-xs font-medium text-gray-600 uppercase">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {assignments.map((a) => (
                    <tr
                      key={a.id}
                      className={a.is_overdue ? 'bg-red-50' : ''}
                      data-testid={`my-assignment-row-${a.id}`}
                    >
                      <td className="px-5 py-3 text-sm font-medium text-gray-900">
                        {a.title}
                        {a.is_overdue && (
                          <span className="ml-2 text-xs text-red-600 font-medium">OVERDUE</span>
                        )}
                      </td>
                      <td className="px-5 py-3 text-sm text-gray-700">{a.priority}</td>
                      <td className="px-5 py-3 text-sm text-gray-700">
                        {a.due_date ? new Date(a.due_date).toLocaleDateString() : '—'}
                      </td>
                      <td className="px-5 py-3">
                        <Badge
                          variant={STATUS_BADGE_VARIANTS[a.status]}
                          data-testid={`my-status-badge-${a.id}`}
                        >
                          {STATUS_LABELS[a.status]}
                        </Badge>
                      </td>
                      <td className="px-5 py-3 flex items-center gap-2">
                        <Link
                          href={`/console/my-assignments/${a.id}`}
                          className="text-sm text-blue-600 hover:underline"
                          data-testid={`view-my-assignment-${a.id}`}
                        >
                          View
                        </Link>
                        {canSubmitReportByStatus(a.status) && (
                          <Link
                            href={`/console/my-assignments/${a.id}/report`}
                            className="text-sm text-green-700 hover:underline font-medium"
                            data-testid={`submit-report-${a.id}`}
                          >
                            Submit Report
                          </Link>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="bg-white rounded-lg shadow p-10 text-center" data-testid="empty-my-assignments">
              <p className="text-gray-500">No assignments have been assigned to you.</p>
            </div>
          )}
        </div>
      </div>
    </RequirePermission>
  );
}
