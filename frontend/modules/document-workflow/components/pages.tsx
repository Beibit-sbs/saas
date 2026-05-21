'use client';

import Link from 'next/link';
import { useMemo, useState } from 'react';
import { Archive, FileText, Mail, Scale, ShieldAlert } from 'lucide-react';
import { RequirePermission, PermissionGate } from '@/shared/ui/permission-gate';
import { PageHeader } from '@/shared/ui/page-header';
import { LoadingState, ErrorState } from '@/shared/ui/page-states';
import { Button } from '@/shared/ui/button';
import { Input } from '@/shared/ui/input';
import { Badge } from '@/shared/ui/badge';
import {
  canApproveDecreeSigning,
  canApproveDocument,
  canArchiveDecree,
  canArchiveDocument,
  canRecordDecreeSignedMetadata,
  canRecordDocumentSignedMetadata,
  canRecordOutgoingSentMetadata,
  canRegisterDecree,
  canRegisterDocument,
  canStartDecreeLegalReview,
  canSubmitDocumentReview,
  canReturnDocument,
  formatUnavailableMetric,
  isArchiveRecord,
} from '../guards';
import {
  useApproveDecreeSigning,
  useApproveDocument,
  useArchiveCorrespondence,
  useArchiveDecree,
  useArchiveDocument,
  useCorrespondence,
  useCreateDecree,
  useCreateDocument,
  useCreateIncomingCorrespondence,
  useCreateOutgoingCorrespondence,
  useDecree,
  useDecrees,
  useDecreeLegalReview,
  useDecreeSignedMetadata,
  useDocument,
  useDocumentAudit,
  useDocumentHistory,
  useDocuments,
  useDocumentSignedMetadata,
  useDocumentWorkflowDashboard,
  useLinkDocumentToAssignment,
  useOutgoingSentMetadata,
  useRegisterCorrespondence,
  useRegisterDecree,
  useRegisterDocument,
  useRouteCorrespondence,
  useSubmitDocumentReview,
  useReturnDocument,
} from '../hooks';
import { DOCUMENT_WORKFLOW_PERMISSIONS } from '../permissions';
import {
  CorrespondenceDirection,
  type ArchiveRecord,
  type CorrespondenceItem,
  type DashboardSummary,
  type Document,
  type DocumentAssignmentLink,
  type DocumentAuditEvent,
  type DocumentDetail,
  type DocumentReview,
  type DocumentStatusHistory,
  type OrderDecree,
} from '../types';

const textareaClassName =
  'flex min-h-[88px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2';

function formatDate(value?: string | null) {
  if (!value) return 'Unavailable';
  try {
    return new Date(value).toLocaleString();
  } catch {
    return value;
  }
}

function formatDateOnly(value?: string | null) {
  if (!value) return 'Unavailable';
  try {
    return new Date(value).toLocaleDateString();
  } catch {
    return value;
  }
}

