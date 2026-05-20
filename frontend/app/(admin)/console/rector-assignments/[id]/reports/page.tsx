'use client';

/**
 * Assignment Reports Sub-page
 * Full reports timeline with reviewer actions.
 */

import React from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import {
  useAssignmentReports,
  useRectorAssignmentDetail,
  useReturnAssignment,
  useCompleteAssignment,
} from '@/modules/rector-assignments/hooks';
import {
  STATUS_LABELS,
  STATUS_BADGE_VARIANTS,
  canReturnByStatus,
  canCompleteByStatus,
} from '@/modules/rector-assignments/status';
import { PERMISSIONS } from '@/shared/config/permissions';
import { PermissionGate } from '@/shared/auth/permission-gate';
import { PageHeader } from '@/shared/ui/page-header';
import { LoadingState, ErrorState } from '@/shared/ui/page-states';
import { Badge } from '@/shared/ui/badge';
import { ConfirmActionDialog } from '@/shared/ui/confirm-action-dialog';

export default function AssignmentReportsPage() {
  const params = useParams();
  const id = params.id as string;

  const { data: a, isLoading: detailLoading, isError: detailError } = useRectorAssignmentDetail(id);
  const { data: reports, isLoading: reportsLoading, isError: reportsError } = useAssignmentReports(id);

  const returnMut = useReturnAssignment(id);
  const completeMut = useCompleteAssignment(id);

  if (detailLoading || reportsLoading) return <LoadingState message="Loading reports..." />;
  if (detailError || reportsError) return <ErrorState message="Failed to load reports." />;

  return (
    <div className="min-h-screen bg-gray-50">
      <PageHeader
        title="Assignment Reports"
      />

      <div className="max-w-4xl mx-auto px-4 py-6 space-y-6">
        {/* Assignment status chip */}
        {a && (
          <div className="flex items-center gap-4 bg-white rounded-lg shadow px-5 py-3">
            <span className="text-sm font-medium text-gray-700">{a.title}</span>
            <Badge variant={STATUS_BADGE_VARIANTS[a.status]}>
              {STATUS_LABELS[a.status]}
            </Badge>
          </div>
        )}

        {/* Reviewer actions */}
        {a && (
          <div className="flex gap-2">
            {canReturnByStatus(a.status) && (
              <PermissionGate permission={PERMISSIONS.RECTOR_ASSIGNMENTS_RETURN}>
                <ConfirmActionDialog
                  trigger={
                    <button
                      className="px-3 py-1.5 text-sm bg-amber-600 text-white rounded-md hover:bg-amber-700"
                      data-testid="return-btn"
                    >
                      Return for Revision
                    </button>
                  }
                  title="Return for revision?"
                  description="The report will be sent back to the executor for correction."
                  confirmLabel="Return"
                  onConfirm={() => returnMut.mutate({ reason: 'Report returned for revision' })}
                />
              </PermissionGate>
            )}

            {canCompleteByStatus(a.status) && (
              <PermissionGate permission={PERMISSIONS.RECTOR_ASSIGNMENTS_COMPLETE}>
                <ConfirmActionDialog
                  trigger={
                    <button
                      className="px-3 py-1.5 text-sm bg-green-600 text-white rounded-md hover:bg-green-700"
                      data-testid="complete-btn"
                    >
                      Approve & Complete
                    </button>
                  }
                  title="Complete this assignment?"
                  description="Approving will mark the assignment as completed."
                  confirmLabel="Complete"
                  onConfirm={() => completeMut.mutate({})}
                />
              </PermissionGate>
            )}
          </div>
        )}

        {/* Reports list */}
        {reports && reports.length > 0 ? (
          <div className="bg-white rounded-lg shadow overflow-hidden">
            <ol className="divide-y divide-gray-100">
              {reports.map((r) => (
                <li key={r.id} className="p-5" data-testid={`report-${r.id}`}>
                  <div className="flex items-center gap-3 mb-2">
                    <Badge variant={r.status === 'SUBMITTED' ? 'success' : 'warning'}>
                      {r.status}
                    </Badge>
                    <span className="text-xs text-gray-500">
                      Submitted: {new Date(r.submitted_at).toLocaleString()}
                    </span>
                    {r.reviewed_at && (
                      <span className="text-xs text-gray-500">
                        Reviewed: {new Date(r.reviewed_at).toLocaleString()}
                      </span>
                    )}
                  </div>
                  {r.summary && (
                    <p className="text-sm text-gray-800 whitespace-pre-wrap">{r.summary}</p>
                  )}
                  {r.next_steps && (
                    <div className="mt-2 pl-3 border-l-2 border-blue-200">
                      <p className="text-xs font-medium text-blue-700">Next steps:</p>
                      <p className="text-sm text-gray-700">{r.next_steps}</p>
                    </div>
                  )}
                </li>
              ))}
            </ol>
          </div>
        ) : (
          <div className="bg-white rounded-lg shadow p-10 text-center" data-testid="no-reports">
            <p className="text-gray-500">No reports submitted for this assignment.</p>
          </div>
        )}
      </div>
    </div>
  );
}
