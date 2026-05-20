'use client';

/**
 * Overdue Assignments Board
 * Filtered registry showing only overdue + escalated assignments.
 */

import React from 'react';
import Link from 'next/link';
import { useRectorAssignmentList } from '@/modules/rector-assignments/hooks';
import {
  STATUS_LABELS,
  STATUS_BADGE_VARIANTS,
} from '@/modules/rector-assignments/status';
import { PERMISSIONS } from '@/shared/config/permissions';
import { RequirePermission } from '@/shared/auth/permission-gate';
import { PageHeader } from '@/shared/ui/page-header';
import { LoadingState, ErrorState } from '@/shared/ui/page-states';
import { Badge } from '@/shared/ui/badge';

export default function OverdueAssignmentsPage() {
  const { data: overdueList, isLoading, isError } = useRectorAssignmentList({
    overdue_only: true,
  });

  if (isLoading) return <LoadingState message="Loading overdue assignments..." />;
  if (isError) return <ErrorState message="Failed to load overdue assignments." />;

  return (
    <RequirePermission permission={PERMISSIONS.RECTOR_ASSIGNMENTS_DASHBOARD_READ}>
      <div className="min-h-screen bg-gray-50">
        <PageHeader
          title="Overdue & Escalations"
        />

        <div className="max-w-5xl mx-auto px-4 py-6">
          {overdueList && overdueList.length > 0 ? (
            <div className="bg-white rounded-lg shadow overflow-hidden">
              <div className="px-5 py-4 border-b border-gray-100">
                <p className="text-sm font-medium text-red-700">
                  {overdueList.length} overdue assignment{overdueList.length !== 1 ? 's' : ''} require attention.
                </p>
              </div>
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th scope="col" className="px-5 py-3 text-left text-xs font-medium text-gray-600 uppercase">Title</th>
                    <th scope="col" className="px-5 py-3 text-left text-xs font-medium text-gray-600 uppercase">Priority</th>
                    <th scope="col" className="px-5 py-3 text-left text-xs font-medium text-gray-600 uppercase">Due Date</th>
                    <th scope="col" className="px-5 py-3 text-left text-xs font-medium text-gray-600 uppercase">Status</th>
                    <th scope="col" className="px-5 py-3 text-left text-xs font-medium text-gray-600 uppercase">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {overdueList.map((a) => (
                    <tr
                      key={a.id}
                      className="bg-red-50"
                      data-testid={`overdue-row-${a.id}`}
                    >
                      <td className="px-5 py-3 text-sm font-medium text-gray-900">
                        {a.title}
                      </td>
                      <td className="px-5 py-3 text-sm text-gray-700">{a.priority}</td>
                      <td className="px-5 py-3 text-sm text-red-700 font-medium">
                        {a.due_date ? new Date(a.due_date).toLocaleDateString() : '—'}
                      </td>
                      <td className="px-5 py-3">
                        <Badge variant={STATUS_BADGE_VARIANTS[a.status]}>
                          {STATUS_LABELS[a.status]}
                        </Badge>
                      </td>
                      <td className="px-5 py-3 text-sm">
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
          ) : (
            <div className="bg-white rounded-lg shadow p-10 text-center" data-testid="no-overdue">
              <p className="text-green-700 font-medium mb-1">No overdue assignments.</p>
              <p className="text-gray-500 text-sm">All assignments are on track.</p>
            </div>
          )}
        </div>
      </div>
    </RequirePermission>
  );
}