function humanize(value: string) {
  return value
    .toLowerCase()
    .replace(/_/g, ' ')
    .replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function getErrorMessage(error: unknown) {
  return error instanceof Error ? error.message : 'Request failed.';
}

function statusVariant(status?: string): 'default' | 'secondary' | 'destructive' | 'outline' | 'success' | 'warning' | 'info' {
  if (!status) return 'outline';
  if (status.includes('ARCHIVED') || status.includes('CANCELLED')) return 'secondary';
  if (status.includes('RETURNED') || status.includes('OVERDUE')) return 'warning';
  if (status.includes('UNDER_REVIEW') || status.includes('LEGAL_REVIEW')) return 'info';
  if (status.includes('APPROVED') || status.includes('SIGNED') || status.includes('REGISTERED')) return 'success';
  return 'outline';
}

export function DocumentStatusBadge({ status }: { status?: string }) {
  return <Badge variant={statusVariant(status)}>{status ? humanize(status) : 'Unknown'}</Badge>;
}

export function DocumentTypeBadge({ type }: { type?: string }) {
  return <Badge variant="outline">{type ? humanize(type) : 'Unspecified type'}</Badge>;
}

export function RegistryNumberBadge({ registryNumber }: { registryNumber?: string | null }) {
  return (
    <Badge variant={registryNumber ? 'success' : 'outline'}>
      {registryNumber ? `Registry ${registryNumber}` : 'Not registered'}
    </Badge>
  );
}

function SectionCard({ title, description, children }: { title: string; description?: string; children: React.ReactNode }) {
  return (
    <section className="rounded-lg border bg-background p-4 shadow-sm">
      <div className="mb-3">
        <h2 className="text-base font-semibold">{title}</h2>
        {description ? <p className="text-sm text-muted-foreground">{description}</p> : null}
      </div>
      {children}
    </section>
  );
}

function InlineNotice({ testId, children }: { testId?: string; children: React.ReactNode }) {
  return (
    <div className="rounded-md border border-amber-200 bg-amber-50 px-3 py-2 text-sm text-amber-900" data-testid={testId}>
      {children}
    </div>
  );
}

function DataQualityError({ reason }: { reason: string }) {
  return (
    <div
      className="flex min-h-[260px] flex-col items-center justify-center gap-3 rounded-lg border border-red-200 bg-red-50 px-6 py-10 text-center"
      data-testid="document-workflow-data-quality-error"
      role="alert"
    >
      <ShieldAlert className="h-8 w-8 text-red-500" />
      <p className="font-semibold text-red-800">Dashboard data could not be verified.</p>
      <p className="max-w-xl text-sm text-red-700">{reason}</p>
      <p className="text-xs text-red-600">Computed metrics are hidden until the backend trust contract is restored.</p>
    </div>
  );
}

function MutationError({ error }: { error?: string | null }) {
  if (!error) return null;
  return (
    <div className="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
      {error}
    </div>
  );
}

function MetadataGrid({ items }: { items: Array<{ label: string; value: React.ReactNode }> }) {
  return (
    <dl className="grid gap-3 md:grid-cols-2">
      {items.map((item) => (
        <div key={item.label} className="rounded-md border border-dashed px-3 py-2">
          <dt className="text-xs uppercase tracking-wide text-muted-foreground">{item.label}</dt>
          <dd className="mt-1 text-sm">{item.value}</dd>
        </div>
      ))}
    </dl>
  );
}

export function DocumentFiltersBar({
  status,
  setStatus,
  documentType,
  setDocumentType,
}: {
  status: string;
  setStatus: (value: string) => void;
  documentType: string;
  setDocumentType: (value: string) => void;
}) {
  return (
    <div className="flex flex-wrap gap-3 rounded-lg border bg-background p-4">
      <div className="min-w-[220px]">
        <label className="mb-1 block text-xs font-medium text-muted-foreground">Status</label>
        <Input value={status} onChange={(event) => setStatus(event.target.value)} placeholder="UNDER_REVIEW" />
      </div>
      <div className="min-w-[220px]">
        <label className="mb-1 block text-xs font-medium text-muted-foreground">Document type</label>
        <Input value={documentType} onChange={(event) => setDocumentType(event.target.value)} placeholder="REPORT" />
      </div>
    </div>
  );
}

export function DocumentRegistryTable({ documents }: { documents: Document[] }) {
  return (
    <div className="overflow-x-auto rounded-lg border bg-background">
      <table className="min-w-full divide-y">
        <thead className="bg-muted/30">
          <tr className="text-left text-xs uppercase tracking-wide text-muted-foreground">
            <th className="px-4 py-3">Title</th>
            <th className="px-4 py-3">Type</th>
            <th className="px-4 py-3">Status</th>
            <th className="px-4 py-3">Registry</th>
            <th className="px-4 py-3">Updated</th>
            <th className="px-4 py-3">Actions</th>
          </tr>
        </thead>
        <tbody className="divide-y">
          {documents.map((document) => (
            <tr key={document.id} data-testid={`document-row-${document.id}`}>
              <td className="px-4 py-3 text-sm font-medium">{document.title}</td>
              <td className="px-4 py-3 text-sm"><DocumentTypeBadge type={document.document_type} /></td>
              <td className="px-4 py-3 text-sm"><DocumentStatusBadge status={document.status} /></td>
              <td className="px-4 py-3 text-sm"><RegistryNumberBadge registryNumber={document.registry_number} /></td>
              <td className="px-4 py-3 text-sm">{formatDate(document.updated_at)}</td>
              <td className="px-4 py-3 text-sm">
                <Link className="text-primary underline-offset-4 hover:underline" href={`/console/documents/${document.id}`}>
                  Open
                </Link>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export function DocumentDetailHeader({ document }: { document: DocumentDetail }) {
  return (
    <SectionCard title={document.title} description="Tenant-scoped document lifecycle and metadata">
      <div className="flex flex-wrap gap-2">
        <DocumentStatusBadge status={document.status} />
        <DocumentTypeBadge type={document.document_type} />
        <RegistryNumberBadge registryNumber={document.registry_number} />
      </div>
      <div className="mt-4 space-y-2">
        <InlineNotice testId="signature-metadata-notice">Signature metadata only.</InlineNotice>
        <InlineNotice testId="no-automatic-signing-notice">No automatic signing.</InlineNotice>
        <InlineNotice testId="registry-official-notice">Registry number is assigned by registration workflow.</InlineNotice>
      </div>
      <div className="mt-4">
        <MetadataGrid
          items={[
            { label: 'Version', value: document.version },
            { label: 'Owner user', value: document.owner_user_id ?? 'Unassigned' },
            { label: 'Created by', value: document.created_by_user_id },
            { label: 'Source department', value: document.source_department_id ?? 'Not set' },
            { label: 'Linked assignment', value: document.linked_assignment_id ?? 'Not linked' },
            { label: 'Updated at', value: formatDate(document.updated_at) },
          ]}
        />
      </div>
    </SectionCard>
  );
}

export function DocumentLifecycleTimeline({ history }: { history: DocumentStatusHistory[] }) {
  return (
    <SectionCard title="Lifecycle timeline" description="Insert-only status history from the backend.">
      {history.length === 0 ? (
        <p className="text-sm text-muted-foreground">No status history available.</p>
      ) : (
        <ol className="space-y-3">
          {history.map((entry) => (
            <li key={entry.id} className="rounded-md border px-3 py-2">
              <div className="flex flex-wrap items-center gap-2">
                <DocumentStatusBadge status={entry.from_status ?? 'INITIAL'} />
                <span className="text-sm text-muted-foreground">to</span>
                <DocumentStatusBadge status={entry.to_status} />
              </div>
              <p className="mt-2 text-sm">Actor #{entry.actor_user_id}</p>
              <p className="text-xs text-muted-foreground">{formatDate(entry.created_at)}</p>
              {entry.reason ? <p className="mt-1 text-sm">Reason: {entry.reason}</p> : null}
            </li>
          ))}
        </ol>
      )}
    </SectionCard>
  );
}

export function DocumentVersionTimeline({ versions }: { versions: DocumentDetail['versions'] }) {
  return (
    <SectionCard title="Version timeline" description="Backend-sourced versions only; no synthetic drafts.">
      {versions.length === 0 ? (
        <p className="text-sm text-muted-foreground">No versions recorded.</p>
      ) : (
        <div className="space-y-3">
          {versions.map((version) => (
            <div key={version.id} className="rounded-md border px-3 py-2" data-testid={`document-version-${version.id}`}>
              <div className="flex items-center justify-between gap-3">
                <p className="font-medium">v{version.version_number} • {version.title}</p>
                <p className="text-xs text-muted-foreground">{formatDate(version.created_at)}</p>
              </div>
              {version.body_text ? <p className="mt-2 text-sm text-muted-foreground">{version.body_text}</p> : null}
            </div>
          ))}
        </div>
      )}
    </SectionCard>
  );
}

export function DocumentReviewPanel({ reviews }: { reviews: DocumentReview[] }) {
  return (
    <SectionCard title="Review panel" description="Review decisions are rendered exactly as returned by the backend.">
      {reviews.length === 0 ? (
        <p className="text-sm text-muted-foreground">No review records yet.</p>
      ) : (
        <div className="space-y-3">
          {reviews.map((review) => (
            <div key={review.id} className="rounded-md border px-3 py-2">
              <div className="flex flex-wrap gap-2">
                <Badge variant="outline">Reviewer #{review.reviewer_user_id}</Badge>
                <Badge variant="info">{humanize(review.decision)}</Badge>
              </div>
              {review.comment ? <p className="mt-2 text-sm">{review.comment}</p> : null}
              <p className="mt-1 text-xs text-muted-foreground">{formatDate(review.created_at)}</p>
            </div>
          ))}
        </div>
      )}
    </SectionCard>
  );
}

export function DocumentAssignmentLinkPanel({ document }: { document: DocumentDetail }) {
  const [assignmentId, setAssignmentId] = useState('');
  const [error, setError] = useState<string | null>(null);
  const mutation = useLinkDocumentToAssignment(document.id, assignmentId || '0');

  async function handleLink() {
    setError(null);
    if (!assignmentId.trim()) {
      setError('Assignment ID is required.');
      return;
    }
    try {
      await mutation.mutateAsync({ link_type: 'SOURCE_DOCUMENT' });
      setAssignmentId('');
    } catch (err) {
      setError(getErrorMessage(err));
    }
  }

  return (
    <SectionCard title="Assignment links" description="Human-initiated link operations only.">
      <div className="space-y-2">
        <InlineNotice testId="assignment-link-human-notice">Assignment link is human-initiated.</InlineNotice>
        <InlineNotice testId="assignment-link-status-notice">No assignment status is changed by document workflow.</InlineNotice>
      </div>
      <div className="mt-4 space-y-3">
        {document.assignment_links.length === 0 ? (
          <p className="text-sm text-muted-foreground">No assignment link.</p>
        ) : (
          document.assignment_links.map((link: DocumentAssignmentLink) => (
            <div key={link.id} className="rounded-md border px-3 py-2">
              <p className="font-medium">Assignment #{link.assignment_id}</p>
              <p className="text-sm text-muted-foreground">{humanize(link.link_type)}</p>
              <p className="text-xs text-muted-foreground">{formatDate(link.created_at)}</p>
            </div>
          ))
        )}
      </div>
      <PermissionGate permission={DOCUMENT_WORKFLOW_PERMISSIONS.DOCUMENTS_LINK_ASSIGNMENT}>
        <div className="mt-4 flex flex-wrap items-end gap-3">
          <div className="min-w-[220px]">
            <label className="mb-1 block text-xs font-medium text-muted-foreground">Assignment ID</label>
            <Input value={assignmentId} onChange={(event) => setAssignmentId(event.target.value)} placeholder="123" />
          </div>
          <Button onClick={handleLink} disabled={mutation.isPending}>Link assignment</Button>
        </div>
        <MutationError error={error} />
      </PermissionGate>
    </SectionCard>
  );
}

export function DocumentActionsBar({ document }: { document: DocumentDetail }) {
  const [registryNumber, setRegistryNumber] = useState('');
  const [reviewerUserId, setReviewerUserId] = useState('');
  const [note, setNote] = useState('');
  const [returnReason, setReturnReason] = useState('');
  const [approveComment, setApproveComment] = useState('');
  const [signedBy, setSignedBy] = useState('');
  const [signedAt, setSignedAt] = useState('');
  const [archiveReason, setArchiveReason] = useState('');
  const [error, setError] = useState<string | null>(null);

  const registerMutation = useRegisterDocument(document.id);
  const reviewMutation = useSubmitDocumentReview(document.id);
  const returnMutation = useReturnDocument(document.id);
  const approveMutation = useApproveDocument(document.id);
  const signedMutation = useDocumentSignedMetadata(document.id);
  const archiveMutation = useArchiveDocument(document.id);

  async function runAction(action: () => Promise<unknown>) {
    setError(null);
    try {
      await action();
    } catch (err) {
      setError(getErrorMessage(err));
    }
  }

  return (
    <SectionCard title="Actions" description="Only backend-supported lifecycle actions are exposed.">
      <MutationError error={error} />
      <div className="grid gap-4 lg:grid-cols-2">
        <PermissionGate permission={DOCUMENT_WORKFLOW_PERMISSIONS.DOCUMENTS_REGISTER}>
          <div className="rounded-md border p-3">
            <p className="font-medium">Register document</p>
            <p className="text-sm text-muted-foreground">Registry number is official workflow metadata.</p>
            <div className="mt-3 flex flex-wrap items-end gap-2">
              <Input value={registryNumber} onChange={(event) => setRegistryNumber(event.target.value)} placeholder="REG-2026-001" />
              <Button
                disabled={!canRegisterDocument(document.status) || registerMutation.isPending || !registryNumber.trim()}
                onClick={() => runAction(() => registerMutation.mutateAsync({ registry_number: registryNumber.trim(), version: document.version }))}
              >
                Register
              </Button>
            </div>
          </div>
        </PermissionGate>

        <PermissionGate permission={DOCUMENT_WORKFLOW_PERMISSIONS.DOCUMENTS_REVIEW}>
          <div className="rounded-md border p-3">
            <p className="font-medium">Submit review</p>
            <div className="mt-3 space-y-2">
              <Input value={reviewerUserId} onChange={(event) => setReviewerUserId(event.target.value)} placeholder="Reviewer user ID" />
              <textarea className={textareaClassName} value={note} onChange={(event) => setNote(event.target.value)} placeholder="Review note" />
              <Button
                disabled={!canSubmitDocumentReview(document.status) || reviewMutation.isPending}
                onClick={() => runAction(() => reviewMutation.mutateAsync({ reviewer_user_id: reviewerUserId ? Number(reviewerUserId) : undefined, note, version: document.version }))}
              >
                Submit review
              </Button>
            </div>
          </div>
        </PermissionGate>

        <PermissionGate permission={DOCUMENT_WORKFLOW_PERMISSIONS.DOCUMENTS_REVIEW}>
          <div className="rounded-md border p-3">
            <p className="font-medium">Return for revision</p>
            <div className="mt-3 space-y-2">
              <textarea className={textareaClassName} value={returnReason} onChange={(event) => setReturnReason(event.target.value)} placeholder="Return reason" />
              <Button
                variant="secondary"
                disabled={!canReturnDocument(document.status) || returnMutation.isPending || !returnReason.trim()}
                onClick={() => runAction(() => returnMutation.mutateAsync({ reason: returnReason.trim(), version: document.version }))}
              >
                Return document
              </Button>
            </div>
          </div>
        </PermissionGate>

        <PermissionGate permission={DOCUMENT_WORKFLOW_PERMISSIONS.DOCUMENTS_APPROVE}>
          <div className="rounded-md border p-3">
            <p className="font-medium">Approve document</p>
            <div className="mt-3 space-y-2">
              <textarea className={textareaClassName} value={approveComment} onChange={(event) => setApproveComment(event.target.value)} placeholder="Approval comment" />
              <Button
                disabled={!canApproveDocument(document.status) || approveMutation.isPending}
                onClick={() => runAction(() => approveMutation.mutateAsync({ comment: approveComment || undefined, version: document.version }))}
              >
                Approve
              </Button>
            </div>
          </div>
        </PermissionGate>

        <PermissionGate permission={DOCUMENT_WORKFLOW_PERMISSIONS.DOCUMENTS_SIGNED_METADATA_RECORD}>
          <div className="rounded-md border p-3">
            <p className="font-medium">Record signed metadata</p>
            <p className="text-sm text-muted-foreground">No automatic signing.</p>
            <div className="mt-3 space-y-2">
              <Input value={signedBy} onChange={(event) => setSignedBy(event.target.value)} placeholder="Signed by user ID" />
              <Input value={signedAt} onChange={(event) => setSignedAt(event.target.value)} placeholder="2026-05-21T12:00:00Z" />
              <Button
                disabled={!canRecordDocumentSignedMetadata(document.status) || signedMutation.isPending || !signedBy.trim()}
                onClick={() => runAction(() => signedMutation.mutateAsync({ signed_by_user_id: Number(signedBy), signed_at: signedAt || undefined, note: note || undefined, version: document.version }))}
              >
                Record signed metadata
              </Button>
            </div>
          </div>
        </PermissionGate>

        <PermissionGate permission={DOCUMENT_WORKFLOW_PERMISSIONS.DOCUMENTS_ARCHIVE}>
          <div className="rounded-md border p-3">
            <p className="font-medium">Archive document</p>
            <div className="mt-3 space-y-2">
              <textarea className={textareaClassName} value={archiveReason} onChange={(event) => setArchiveReason(event.target.value)} placeholder="Archive reason" />
              <Button
                variant="secondary"
                disabled={!canArchiveDocument(document.status) || archiveMutation.isPending}
                onClick={() => runAction(() => archiveMutation.mutateAsync({ reason: archiveReason || undefined, version: document.version }))}
              >
                Archive
              </Button>
            </div>
          </div>
        </PermissionGate>
      </div>
    </SectionCard>
  );
}

export function DocumentAuditTrailPanel({ events }: { events: DocumentAuditEvent[] }) {
  return (
    <SectionCard title="Audit trail" description="Insert-only audit events returned by the backend.">
      {events.length === 0 ? (
        <p className="text-sm text-muted-foreground">No audit events.</p>
      ) : (
        <div className="space-y-3">
          {events.map((event) => (
            <div key={event.id} className="rounded-md border px-3 py-2" data-testid={`audit-event-${event.id}`}>
              <div className="flex flex-wrap items-center gap-2">
                <Badge variant="outline">{humanize(event.event_type)}</Badge>
                <Badge variant="secondary">Action: {event.action}</Badge>
              </div>
              <p className="mt-2 text-sm">Actor #{event.actor_user_id}</p>
              <p className="text-xs text-muted-foreground">{formatDate(event.created_at)}</p>
            </div>
          ))}
        </div>
      )}
    </SectionCard>
  );
}

export function DocumentStatusHistoryPanel({ history }: { history: DocumentStatusHistory[] }) {
  return <DocumentLifecycleTimeline history={history} />;
}

export function DocumentCreateForm() {
  const [title, setTitle] = useState('');
  const [documentType, setDocumentType] = useState('REPORT');
  const [sourceDepartmentId, setSourceDepartmentId] = useState('');
  const [ownerUserId, setOwnerUserId] = useState('');
  const [linkedAssignmentId, setLinkedAssignmentId] = useState('');
  const [createdId, setCreatedId] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);
  const mutation = useCreateDocument();

  async function handleCreate() {
    setError(null);
    try {
      const created = await mutation.mutateAsync({
        title,
        document_type: documentType,
        source_department_id: sourceDepartmentId ? Number(sourceDepartmentId) : undefined,
        owner_user_id: ownerUserId ? Number(ownerUserId) : undefined,
        linked_assignment_id: linkedAssignmentId ? Number(linkedAssignmentId) : undefined,
      });
      setCreatedId(created.id);
      setTitle('');
    } catch (err) {
      setError(getErrorMessage(err));
    }
  }

  return (
    <SectionCard title="Create document" description="Creates a DRAFT document only.">
      <div className="grid gap-3 md:grid-cols-2">
        <div>
          <label className="mb-1 block text-xs font-medium text-muted-foreground">Title</label>
          <Input value={title} onChange={(event) => setTitle(event.target.value)} placeholder="Senate briefing note" />
        </div>
        <div>
          <label className="mb-1 block text-xs font-medium text-muted-foreground">Type</label>
          <Input value={documentType} onChange={(event) => setDocumentType(event.target.value)} placeholder="REPORT" />
        </div>
        <div>
          <label className="mb-1 block text-xs font-medium text-muted-foreground">Source department ID</label>
          <Input value={sourceDepartmentId} onChange={(event) => setSourceDepartmentId(event.target.value)} placeholder="42" />
        </div>
        <div>
          <label className="mb-1 block text-xs font-medium text-muted-foreground">Owner user ID</label>
          <Input value={ownerUserId} onChange={(event) => setOwnerUserId(event.target.value)} placeholder="7" />
        </div>
        <div>
          <label className="mb-1 block text-xs font-medium text-muted-foreground">Linked assignment ID</label>
          <Input value={linkedAssignmentId} onChange={(event) => setLinkedAssignmentId(event.target.value)} placeholder="123" />
        </div>
      </div>
      <div className="mt-4 flex items-center gap-3">
        <Button onClick={handleCreate} disabled={mutation.isPending || !title.trim() || !documentType.trim()}>
          Create document
        </Button>
        {createdId ? <Link className="text-primary hover:underline" href={`/console/documents/${createdId}`}>Open created document</Link> : null}
      </div>
      <MutationError error={error} />
    </SectionCard>
  );
}

export function DecreeRegistryTable({ decrees }: { decrees: OrderDecree[] }) {
  return (
    <div className="overflow-x-auto rounded-lg border bg-background">
      <table className="min-w-full divide-y">
        <thead className="bg-muted/30">
          <tr className="text-left text-xs uppercase tracking-wide text-muted-foreground">
            <th className="px-4 py-3">Title</th>
            <th className="px-4 py-3">Status</th>
            <th className="px-4 py-3">Registry</th>
            <th className="px-4 py-3">Effective date</th>
            <th className="px-4 py-3">Actions</th>
          </tr>
        </thead>
        <tbody className="divide-y">
          {decrees.map((decree) => (
            <tr key={decree.id} data-testid={`decree-row-${decree.id}`}>
              <td className="px-4 py-3 text-sm font-medium">{decree.title}</td>
              <td className="px-4 py-3 text-sm"><DocumentStatusBadge status={decree.status} /></td>
              <td className="px-4 py-3 text-sm"><RegistryNumberBadge registryNumber={decree.registry_number} /></td>
              <td className="px-4 py-3 text-sm">{formatDateOnly(decree.effective_date)}</td>
              <td className="px-4 py-3 text-sm">
                <Link className="text-primary hover:underline" href={`/console/documents/decrees/${decree.id}`}>Open</Link>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export function SignedMetadataNotice() {
  return (
    <div className="space-y-2">
      <InlineNotice testId="signed-metadata-only-notice">Signed metadata only.</InlineNotice>
      <InlineNotice testId="no-auto-signature-notice">No auto-signature.</InlineNotice>
      <InlineNotice testId="no-auto-approval-notice">No auto-approval.</InlineNotice>
      <InlineNotice testId="decree-registry-official-notice">Registry number is official workflow metadata.</InlineNotice>
    </div>
  );
}

export function DecreeLifecycleTimeline({ decree }: { decree: OrderDecree }) {
  return (
    <SectionCard title="Lifecycle state" description="Current decree/order lifecycle state.">
      <MetadataGrid
        items={[
          { label: 'Status', value: <DocumentStatusBadge status={decree.status} /> },
          { label: 'Version', value: decree.version },
          { label: 'Effective date', value: formatDateOnly(decree.effective_date) },
          { label: 'Signed by', value: decree.signed_by_user_id ?? 'Not recorded' },
          { label: 'Signed at', value: formatDate(decree.signed_at) },
          { label: 'Linked document', value: decree.linked_document_id ?? 'Not linked' },
        ]}
      />
    </SectionCard>
  );
}

export function DecreeDetailPanel({ decree }: { decree: OrderDecree }) {
  const [note, setNote] = useState('');
  const [comment, setComment] = useState('');
  const [signedBy, setSignedBy] = useState('');
  const [signedAt, setSignedAt] = useState('');
  const [registryNumber, setRegistryNumber] = useState('');
  const [archiveReason, setArchiveReason] = useState('');
  const [error, setError] = useState<string | null>(null);
  const legalReviewMutation = useDecreeLegalReview(decree.id);
  const approveMutation = useApproveDecreeSigning(decree.id);
  const signedMutation = useDecreeSignedMetadata(decree.id);
  const registerMutation = useRegisterDecree(decree.id);
  const archiveMutation = useArchiveDecree(decree.id);

  async function runAction(action: () => Promise<unknown>) {
    setError(null);
    try {
      await action();
    } catch (err) {
      setError(getErrorMessage(err));
    }
  }

  return (
    <SectionCard title={decree.title} description="Decree/order detail and action surface">
      <SignedMetadataNotice />
      <div className="mt-4">
        <MetadataGrid
          items={[
            { label: 'Registry number', value: decree.registry_number ?? 'Not assigned' },
            { label: 'Registry date', value: formatDate(decree.registry_date) },
            { label: 'Linked assignment', value: decree.linked_assignment_id ?? 'Not linked' },
            { label: 'Created at', value: formatDate(decree.created_at) },
          ]}
        />
      </div>
      <MutationError error={error} />
      <div className="mt-4 grid gap-4 lg:grid-cols-2">
        <PermissionGate permission={DOCUMENT_WORKFLOW_PERMISSIONS.DECREES_LEGAL_REVIEW}>
          <div className="rounded-md border p-3">
            <p className="font-medium">Submit legal review</p>
            <textarea className={`${textareaClassName} mt-2`} value={note} onChange={(event) => setNote(event.target.value)} placeholder="Legal review note" />
            <Button className="mt-3" disabled={!canStartDecreeLegalReview(decree.status) || legalReviewMutation.isPending} onClick={() => runAction(() => legalReviewMutation.mutateAsync({ note, version: decree.version }))}>
              Submit legal review
            </Button>
          </div>
        </PermissionGate>

        <PermissionGate permission={DOCUMENT_WORKFLOW_PERMISSIONS.DECREES_APPROVE_SIGNING}>
          <div className="rounded-md border p-3">
            <p className="font-medium">Approve for signing</p>
            <textarea className={`${textareaClassName} mt-2`} value={comment} onChange={(event) => setComment(event.target.value)} placeholder="Approval comment" />
            <Button className="mt-3" disabled={!canApproveDecreeSigning(decree.status) || approveMutation.isPending} onClick={() => runAction(() => approveMutation.mutateAsync({ comment, version: decree.version }))}>
              Approve for signing
            </Button>
          </div>
        </PermissionGate>

        <PermissionGate permission={DOCUMENT_WORKFLOW_PERMISSIONS.DECREES_SIGNED_METADATA_RECORD}>
          <div className="rounded-md border p-3">
            <p className="font-medium">Record signed metadata</p>
            <Input className="mt-2" value={signedBy} onChange={(event) => setSignedBy(event.target.value)} placeholder="Signed by user ID" />
            <Input className="mt-2" value={signedAt} onChange={(event) => setSignedAt(event.target.value)} placeholder="2026-05-21T12:00:00Z" />
            <Button className="mt-3" disabled={!canRecordDecreeSignedMetadata(decree.status) || signedMutation.isPending || !signedBy.trim()} onClick={() => runAction(() => signedMutation.mutateAsync({ signed_by_user_id: Number(signedBy), signed_at: signedAt || undefined, version: decree.version }))}>
              Record signed metadata
            </Button>
          </div>
        </PermissionGate>

        <PermissionGate permission={DOCUMENT_WORKFLOW_PERMISSIONS.DECREES_REGISTER}>
          <div className="rounded-md border p-3">
            <p className="font-medium">Register decree</p>
            <Input className="mt-2" value={registryNumber} onChange={(event) => setRegistryNumber(event.target.value)} placeholder="DEC-2026-001" />
            <Button className="mt-3" disabled={!canRegisterDecree(decree.status) || registerMutation.isPending || !registryNumber.trim()} onClick={() => runAction(() => registerMutation.mutateAsync({ registry_number: registryNumber.trim(), version: decree.version }))}>
              Register decree
            </Button>
          </div>
        </PermissionGate>

        <PermissionGate permission={DOCUMENT_WORKFLOW_PERMISSIONS.DECREES_ARCHIVE}>
          <div className="rounded-md border p-3">
            <p className="font-medium">Archive decree</p>
            <textarea className={`${textareaClassName} mt-2`} value={archiveReason} onChange={(event) => setArchiveReason(event.target.value)} placeholder="Archive reason" />
            <Button className="mt-3" variant="secondary" disabled={!canArchiveDecree(decree.status) || archiveMutation.isPending} onClick={() => runAction(() => archiveMutation.mutateAsync({ reason: archiveReason || undefined, version: decree.version }))}>
              Archive decree
            </Button>
          </div>
        </PermissionGate>
      </div>
    </SectionCard>
  );
}

export function DecreeCreateForm() {
  const [title, setTitle] = useState('');
  const [decreeType, setDecreeType] = useState('ORDER');
  const [effectiveDate, setEffectiveDate] = useState('');
  const [linkedDocumentId, setLinkedDocumentId] = useState('');
  const [createdId, setCreatedId] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);
  const mutation = useCreateDecree();

  async function handleCreate() {
    setError(null);
    try {
      const created = await mutation.mutateAsync({
        title,
        decree_type: decreeType,
        effective_date: effectiveDate || undefined,
        linked_document_id: linkedDocumentId ? Number(linkedDocumentId) : undefined,
      });
      setCreatedId(created.id);
      setTitle('');
    } catch (err) {
      setError(getErrorMessage(err));
    }
  }

  return (
    <SectionCard title="Create decree or order" description="Creates a DRAFT_ORDER item only.">
      <SignedMetadataNotice />
      <div className="mt-4 grid gap-3 md:grid-cols-2">
        <Input value={title} onChange={(event) => setTitle(event.target.value)} placeholder="Appointment order" />
        <Input value={decreeType} onChange={(event) => setDecreeType(event.target.value)} placeholder="ORDER" />
        <Input value={effectiveDate} onChange={(event) => setEffectiveDate(event.target.value)} placeholder="2026-05-21" />
        <Input value={linkedDocumentId} onChange={(event) => setLinkedDocumentId(event.target.value)} placeholder="Linked document ID" />
      </div>
      <div className="mt-4 flex items-center gap-3">
        <Button onClick={handleCreate} disabled={mutation.isPending || !title.trim() || !decreeType.trim()}>
          Create decree
        </Button>
        {createdId ? <Link className="text-primary hover:underline" href={`/console/documents/decrees/${createdId}`}>Open created decree</Link> : null}
      </div>
      <MutationError error={error} />
    </SectionCard>
  );
}

export function CorrespondenceRouteForm({ item }: { item: CorrespondenceItem }) {
  const [registryNumber, setRegistryNumber] = useState('');
  const [toUserId, setToUserId] = useState('');
  const [toRole, setToRole] = useState('');
  const [routeComment, setRouteComment] = useState('');
  const [archiveReason, setArchiveReason] = useState('');
  const [error, setError] = useState<string | null>(null);
  const registerMutation = useRegisterCorrespondence(item.id);
  const routeMutation = useRouteCorrespondence(item.id);
  const sentMutation = useOutgoingSentMetadata(item.id);
  const archiveMutation = useArchiveCorrespondence(item.id);

  async function runAction(action: () => Promise<unknown>) {
    setError(null);
    try {
      await action();
    } catch (err) {
      setError(getErrorMessage(err));
    }
  }

  return (
    <SectionCard title={`Actions for #${item.id}`} description="Correspondence actions are metadata-only and backend-authoritative.">
      <div className="space-y-2">
        <InlineNotice testId="sent-metadata-only-notice">Sent metadata only.</InlineNotice>
        <InlineNotice testId="delivered-metadata-only-notice">Delivered metadata only.</InlineNotice>
        <InlineNotice testId="no-provider-delivery-notice">No provider delivery integration.</InlineNotice>
        <InlineNotice testId="no-fake-delivery-notice">No fake sent/delivered status.</InlineNotice>
      </div>
      <MutationError error={error} />
      <div className="mt-4 grid gap-4 lg:grid-cols-2">
        <PermissionGate permission={DOCUMENT_WORKFLOW_PERMISSIONS.CORRESPONDENCE_REGISTER}>
          <div className="rounded-md border p-3">
            <p className="font-medium">Register correspondence</p>
            <Input className="mt-2" value={registryNumber} onChange={(event) => setRegistryNumber(event.target.value)} placeholder="CORR-2026-001" />
            <Button className="mt-3" disabled={registerMutation.isPending || !registryNumber.trim()} onClick={() => runAction(() => registerMutation.mutateAsync({ registry_number: registryNumber.trim() }))}>
              Register
            </Button>
          </div>
        </PermissionGate>

        <PermissionGate permission={DOCUMENT_WORKFLOW_PERMISSIONS.CORRESPONDENCE_ROUTE}>
          <div className="rounded-md border p-3">
            <p className="font-medium">Route correspondence</p>
            <Input className="mt-2" value={toUserId} onChange={(event) => setToUserId(event.target.value)} placeholder="To user ID" />
            <Input className="mt-2" value={toRole} onChange={(event) => setToRole(event.target.value)} placeholder="To role" />
            <textarea className={`${textareaClassName} mt-2`} value={routeComment} onChange={(event) => setRouteComment(event.target.value)} placeholder="Route comment" />
            <Button className="mt-3" disabled={routeMutation.isPending || (!toUserId.trim() && !toRole.trim())} onClick={() => runAction(() => routeMutation.mutateAsync({ to_user_id: toUserId ? Number(toUserId) : undefined, to_role: toRole || undefined, route_comment: routeComment || undefined }))}>
              Route
            </Button>
          </div>
        </PermissionGate>

        <PermissionGate permission={DOCUMENT_WORKFLOW_PERMISSIONS.CORRESPONDENCE_SENT_METADATA_RECORD}>
          <div className="rounded-md border p-3">
            <p className="font-medium">Record sent metadata</p>
            <Button className="mt-3" disabled={!canRecordOutgoingSentMetadata(item.direction, item.status) || sentMutation.isPending} onClick={() => runAction(() => sentMutation.mutateAsync())}>
              Record sent metadata
            </Button>
          </div>
        </PermissionGate>

        <PermissionGate permission={DOCUMENT_WORKFLOW_PERMISSIONS.CORRESPONDENCE_ARCHIVE}>
          <div className="rounded-md border p-3">
            <p className="font-medium">Archive correspondence</p>
            <textarea className={`${textareaClassName} mt-2`} value={archiveReason} onChange={(event) => setArchiveReason(event.target.value)} placeholder="Archive reason" />
            <Button className="mt-3" variant="secondary" disabled={archiveMutation.isPending} onClick={() => runAction(() => archiveMutation.mutateAsync({ reason: archiveReason || undefined }))}>
              Archive
            </Button>
          </div>
        </PermissionGate>
      </div>
    </SectionCard>
  );
}

export function CorrespondenceRoutePanel({ item }: { item: CorrespondenceItem | null }) {
  if (!item) {
    return (
      <SectionCard title="Correspondence detail" description="Select a correspondence item from the registry to act on it.">
        <p className="text-sm text-muted-foreground">No correspondence item selected.</p>
      </SectionCard>
    );
  }
  return <CorrespondenceRouteForm item={item} />;
}

export function CorrespondenceRegistryTable({
  items,
  selectedId,
  onSelect,
}: {
  items: CorrespondenceItem[];
  selectedId: number | null;
  onSelect: (id: number) => void;
}) {
  return (
    <div className="overflow-x-auto rounded-lg border bg-background">
      <table className="min-w-full divide-y">
        <thead className="bg-muted/30">
          <tr className="text-left text-xs uppercase tracking-wide text-muted-foreground">
            <th className="px-4 py-3">Subject</th>
            <th className="px-4 py-3">Direction</th>
            <th className="px-4 py-3">Status</th>
            <th className="px-4 py-3">Registry</th>
            <th className="px-4 py-3">Party</th>
            <th className="px-4 py-3">Select</th>
          </tr>
        </thead>
        <tbody className="divide-y">
          {items.map((item) => (
            <tr key={item.id} className={selectedId === item.id ? 'bg-muted/20' : undefined}>
              <td className="px-4 py-3 text-sm font-medium">{item.subject}</td>
              <td className="px-4 py-3 text-sm"><Badge variant="outline">{humanize(item.direction)}</Badge></td>
              <td className="px-4 py-3 text-sm"><DocumentStatusBadge status={item.status} /></td>
              <td className="px-4 py-3 text-sm"><RegistryNumberBadge registryNumber={item.registry_number} /></td>
              <td className="px-4 py-3 text-sm">{item.direction === CorrespondenceDirection.INCOMING ? item.sender_name || item.sender_organization || 'Unknown sender' : item.recipient_name || item.recipient_organization || 'Unknown recipient'}</td>
              <td className="px-4 py-3 text-sm">
                <Button variant="outline" size="sm" onClick={() => onSelect(item.id)}>
                  {selectedId === item.id ? 'Selected' : 'Select'}
                </Button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function CorrespondenceCreateBase({
  direction,
  onSubmit,
}: {
  direction: 'incoming' | 'outgoing';
  onSubmit: (payload: Record<string, unknown>) => Promise<number>;
}) {
  const [subject, setSubject] = useState('');
  const [correspondenceType, setCorrespondenceType] = useState('LETTER');
  const [partyName, setPartyName] = useState('');
  const [organization, setOrganization] = useState('');
  const [receivedAt, setReceivedAt] = useState('');
  const [linkedDocumentId, setLinkedDocumentId] = useState('');
  const [createdId, setCreatedId] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function handleCreate() {
    setError(null);
    try {
      const id = await onSubmit({
        subject,
        correspondence_type: correspondenceType,
        ...(direction === 'incoming'
          ? {
              sender_name: partyName || undefined,
              sender_organization: organization || undefined,
              received_at: receivedAt || undefined,
            }
          : {
              recipient_name: partyName || undefined,
              recipient_organization: organization || undefined,
            }),
        linked_document_id: linkedDocumentId ? Number(linkedDocumentId) : undefined,
      });
      setCreatedId(id);
      setSubject('');
    } catch (err) {
      setError(getErrorMessage(err));
    }
  }

  return (
    <SectionCard title={`Create ${direction} correspondence`} description="No fake sent/delivered status is generated by the frontend.">
      <div className="space-y-2">
        <InlineNotice>{direction === 'incoming' ? 'Received metadata only.' : 'Sent metadata only.'}</InlineNotice>
        <InlineNotice>No provider delivery integration.</InlineNotice>
      </div>
      <div className="mt-4 grid gap-3 md:grid-cols-2">
        <Input value={subject} onChange={(event) => setSubject(event.target.value)} placeholder="Subject" />
        <Input value={correspondenceType} onChange={(event) => setCorrespondenceType(event.target.value)} placeholder="LETTER" />
        <Input value={partyName} onChange={(event) => setPartyName(event.target.value)} placeholder={direction === 'incoming' ? 'Sender name' : 'Recipient name'} />
        <Input value={organization} onChange={(event) => setOrganization(event.target.value)} placeholder={direction === 'incoming' ? 'Sender organization' : 'Recipient organization'} />
        {direction === 'incoming' ? <Input value={receivedAt} onChange={(event) => setReceivedAt(event.target.value)} placeholder="2026-05-21T09:00:00Z" /> : null}
        <Input value={linkedDocumentId} onChange={(event) => setLinkedDocumentId(event.target.value)} placeholder="Linked document ID" />
      </div>
      <div className="mt-4 flex items-center gap-3">
        <Button onClick={handleCreate} disabled={!subject.trim()}>
          Create correspondence
        </Button>
        {createdId ? <Badge variant="success">Created #{createdId}</Badge> : null}
      </div>
      <MutationError error={error} />
    </SectionCard>
  );
}

export function IncomingCorrespondenceForm() {
  const mutation = useCreateIncomingCorrespondence();
  return (
    <CorrespondenceCreateBase
      direction="incoming"
      onSubmit={async (payload) => {
        const created = await mutation.mutateAsync(payload as never);
        return created.id;
      }}
    />
  );
}

export function OutgoingCorrespondenceForm() {
  const mutation = useCreateOutgoingCorrespondence();
  return (
    <CorrespondenceCreateBase
      direction="outgoing"
      onSubmit={async (payload) => {
        const created = await mutation.mutateAsync(payload as never);
        return created.id;
      }}
    />
  );
}

function KpiCard({
  label,
  value,
  description,
  testId,
}: {
  label: string;
  value?: number | null;
  description?: string;
  testId: string;
}) {
  const unavailable = value === undefined || value === null;
  return (
    <div className="rounded-lg border bg-background p-4" data-testid={testId}>
      <p className="text-xs uppercase tracking-wide text-muted-foreground">{label}</p>
      <p className="mt-2 text-2xl font-semibold">{unavailable ? 'Unavailable' : value}</p>
      {description ? <p className="mt-1 text-sm text-muted-foreground">{description}</p> : null}
    </div>
  );
}

export function DocumentWorkflowDashboardCards({ dashboard }: { dashboard: DashboardSummary }) {
  return (
    <div className="space-y-4">
      <InlineNotice testId="computed-from-documents-label">Computed from documents.</InlineNotice>
      {dashboard.incomplete_data ? (
        <InlineNotice testId="incomplete-dashboard-notice">Incomplete dashboard data reported by backend.</InlineNotice>
      ) : null}
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-5">
        <KpiCard label="Total documents" value={dashboard.total_documents} description="All documents in tenant scope" testId="kpi-total-documents" />
        <KpiCard label="Registered documents" value={dashboard.registered_documents} testId="kpi-registered-documents" />
        <KpiCard label="Under review" value={dashboard.under_review_count} testId="kpi-under-review" />
        <KpiCard label="Returned for revision" value={dashboard.returned_for_revision_count} testId="kpi-returned-revision" />
        <KpiCard label="Approved and signed" value={dashboard.approved_count + dashboard.signed_count} testId="kpi-approved-signed" />
        <KpiCard label="Incoming correspondence" value={dashboard.incoming_correspondence_count} testId="kpi-incoming-correspondence" />
        <KpiCard label="Outgoing correspondence" value={dashboard.outgoing_correspondence_count} testId="kpi-outgoing-correspondence" />
        <KpiCard label="Decrees pending signature" value={dashboard.decrees_pending_signature} testId="kpi-decrees-pending-signature" />
        <KpiCard label="Assignment-linked documents" value={dashboard.documents_linked_to_assignments} testId="kpi-documents-linked-assignment" />
        <KpiCard label="Average review cycle" value={dashboard.average_review_cycle_days} description={formatUnavailableMetric(dashboard.average_review_cycle_days)} testId="kpi-average-review-cycle" />
      </div>
    </div>
  );
}

export function ArchivePanel({ records }: { records: ArchiveRecord[] }) {
  return (
    <SectionCard title="Archive records" description="Archived records only; no hard delete action exists.">
      {records.length === 0 ? (
        <p className="text-sm text-muted-foreground">No archived records were returned for the current filters.</p>
      ) : (
        <div className="space-y-3">
          {records.map((record) => (
            <div key={`${record.kind}-${record.id}`} className="rounded-md border px-3 py-2" data-testid={`archive-record-${record.kind}-${record.id}`}>
              <div className="flex flex-wrap items-center gap-2">
                <Badge variant="secondary">{humanize(record.kind)}</Badge>
                <DocumentStatusBadge status={record.status} />
                <RegistryNumberBadge registryNumber={record.registry_number} />
              </div>
              <p className="mt-2 font-medium">{record.title}</p>
              <p className="text-xs text-muted-foreground">Archived at {formatDate(record.archived_at)}</p>
            </div>
          ))}
        </div>
      )}
    </SectionCard>
  );
}

export function DocumentRegistryPage() {
  const [status, setStatus] = useState('');
  const [documentType, setDocumentType] = useState('');
  const { data, isLoading, error, refetch } = useDocuments({ status: status || undefined, document_type: documentType || undefined, page_size: 50 });

  if (isLoading) return <LoadingState message="Loading document registry..." />;
  if (error) return <ErrorState error={error} onRetry={refetch} title="Failed to load documents" />;

  return (
    <RequirePermission permission={DOCUMENT_WORKFLOW_PERMISSIONS.DOCUMENTS_READ}>
      <div className="space-y-6">
        <PageHeader
          title="Document registry"
          description="Document / decree / correspondence backend data only. No hard delete."
          icon={FileText}
          actions={
            <PermissionGate permission={DOCUMENT_WORKFLOW_PERMISSIONS.DOCUMENTS_CREATE}>
              <Button asChild><Link href="/console/documents/new">New document</Link></Button>
            </PermissionGate>
          }
        />
        <DocumentFiltersBar status={status} setStatus={setStatus} documentType={documentType} setDocumentType={setDocumentType} />
        <InlineNotice testId="document-registry-no-hard-delete">No hard delete action is available.</InlineNotice>
        <DocumentRegistryTable documents={data?.items ?? []} />
      </div>
    </RequirePermission>
  );
}

export function DocumentCreatePage() {
  return (
    <RequirePermission permission={DOCUMENT_WORKFLOW_PERMISSIONS.DOCUMENTS_CREATE}>
      <div className="space-y-6">
        <PageHeader title="New document" description="Create a draft document record." icon={FileText} />
        <DocumentCreateForm />
      </div>
    </RequirePermission>
  );
}

export function DocumentDetailPage({ id }: { id: string }) {
  const { data, isLoading, error, refetch } = useDocument(id);

  if (isLoading) return <LoadingState message="Loading document detail..." />;
  if (error) return <ErrorState error={error} onRetry={refetch} title="Failed to load document" />;
  if (!data) return <ErrorState title="Document not found" message="The document detail response was empty." />;

  return (
    <RequirePermission permission={DOCUMENT_WORKFLOW_PERMISSIONS.DOCUMENTS_READ}>
      <div className="space-y-6">
        <PageHeader
          title="Document detail"
          description="Lifecycle, reviews, versions, and assignment links."
          icon={FileText}
          actions={<Button asChild variant="outline"><Link href={`/console/documents/${id}/audit`}>Open audit trail</Link></Button>}
        />
        <DocumentDetailHeader document={data} />
        <DocumentActionsBar document={data} />
        <DocumentVersionTimeline versions={data.versions} />
        <DocumentReviewPanel reviews={data.reviews} />
        <DocumentAssignmentLinkPanel document={data} />
      </div>
    </RequirePermission>
  );
}

export function DocumentAuditPage({ id }: { id: string }) {
  const detail = useDocument(id);
  const audit = useDocumentAudit(id);
  const history = useDocumentHistory(id);

  if (detail.isLoading || audit.isLoading || history.isLoading) {
    return <LoadingState message="Loading document audit and history..." />;
  }
  if (detail.error || audit.error || history.error) {
    return <ErrorState error={detail.error || audit.error || history.error} title="Failed to load audit data" onRetry={() => { detail.refetch(); audit.refetch(); history.refetch(); }} />;
  }

  return (
    <RequirePermission permission={DOCUMENT_WORKFLOW_PERMISSIONS.DOCUMENTS_AUDIT_READ}>
      <div className="space-y-6">
        <PageHeader title="Document audit trail" description="Audit events and status history" icon={Archive} actions={<Button asChild variant="outline"><Link href={`/console/documents/${id}`}>Back to detail</Link></Button>} />
        {detail.data ? <DocumentDetailHeader document={detail.data} /> : null}
        <DocumentAuditTrailPanel events={audit.data ?? []} />
        <DocumentStatusHistoryPanel history={history.data ?? []} />
      </div>
    </RequirePermission>
  );
}

export function DecreeRegistryPage() {
  const [status, setStatus] = useState('');
  const [decreeType, setDecreeType] = useState('');
  const { data, isLoading, error, refetch } = useDecrees({ status: status || undefined, decree_type: decreeType || undefined, page_size: 50 });

  if (isLoading) return <LoadingState message="Loading decrees and orders..." />;
  if (error) return <ErrorState error={error} title="Failed to load decrees" onRetry={refetch} />;

  return (
    <RequirePermission permission={DOCUMENT_WORKFLOW_PERMISSIONS.DECREES_READ}>
      <div className="space-y-6">
        <PageHeader title="Decree registry" description="Decrees and orders with signing metadata only." icon={Scale} actions={<PermissionGate permission={DOCUMENT_WORKFLOW_PERMISSIONS.DECREES_CREATE}><Button asChild><Link href="/console/documents/decrees/new">New decree</Link></Button></PermissionGate>} />
        <div className="flex flex-wrap gap-3 rounded-lg border bg-background p-4">
          <Input value={status} onChange={(event) => setStatus(event.target.value)} placeholder="REGISTERED" />
          <Input value={decreeType} onChange={(event) => setDecreeType(event.target.value)} placeholder="ORDER" />
        </div>
        <DecreeRegistryTable decrees={data?.items ?? []} />
      </div>
    </RequirePermission>
  );
}

export function DecreeCreatePage() {
  return (
    <RequirePermission permission={DOCUMENT_WORKFLOW_PERMISSIONS.DECREES_CREATE}>
      <div className="space-y-6">
        <PageHeader title="New decree" description="Create a decree/order draft." icon={Scale} />
        <DecreeCreateForm />
      </div>
    </RequirePermission>
  );
}

export function DecreeDetailPage({ id }: { id: string }) {
  const { data, isLoading, error, refetch } = useDecree(id);

  if (isLoading) return <LoadingState message="Loading decree detail..." />;
  if (error) return <ErrorState error={error} title="Failed to load decree" onRetry={refetch} />;
  if (!data) return <ErrorState title="Decree not found" message="The decree detail response was empty." />;

  return (
    <RequirePermission permission={DOCUMENT_WORKFLOW_PERMISSIONS.DECREES_READ}>
      <div className="space-y-6">
        <PageHeader title="Decree detail" description="Legal review, signing metadata, register, and archive." icon={Scale} />
        <DecreeLifecycleTimeline decree={data} />
        <DecreeDetailPanel decree={data} />
      </div>
    </RequirePermission>
  );
}

export function CorrespondenceRegistryPage() {
  const [direction, setDirection] = useState('');
  const [status, setStatus] = useState('');
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const { data, isLoading, error, refetch } = useCorrespondence({ direction: direction || undefined, status: status || undefined, page_size: 50 });
  const selected = data?.items.find((item) => item.id === selectedId) ?? null;

  if (isLoading) return <LoadingState message="Loading correspondence registry..." />;
  if (error) return <ErrorState error={error} title="Failed to load correspondence" onRetry={refetch} />;

  return (
    <RequirePermission permission={DOCUMENT_WORKFLOW_PERMISSIONS.CORRESPONDENCE_READ}>
      <div className="space-y-6">
        <PageHeader
          title="Correspondence registry"
          description="Incoming and outgoing correspondence with metadata-only delivery states."
          icon={Mail}
          actions={
            <div className="flex gap-2">
              <PermissionGate permission={DOCUMENT_WORKFLOW_PERMISSIONS.CORRESPONDENCE_CREATE}>
                <Button asChild variant="outline"><Link href="/console/documents/correspondence/incoming/new">New incoming</Link></Button>
              </PermissionGate>
              <PermissionGate permission={DOCUMENT_WORKFLOW_PERMISSIONS.CORRESPONDENCE_CREATE}>
                <Button asChild><Link href="/console/documents/correspondence/outgoing/new">New outgoing</Link></Button>
              </PermissionGate>
            </div>
          }
        />
        <div className="flex flex-wrap gap-3 rounded-lg border bg-background p-4">
          <Input value={direction} onChange={(event) => setDirection(event.target.value)} placeholder="INCOMING or OUTGOING" />
          <Input value={status} onChange={(event) => setStatus(event.target.value)} placeholder="REGISTERED" />
        </div>
        <CorrespondenceRegistryTable items={data?.items ?? []} selectedId={selectedId} onSelect={setSelectedId} />
        <CorrespondenceRoutePanel item={selected} />
      </div>
    </RequirePermission>
  );
}

export function IncomingCorrespondenceCreatePage() {
  return (
    <RequirePermission permission={DOCUMENT_WORKFLOW_PERMISSIONS.CORRESPONDENCE_CREATE}>
      <div className="space-y-6">
        <PageHeader title="New incoming correspondence" description="Create an incoming correspondence record." icon={Mail} />
        <IncomingCorrespondenceForm />
      </div>
    </RequirePermission>
  );
}

export function OutgoingCorrespondenceCreatePage() {
  return (
    <RequirePermission permission={DOCUMENT_WORKFLOW_PERMISSIONS.CORRESPONDENCE_CREATE}>
      <div className="space-y-6">
        <PageHeader title="New outgoing correspondence" description="Create an outgoing correspondence record." icon={Mail} />
        <OutgoingCorrespondenceForm />
      </div>
    </RequirePermission>
  );
}

export function DocumentWorkflowDashboardPage() {
  const { data, isLoading, error, refetch } = useDocumentWorkflowDashboard();

  if (isLoading) return <LoadingState message="Loading document workflow dashboard..." />;
  if (error) {
    const message = getErrorMessage(error);
    if (message.includes('fake_metrics') || message.includes('data source mismatch')) {
      return <DataQualityError reason={message} />;
    }
    return <ErrorState error={error} title="Failed to load dashboard" onRetry={refetch} />;
  }
  if (!data) return <ErrorState title="Dashboard unavailable" message="No dashboard payload was returned." />;

  return (
    <RequirePermission permission={DOCUMENT_WORKFLOW_PERMISSIONS.DASHBOARD_READ}>
      <div className="space-y-6">
        <PageHeader title="Document workflow dashboard" description="Computed from documents only." icon={FileText} />
        <DocumentWorkflowDashboardCards dashboard={data} />
      </div>
    </RequirePermission>
  );
}

export function ArchivePage() {
  const documents = useDocuments({ status: 'ARCHIVED', page_size: 100 });
  const decrees = useDecrees({ status: 'ARCHIVED', page_size: 100 });
  const correspondence = useCorrespondence({ status: 'ARCHIVED', page_size: 100 });

  if (documents.isLoading || decrees.isLoading || correspondence.isLoading) {
    return <LoadingState message="Loading archive records..." />;
  }
  if (documents.error || decrees.error || correspondence.error) {
    return <ErrorState error={documents.error || decrees.error || correspondence.error} title="Failed to load archive records" onRetry={() => { documents.refetch(); decrees.refetch(); correspondence.refetch(); }} />;
  }

  const records = useMemo<ArchiveRecord[]>(() => {
    const documentRecords = (documents.data?.items ?? [])
      .filter((item) => isArchiveRecord(item.archived_at))
      .map((item) => ({ kind: 'document' as const, id: item.id, title: item.title, status: item.status, archived_at: item.archived_at, registry_number: item.registry_number }));
    const decreeRecords = (decrees.data?.items ?? [])
      .filter((item) => isArchiveRecord(item.archived_at))
      .map((item) => ({ kind: 'decree' as const, id: item.id, title: item.title, status: item.status, archived_at: item.archived_at, registry_number: item.registry_number }));
    const correspondenceRecords = (correspondence.data?.items ?? [])
      .filter((item) => isArchiveRecord(item.archived_at))
      .map((item) => ({ kind: 'correspondence' as const, id: item.id, title: item.subject, status: item.status, archived_at: item.archived_at, registry_number: item.registry_number }));
    return [...documentRecords, ...decreeRecords, ...correspondenceRecords];
  }, [correspondence.data?.items, decrees.data?.items, documents.data?.items]);

  return (
    <RequirePermission permission={DOCUMENT_WORKFLOW_PERMISSIONS.DOCUMENTS_READ}>
      <div className="space-y-6">
        <PageHeader title="Archive" description="Archived document workflow records only." icon={Archive} />
        <ArchivePanel records={records} />
      </div>
    </RequirePermission>
  );
}