'use client';

/**
 * Rector Assignment Detail Page
 * Multi-tab: Overview | Tasks | Assignees | Reports | Evidence | Comments | Audit
 *
 * Lifecycle actions (assign, accept, return, complete, escalate, cancel, archive)
 * are gated by both permission and status predicates.
 */

import React, { useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import {
  useRectorAssignmentDetail,
  useAssignmentStatusHistory,
  useAssignmentComments,
  useAssignmentEvidence,
  useAssignmentReports,
  useAssignmentAudit,
  useAssignAssignment,
  useAcceptAssignment,
  useReturnAssignment,
  useCompleteAssignment,
  useEscalateAssignment,
  useCancelAssignment,
  useArchiveAssignment,
  useAddComment,
} from '@/modules/rector-assignments/hooks';
import {
  STATUS_LABELS,
  STATUS_BADGE_VARIANTS,
  canAssignByStatus,
  canAcceptByStatus,
  canReturnByStatus,
  canCompleteByStatus,
  canEscalateByStatus,
  canCancelByStatus,
  canArchiveByStatus,
} from '@/modules/rector-assignments/status';
import { AssignmentStatus, CommentVisibility } from '@/modules/rector-assignments/types';
import { PERMISSIONS } from '@/shared/config/permissions';
import { PermissionGate, RequirePermission } from '@/shared/auth/permission-gate';
import { PageHeader } from '@/shared/ui/page-header';
import { LoadingState, ErrorState } from '@/shared/ui/page-states';
import { Badge } from '@/shared/ui/badge';
import { ConfirmActionDialog } from '@/shared/ui/confirm-action-dialog';

type Tab = 'overview' | 'reports' | 'evidence' | 'comments' | 'history' | 'audit';

export default function AssignmentDetailPage() {
  const params = useParams();
  const router = useRouter();
  const id = params.id as string;

  const [activeTab, setActiveTab] = useState<Tab>('overview');
  const [commentText, setCommentText] = useState('');
  const [commentVisibility, setCommentVisibility] = useState<CommentVisibility>(
    CommentVisibility.INTERNAL,
  );

  const { data: a, isLoading, isError } = useRectorAssignmentDetail(id);
  const { data: history } = useAssignmentStatusHistory(id);
  const { data: comments } = useAssignmentComments(id);
  const { data: evidence } = useAssignmentEvidence(id);
  const { data: reports } = useAssignmentReports(id);
  const { data: audit } = useAssignmentAudit(id);

  const assignMut = useAssignAssignment(id);
  const acceptMut = useAcceptAssignment(id);
  const returnMut = useReturnAssignment(id);
  const completeMut = useCompleteAssignment(id);
  const escalateMut = useEscalateAssignment(id);
  const cancelMut = useCancelAssignment(id);
  const archiveMut = useArchiveAssignment(id);
  const addCommentMut = useAddComment(id);

  if (isLoading) return <LoadingState message="Loading assignment..." />;
  if (isError || !a) return <ErrorState message="Failed to load assignment." />;

  const TABS: { key: Tab; label: string }[] = [
    { key: 'overview', label: 'Overview' },
    { key: 'reports', label: `Reports (${reports?.length ?? 0})` },
    { key: 'evidence', label: `Evidence (${evidence?.length ?? 0})` },
    { key: 'comments', label: `Comments (${comments?.length ?? 0})` },
    { key: 'history', label: 'History' },
    { key: 'audit', label: 'Audit' },
  ];

  async function handleComment(e: React.FormEvent) {
    e.preventDefault();
    if (!commentText.trim()) return;
    await addCommentMut.mutateAsync({ content: commentText.trim(), visibility: commentVisibility });
    setCommentText('');
  }

  return (
    <RequirePermission permission={PERMISSIONS.RECTOR_ASSIGNMENTS_LIST}>
      <div className="min-h-screen bg-gray-50">
        <PageHeader
          title={a.title}
        />

        <div className="max-w-5xl mx-auto px-4 py-6 space-y-6">
          {/* Header strip */}
          <div className="flex items-center gap-4 bg-white rounded-lg shadow px-5 py-4">
            <Badge
              variant={STATUS_BADGE_VARIANTS[a.status]}
              data-testid="status-badge"
            >
              {STATUS_LABELS[a.status] ?? a.status}
            </Badge>
            <span className="text-sm text-gray-600">Priority: {a.priority}</span>
            {a.due_date && (
              <span className="text-sm text-gray-600">
                Due:{' '}
                <span className={a.is_overdue ? 'text-red-600 font-medium' : ''}>
                  {new Date(a.due_date).toLocaleDateString()}
                  {a.is_overdue && ' (OVERDUE)'}
                </span>
              </span>
            )}

            {/* Lifecycle actions */}
            <div className="ml-auto flex flex-wrap gap-2">
              {canAssignByStatus(a.status) && (
                <PermissionGate permission={PERMISSIONS.RECTOR_ASSIGNMENTS_ASSIGN}>
                  <Link
                    href={`/console/rector-assignments/${id}?action=assign`}
                    className="px-3 py-1.5 text-sm bg-blue-600 text-white rounded-md hover:bg-blue-700"
                    data-testid="assign-btn"
                  >
                    Assign
                  </Link>
                </PermissionGate>
              )}

              {canAcceptByStatus(a.status) && (
                <PermissionGate permission={PERMISSIONS.RECTOR_ASSIGNMENTS_ACCEPT}>
                  <ConfirmActionDialog
                    trigger={
                      <button
                        className="px-3 py-1.5 text-sm bg-green-600 text-white rounded-md hover:bg-green-700"
                        data-testid="accept-btn"
                      >
                        Accept
                      </button>
                    }
                    title="Accept assignment?"
                    description="This will mark the assignment as accepted and move it to in-progress."
                    confirmLabel="Accept"
                    onConfirm={() => acceptMut.mutate()}
                  />
                </PermissionGate>
              )}

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
                    description="The report will be returned to the executor for correction."
                    confirmLabel="Return"
                    onConfirm={() => returnMut.mutate({ reason: 'Returned for revision' })}
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
                        Mark Complete
                      </button>
                    }
                    title="Complete this assignment?"
                    description="This will mark the assignment as completed. This action cannot be undone."
                    confirmLabel="Complete"
                    onConfirm={() => completeMut.mutate({})}
                  />
                </PermissionGate>
              )}

              {canEscalateByStatus(a.status) && (
                <PermissionGate permission={PERMISSIONS.RECTOR_ASSIGNMENTS_ESCALATE}>
                  <ConfirmActionDialog
                    trigger={
                      <button
                        className="px-3 py-1.5 text-sm bg-red-600 text-white rounded-md hover:bg-red-700"
                        data-testid="escalate-btn"
                      >
                        Escalate
                      </button>
                    }
                    title="Escalate this assignment?"
                    description="This will escalate the assignment to upper management."
                    confirmLabel="Escalate"
                    onConfirm={() =>
                      escalateMut.mutate({ escalated_to_role: 'rector', reason: 'Escalated via UI' })
                    }
                  />
                </PermissionGate>
              )}

              {canCancelByStatus(a.status) && (
                <PermissionGate permission={PERMISSIONS.RECTOR_ASSIGNMENTS_CANCEL}>
                  <ConfirmActionDialog
                    trigger={
                      <button
                        className="px-3 py-1.5 text-sm bg-gray-200 text-gray-800 rounded-md hover:bg-gray-300"
                        data-testid="cancel-btn"
                      >
                        Cancel
                      </button>
                    }
                    title="Cancel this assignment?"
                    description="This will cancel the assignment. This action cannot be undone."
                    confirmLabel="Cancel Assignment"
                    variant="destructive"
                    onConfirm={() => cancelMut.mutate({ reason: 'Cancelled via UI' })}
                  />
                </PermissionGate>
              )}

              {canArchiveByStatus(a.status) && (
                <PermissionGate permission={PERMISSIONS.RECTOR_ASSIGNMENTS_ARCHIVE}>
                  <ConfirmActionDialog
                    trigger={
                      <button
                        className="px-3 py-1.5 text-sm bg-gray-400 text-white rounded-md hover:bg-gray-500"
                        data-testid="archive-btn"
                      >
                        Archive
                      </button>
                    }
                    title="Archive this assignment?"
                    description="Archived assignments are read-only. This action is reversible only by an admin."
                    confirmLabel="Archive"
                    onConfirm={() => archiveMut.mutate({})}
                  />
                </PermissionGate>
              )}
            </div>
          </div>

          {/* Tab Navigation */}
          <div className="flex gap-2 border-b border-gray-200" role="tablist">
            {TABS.map((tab) => (
              <button
                key={tab.key}
                role="tab"
                aria-selected={activeTab === tab.key}
                onClick={() => setActiveTab(tab.key)}
                className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
                  activeTab === tab.key
                    ? 'border-blue-600 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700'
                }`}
                data-testid={`tab-${tab.key}`}
              >
                {tab.label}
              </button>
            ))}
          </div>

          {/* Tab Panels */}
          <div role="tabpanel" data-testid={`panel-${activeTab}`}>
            {activeTab === 'overview' && (
              <div className="bg-white rounded-lg shadow p-6 space-y-4">
                <dl className="grid grid-cols-2 gap-4">
                  <div>
                    <dt className="text-xs font-medium text-gray-500 uppercase">Title</dt>
                    <dd className="mt-1 text-sm text-gray-900">{a.title}</dd>
                  </div>
                  <div>
                    <dt className="text-xs font-medium text-gray-500 uppercase">Status</dt>
                    <dd className="mt-1">
                      <Badge variant={STATUS_BADGE_VARIANTS[a.status]}>
                        {STATUS_LABELS[a.status]}
                      </Badge>
                    </dd>
                  </div>
                  <div>
                    <dt className="text-xs font-medium text-gray-500 uppercase">Priority</dt>
                    <dd className="mt-1 text-sm text-gray-900">{a.priority}</dd>
                  </div>
                  <div>
                    <dt className="text-xs font-medium text-gray-500 uppercase">Created</dt>
                    <dd className="mt-1 text-sm text-gray-900">
                      {new Date(a.created_at).toLocaleString()}
                    </dd>
                  </div>
                  {a.due_date && (
                    <div>
                      <dt className="text-xs font-medium text-gray-500 uppercase">Due Date</dt>
                      <dd className="mt-1 text-sm">
                        <span className={a.is_overdue ? 'text-red-600 font-medium' : 'text-gray-900'}>
                          {new Date(a.due_date).toLocaleDateString()}
                        </span>
                      </dd>
                    </div>
                  )}
                  {a.recurrence_type !== 'NONE' && (
                    <div>
                      <dt className="text-xs font-medium text-gray-500 uppercase">Recurrence</dt>
                      <dd className="mt-1 text-sm text-gray-900">{a.recurrence_type}</dd>
                    </div>
                  )}
                </dl>

                {a.description && (
                  <div>
                    <h3 className="text-xs font-medium text-gray-500 uppercase mb-1">Description</h3>
                    <p className="text-sm text-gray-800 whitespace-pre-wrap">{a.description}</p>
                  </div>
                )}

                {/* Assignees */}
                {a.assignees && a.assignees.length > 0 && (
                  <div>
                    <h3 className="text-xs font-medium text-gray-500 uppercase mb-2">Assignees</h3>
                    <ul className="space-y-1">
                      {a.assignees.map((assignee) => (
                        <li key={assignee.id} className="text-sm text-gray-800">
                          {assignee.user_id}{' '}
                          <span className="text-gray-500">({assignee.role_on_assignment})</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            )}

            {activeTab === 'reports' && (
              <div className="bg-white rounded-lg shadow p-6 space-y-4">
                <div className="flex items-center justify-between mb-2">
                  <h3 className="font-medium">Submission Reports</h3>
                  <PermissionGate permission={PERMISSIONS.RECTOR_ASSIGNMENTS_REPORT_SUBMIT}>
                    <Link
                      href={`/console/my-assignments/${id}/report`}
                      className="px-3 py-1.5 text-sm bg-blue-600 text-white rounded-md hover:bg-blue-700"
                      data-testid="add-report-link"
                    >
                      Submit Report
                    </Link>
                  </PermissionGate>
                </div>
                {reports && reports.length > 0 ? (
                  <ul className="divide-y divide-gray-100">
                    {reports.map((r) => (
                      <li key={r.id} className="py-3">
                        <div className="flex items-center gap-3">
                          <Badge variant={r.status === 'SUBMITTED' ? 'success' : 'warning'}>
                            {r.status}
                          </Badge>
                          <span className="text-xs text-gray-500">
                            {new Date(r.submitted_at).toLocaleString()}
                          </span>
                        </div>
                        {r.summary && (
                          <p className="mt-1 text-sm text-gray-700">{r.summary}</p>
                        )}
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="text-sm text-gray-500" data-testid="no-reports">
                    No reports submitted yet.
                  </p>
                )}
              </div>
            )}

            {activeTab === 'evidence' && (
              <div className="bg-white rounded-lg shadow p-6 space-y-4">
                <h3 className="font-medium">Evidence Attachments</h3>
                {evidence && evidence.length > 0 ? (
                  <ul className="divide-y divide-gray-100">
                    {evidence.map((ev) => (
                      <li key={ev.id} className="py-3 flex items-center gap-3">
                        <span className="text-sm font-medium text-gray-800">{ev.evidence_type}</span>
                        {ev.url && (
                          <a
                            href={ev.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-sm text-blue-600 hover:underline"
                          >
                            View
                          </a>
                        )}
                        {ev.description && (
                          <span className="text-sm text-gray-500">{ev.description}</span>
                        )}
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="text-sm text-gray-500" data-testid="no-evidence">
                    No evidence attached.
                  </p>
                )}
              </div>
            )}

            {activeTab === 'comments' && (
              <div className="bg-white rounded-lg shadow p-6 space-y-4">
                <h3 className="font-medium">Comments</h3>
                {comments && comments.length > 0 ? (
                  <ul className="space-y-3">
                    {comments.map((c) => (
                      <li key={c.id} className="rounded border border-gray-100 p-3">
                        <div className="flex items-center gap-2 mb-1">
                          <span className="text-xs text-gray-500">
                            {new Date(c.created_at).toLocaleString()}
                          </span>
                          {c.visibility !== CommentVisibility.INTERNAL && (
                            <Badge variant="secondary">{c.visibility}</Badge>
                          )}
                        </div>
                        <p className="text-sm text-gray-800">{c.content}</p>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="text-sm text-gray-500" data-testid="no-comments">
                    No comments yet.
                  </p>
                )}

                <PermissionGate permission={PERMISSIONS.RECTOR_ASSIGNMENTS_COMMENT}>
                  <form onSubmit={handleComment} className="mt-4 space-y-2" data-testid="comment-form">
                    <textarea
                      value={commentText}
                      onChange={(e) => setCommentText(e.target.value)}
                      rows={3}
                      placeholder="Add a comment..."
                      className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
                      data-testid="comment-input"
                    />
                    <div className="flex items-center gap-3">
                      <select
                        value={commentVisibility}
                        onChange={(e) => setCommentVisibility(e.target.value as CommentVisibility)}
                        className="px-2 py-1.5 border border-gray-300 rounded-md text-sm"
                        data-testid="comment-visibility"
                      >
                        <option value="INTERNAL">Internal</option>
                        <option value="ASSIGNEES">Assignees</option>
                        <option value="LEADERSHIP">Leadership</option>
                      </select>
                      <button
                        type="submit"
                        disabled={!commentText.trim() || addCommentMut.isPending}
                        className="px-3 py-1.5 bg-blue-600 text-white text-sm rounded-md hover:bg-blue-700 disabled:opacity-50"
                        data-testid="submit-comment-btn"
                      >
                        {addCommentMut.isPending ? 'Posting...' : 'Post Comment'}
                      </button>
                    </div>
                  </form>
                </PermissionGate>
              </div>
            )}

            {activeTab === 'history' && (
              <div className="bg-white rounded-lg shadow p-6">
                <h3 className="font-medium mb-4">Status History</h3>
                {history && history.length > 0 ? (
                  <ol className="relative border-l border-gray-200 ml-3 space-y-4">
                    {history.map((h) => (
                      <li key={h.id} className="ml-6">
                        <div className="absolute -left-1.5 w-3 h-3 rounded-full bg-blue-500" />
                        <div className="flex items-center gap-2 mb-0.5">
                          <Badge variant={STATUS_BADGE_VARIANTS[h.new_status]}>
                            {STATUS_LABELS[h.new_status]}
                          </Badge>
                          <span className="text-xs text-gray-500">
                            {new Date(h.changed_at).toLocaleString()}
                          </span>
                        </div>
                        {h.reason && (
                          <p className="text-xs text-gray-600">{h.reason}</p>
                        )}
                      </li>
                    ))}
                  </ol>
                ) : (
                  <p className="text-sm text-gray-500">No status history found.</p>
                )}
              </div>
            )}

            {activeTab === 'audit' && (
              <RequirePermission permission={PERMISSIONS.RECTOR_ASSIGNMENTS_AUDIT_READ}>
                <div className="bg-white rounded-lg shadow p-6">
                  <h3 className="font-medium mb-4">Audit Trail</h3>
                  {audit && audit.length > 0 ? (
                    <ul className="divide-y divide-gray-100">
                      {audit.map((event) => (
                        <li key={event.id} className="py-3 flex items-start gap-3">
                          <span className="text-xs text-gray-500 whitespace-nowrap mt-0.5">
                            {new Date(event.created_at).toLocaleString()}
                          </span>
                          <span className="text-sm font-medium text-gray-800">{event.event_type}</span>
                          {event.payload && (
                            <span className="text-xs text-gray-500 ml-auto">{JSON.stringify(event.payload)}</span>
                          )}
                        </li>
                      ))}
                    </ul>
                  ) : (
                    <p className="text-sm text-gray-500">No audit events recorded.</p>
                  )}
                </div>
              </RequirePermission>
            )}
          </div>
        </div>
      </div>
    </RequirePermission>
  );
}
