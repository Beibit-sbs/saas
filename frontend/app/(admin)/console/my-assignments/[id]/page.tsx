'use client';

/**
 * Executor Assignment Detail
 * Lightweight detail view for assignees — shows status, description,
 * submit-report CTA, evidence upload, and comment thread.
 */

import React, { useState } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import {
  useRectorAssignmentDetail,
  useAssignmentReports,
  useAssignmentComments,
  useAddComment,
  useAcceptAssignment,
} from '@/modules/rector-assignments/hooks';
import {
  STATUS_LABELS,
  STATUS_BADGE_VARIANTS,
  canAcceptByStatus,
  canSubmitReportByStatus,
} from '@/modules/rector-assignments/status';
import { CommentVisibility } from '@/modules/rector-assignments/types';
import { PERMISSIONS } from '@/shared/config/permissions';
import { PermissionGate, RequirePermission } from '@/shared/auth/permission-gate';
import { PageHeader } from '@/shared/ui/page-header';
import { LoadingState, ErrorState } from '@/shared/ui/page-states';
import { Badge } from '@/shared/ui/badge';
import { ConfirmActionDialog } from '@/shared/ui/confirm-action-dialog';

export default function ExecutorAssignmentDetailPage() {
  const params = useParams();
  const id = params.id as string;

  const [commentText, setCommentText] = useState('');

  const { data: a, isLoading, isError } = useRectorAssignmentDetail(id);
  const { data: reports } = useAssignmentReports(id);
  const { data: comments } = useAssignmentComments(id);
  const acceptMut = useAcceptAssignment(id);
  const addCommentMut = useAddComment(id);

  if (isLoading) return <LoadingState message="Loading assignment..." />;
  if (isError || !a) return <ErrorState message="Failed to load assignment." />;

  async function handleComment(e: React.FormEvent) {
    e.preventDefault();
    if (!commentText.trim()) return;
    await addCommentMut.mutateAsync({ content: commentText.trim(), visibility: CommentVisibility.INTERNAL });
    setCommentText('');
  }

  return (
    <RequirePermission permission={PERMISSIONS.RECTOR_ASSIGNMENTS_LIST}>
      <div className="min-h-screen bg-gray-50">
        <PageHeader
          title={a.title}
        />

        <div className="max-w-3xl mx-auto px-4 py-6 space-y-6">
          {/* Status + actions */}
          <div className="flex items-center gap-4 bg-white rounded-lg shadow px-5 py-4">
            <Badge
              variant={STATUS_BADGE_VARIANTS[a.status]}
              data-testid="exec-status-badge"
            >
              {STATUS_LABELS[a.status]}
            </Badge>
            <span className="text-sm text-gray-600">{a.priority}</span>
            {a.due_date && (
              <span className={`text-sm ${a.is_overdue ? 'text-red-600 font-medium' : 'text-gray-600'}`}>
                Due: {new Date(a.due_date).toLocaleDateString()}
                {a.is_overdue && ' (OVERDUE)'}
              </span>
            )}

            <div className="ml-auto flex gap-2">
              {canAcceptByStatus(a.status) && (
                <PermissionGate permission={PERMISSIONS.RECTOR_ASSIGNMENTS_ACCEPT}>
                  <ConfirmActionDialog
                    trigger={
                      <button
                        className="px-3 py-1.5 text-sm bg-green-600 text-white rounded-md hover:bg-green-700"
                        data-testid="exec-accept-btn"
                      >
                        Accept
                      </button>
                    }
                    title="Accept this assignment?"
                    description="You will be committing to complete and report on this assignment."
                    confirmLabel="Accept"
                    onConfirm={() => acceptMut.mutate()}
                  />
                </PermissionGate>
              )}

              {canSubmitReportByStatus(a.status) && (
                <Link
                  href={`/console/my-assignments/${id}/report`}
                  className="px-3 py-1.5 text-sm bg-blue-600 text-white rounded-md hover:bg-blue-700"
                  data-testid="exec-submit-report-btn"
                >
                  Submit Report
                </Link>
              )}
            </div>
          </div>

          {/* Assignment details */}
          <div className="bg-white rounded-lg shadow p-6 space-y-4">
            {a.description && (
              <div>
                <h3 className="text-xs font-medium text-gray-500 uppercase mb-1">Description</h3>
                <p className="text-sm text-gray-800 whitespace-pre-wrap">{a.description}</p>
              </div>
            )}

            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <span className="text-xs text-gray-500 uppercase">Created</span>
                <p className="text-gray-800">{new Date(a.created_at).toLocaleDateString()}</p>
              </div>
              {a.due_date && (
                <div>
                  <span className="text-xs text-gray-500 uppercase">Due Date</span>
                  <p className={a.is_overdue ? 'text-red-600 font-medium' : 'text-gray-800'}>
                    {new Date(a.due_date).toLocaleDateString()}
                  </p>
                </div>
              )}
            </div>
          </div>

          {/* Recent reports */}
          {reports && reports.length > 0 && (
            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="font-medium mb-3">My Reports ({reports.length})</h3>
              <ul className="space-y-2">
                {reports.slice(0, 3).map((r) => (
                  <li key={r.id} className="flex items-center gap-3">
                    <Badge variant={r.status === 'SUBMITTED' ? 'success' : 'warning'}>
                      {r.status}
                    </Badge>
                    <span className="text-xs text-gray-500">
                      {new Date(r.submitted_at).toLocaleString()}
                    </span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Comments */}
          <div className="bg-white rounded-lg shadow p-6 space-y-4">
            <h3 className="font-medium">Comments</h3>
            {comments && comments.length > 0 ? (
              <ul className="space-y-2">
                {comments.map((c) => (
                  <li key={c.id} className="rounded border border-gray-100 p-3">
                    <p className="text-xs text-gray-500 mb-1">
                      {new Date(c.created_at).toLocaleString()}
                    </p>
                    <p className="text-sm text-gray-800">{c.content}</p>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-sm text-gray-500">No comments yet.</p>
            )}

            <PermissionGate permission={PERMISSIONS.RECTOR_ASSIGNMENTS_COMMENT}>
              <form onSubmit={handleComment} className="space-y-2 mt-3" data-testid="exec-comment-form">
                <textarea
                  value={commentText}
                  onChange={(e) => setCommentText(e.target.value)}
                  rows={2}
                  placeholder="Add a comment..."
                  className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
                  data-testid="exec-comment-input"
                />
                <button
                  type="submit"
                  disabled={!commentText.trim() || addCommentMut.isPending}
                  className="px-3 py-1.5 bg-blue-600 text-white text-sm rounded-md hover:bg-blue-700 disabled:opacity-50"
                  data-testid="exec-submit-comment-btn"
                >
                  {addCommentMut.isPending ? 'Posting...' : 'Post'}
                </button>
              </form>
            </PermissionGate>
          </div>
        </div>
      </div>
    </RequirePermission>
  );
}
