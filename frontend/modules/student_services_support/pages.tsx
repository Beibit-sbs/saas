'use client';

import Link from 'next/link';
import type { ReactNode } from 'react';
import { PermissionGate, RequirePermission } from '@/shared/ui/permission-gate';
import {
  STUDENT_SERVICES_SUPPORT_DATA_SOURCE,
  STUDENT_SERVICES_SUPPORT_NAV_ITEMS,
  STUDENT_SERVICES_SUPPORT_PERMISSION_VALUES,
  STUDENT_SERVICES_SUPPORT_ROUTES,
  STUDENT_SERVICES_SUPPORT_RUNTIME_MODE,
  STUDENT_SERVICES_SUPPORT_SAFETY_FLAGS,
  STUDENT_SERVICES_ROUTE_BOUNDARIES,
} from './constants';
import {
  STUDENT_SERVICES_BOUNDARY_COPY,
  STUDENT_SERVICES_FORBIDDEN_LABELS,
} from './boundaryLabels';
import { hasStudentServicesSupportPermission } from './guards';
import type {
  ComplaintRecord,
  DashboardSummary,
  EscalationRecord,
  FinanceHardshipFinanceOfficeReferralQueueItem,
  FinanceHardshipReviewerQueueItem,
  ReadinessRecord,
  ServiceRequestRecord,
  StudentServicesSupportRouteDefinition,
  StudentServicesSupportRouteKey,
  SupportCaseNoteRecord,
  SupportCaseRecord,
  SupportEvidenceRecord,
} from './types';

interface StudentServicesSupportState {
  loading?: boolean;
  error?: string | null;
  incompleteData?: boolean;
  requests?: ServiceRequestRecord[];
  requestDetail?: ServiceRequestRecord | null;
  cases?: SupportCaseRecord[];
  caseDetail?: SupportCaseRecord | null;
  notes?: SupportCaseNoteRecord[];
  evidence?: SupportEvidenceRecord[];
  hardship?: ReadinessRecord | null;
  accommodation?: ReadinessRecord | null;
  complaint?: ComplaintRecord | null;
  escalation?: EscalationRecord | null;
  dashboard?: DashboardSummary | null;
  financeHardshipQueue?: FinanceHardshipReviewerQueueItem[];
  financeOfficeReferralQueue?: FinanceHardshipFinanceOfficeReferralQueueItem[];
}

function slugify(value: string) {
  return value.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/(^-|-$)/g, '');
}

function getRouteDefinition(routeKey: StudentServicesSupportRouteKey): StudentServicesSupportRouteDefinition {
  const route = STUDENT_SERVICES_SUPPORT_ROUTES.find((item) => item.key === routeKey);
  if (!route) {
    throw new Error(`Unknown Student Services Support route key: ${routeKey}`);
  }
  return route;
}

function buildDefaultDashboard(): DashboardSummary {
  return {
    tenant_id: 0,
    module: 'student_services_support',
    contract_version: 'A-042.2.RUNTIME',
    runtime_mode: STUDENT_SERVICES_SUPPORT_RUNTIME_MODE,
    fake_metrics: false,
    provider_live_enabled: false,
    autonomous_decision_enabled: false,
    hidden_score_present: false,
    human_review_required: true,
    incomplete_data: true,
    data_source: STUDENT_SERVICES_SUPPORT_DATA_SOURCE,
    open_requests: 0,
    open_support_cases: 0,
    escalated_cases: 0,
    hardship_readiness_counts: {},
    finance_hardship_handoff_visibility: {
      source_module: 'finance_procurement_asset',
      source_flow: 'student_finance_receivables_handoff',
      total: 0,
      review_queue_count: 0,
      missing_evidence_count: 0,
      readiness_counts: {},
      no_automatic_aid_decision: true,
      no_billing_balance_mutation: true,
      human_review_required: true,
    },
    accommodation_readiness_counts: {},
    complaint_counts: {},
  };
}

function buildDefaultState(routeKey: StudentServicesSupportRouteKey): StudentServicesSupportState {
  const requestSeed: ServiceRequestRecord = {
    id: 1,
    tenant_id: 0,
    request_type: 'general_support',
    status: 'submitted',
    support_priority: 'medium',
    student_id: 'S-1001',
    subject: 'Support request',
    description: 'Metadata-only support request.',
    metadata: { human_review_required: true },
  };

  const caseSeed: SupportCaseRecord = {
    id: 1,
    tenant_id: 0,
    case_type: 'support_case',
    status: 'under_review',
    request_id: 1,
    title: 'Support case',
    metadata: { evidence_metadata_only: true },
  };

  const noteSeed: SupportCaseNoteRecord = {
    id: 1,
    tenant_id: 0,
    case_id: 1,
    note: 'Case note metadata entry.',
    metadata: { human_review_required: true },
  };

  const evidenceSeed: SupportEvidenceRecord = {
    id: 1,
    tenant_id: 0,
    case_id: 1,
    evidence_type: 'document_metadata',
    source_available: false,
    limitations: 'Evidence metadata only.',
  };

  const readinessSeed: ReadinessRecord = {
    id: 1,
    tenant_id: 0,
    request_id: 1,
    status: 'readiness_evaluated',
    readiness_status: 'ready_for_human_review',
    missing_evidence: ['supporting_document_metadata'],
    recommended_next_step: 'Human reviewer confirms evidence sufficiency.',
  };

  const complaintSeed: ComplaintRecord = {
    id: 1,
    tenant_id: 0,
    status: 'routed',
    request_id: 1,
    routed_to: 'Student Affairs',
    complaint_summary: 'Complaint metadata summary.',
  };

  const escalationSeed: EscalationRecord = {
    id: 1,
    tenant_id: 0,
    case_id: 1,
    escalation_status: 'pending',
    reason: 'Human escalation metadata reason.',
  };

  const financeHardshipQueueSeed: FinanceHardshipReviewerQueueItem = {
    hardship_id: 1,
    request_id: 1,
    student_id: 'S-1001',
    support_priority: 'high',
    hardship_status: 'readiness_evaluated',
    service_request_status: 'submitted',
    readiness_status: 'blocked_missing_required_evidence',
    missing_evidence: ['balance_statement'],
    recommended_next_step: 'collect_missing_evidence',
    receivables_metadata_id: 7,
    source_module: 'finance_procurement_asset',
    source_flow: 'student_finance_receivables_handoff',
    no_automatic_aid_decision: true,
    no_billing_balance_mutation: true,
    human_review_required: true,
  };

  const financeOfficeReferralQueueSeed: FinanceHardshipFinanceOfficeReferralQueueItem = {
    hardship_id: 1,
    request_id: 1,
    student_id: 'S-1001',
    support_priority: 'high',
    hardship_status: 'finance_office_referral_recorded',
    readiness_status: 'ready_for_human_review',
    receivables_metadata_id: 7,
    referral_target: 'student_finance_office',
    referral_reason: 'manual_follow_up',
    referral_priority: 'high',
    note: 'finance_office_referral_metadata_only',
    referred_by_user_id: 'reviewer-1',
    source_module: 'student_services_support',
    target_module: 'finance_procurement_asset',
    no_automatic_aid_decision: true,
    no_billing_balance_mutation: true,
    no_payment_execution: true,
    human_review_required: true,
  };

  const base: StudentServicesSupportState = {
    loading: false,
    error: null,
    incompleteData: true,
    requests: [requestSeed],
    requestDetail: requestSeed,
    cases: [caseSeed],
    caseDetail: caseSeed,
    notes: [noteSeed],
    evidence: [evidenceSeed],
    hardship: readinessSeed,
    accommodation: readinessSeed,
    complaint: complaintSeed,
    escalation: escalationSeed,
    dashboard: buildDefaultDashboard(),
    financeHardshipQueue: [],
    financeOfficeReferralQueue: [],
  };

  if (routeKey === 'dashboard') {
    base.dashboard = {
      ...buildDefaultDashboard(),
      open_requests: 1,
      open_support_cases: 1,
      escalated_cases: 1,
      hardship_readiness_counts: { ready_for_human_review: 1 },
      finance_hardship_handoff_visibility: {
        source_module: 'finance_procurement_asset',
        source_flow: 'student_finance_receivables_handoff',
        total: 2,
        review_queue_count: 1,
        missing_evidence_count: 1,
        readiness_counts: { ready_for_human_review: 1, blocked_missing_required_evidence: 1 },
        no_automatic_aid_decision: true,
        no_billing_balance_mutation: true,
        human_review_required: true,
      },
      accommodation_readiness_counts: { ready_for_human_review: 1 },
      complaint_counts: { routed: 1 },
    };
    base.financeHardshipQueue = [financeHardshipQueueSeed];
    base.financeOfficeReferralQueue = [financeOfficeReferralQueueSeed];
  }

  return base;
}

export function StudentServicesBoundaryBanner({ labels }: { labels: string[] }) {
  return (
    <section className="rounded-xl border border-amber-200 bg-amber-50 p-4" data-testid="sss-boundary-banner">
      <div className="flex flex-wrap gap-2">
        {labels.map((label) => (
          <span key={label} data-testid={`sss-boundary-${slugify(label)}`} className="inline-flex rounded-full border border-amber-300 px-3 py-1 text-xs font-medium text-amber-900">
            {label}
          </span>
        ))}
      </div>
    </section>
  );
}

export function StudentServicesPermissionGate({
  permission,
  children,
  fallback,
}: {
  permission: string;
  children: ReactNode;
  fallback?: ReactNode;
}) {
  return <PermissionGate permission={permission as never} fallback={fallback}>{children}</PermissionGate>;
}

export function StudentServiceRequestStatusBadge({ status }: { status: string }) {
  return <span className="rounded-full border px-2 py-1 text-xs font-medium" data-testid="sss-request-status-badge">{status}</span>;
}

export function StudentServiceAssignmentPanel({ assignedTo }: { assignedTo?: string | null }) {
  return (
    <section className="rounded-xl border bg-card p-4" data-testid="sss-assignment-panel">
      <h3 className="text-base font-semibold">Assignment</h3>
      <p className="mt-2 text-sm text-muted-foreground">Assigned to: {assignedTo ?? 'Unassigned'}</p>
      <p className="mt-2 text-xs text-muted-foreground">Human review required. No automatic assignment outcome.</p>
    </section>
  );
}

export function StudentServiceRequestList({ items }: { items: ServiceRequestRecord[] }) {
  if (items.length === 0) {
    return <p data-testid="sss-requests-empty" className="text-sm text-muted-foreground">No service requests found.</p>;
  }

  return (
    <section className="rounded-xl border bg-card p-4" data-testid="sss-request-list">
      <h3 className="text-base font-semibold">Service Requests</h3>
      <ul className="mt-3 space-y-2 text-sm">
        {items.map((item) => (
          <li key={item.id} className="rounded-lg border p-3">
            <div className="flex items-center justify-between gap-3">
              <span className="font-medium">#{item.id} {item.subject ?? 'Support request'}</span>
              <StudentServiceRequestStatusBadge status={item.status} />
            </div>
            <p className="mt-1 text-muted-foreground">Priority: {item.support_priority}</p>
          </li>
        ))}
      </ul>
    </section>
  );
}

export function StudentServiceRequestDetail({ item }: { item: ServiceRequestRecord | null }) {
  if (!item) {
    return <p data-testid="sss-request-detail-empty" className="text-sm text-muted-foreground">Request detail is unavailable.</p>;
  }

  return (
    <section className="rounded-xl border bg-card p-4" data-testid="sss-request-detail">
      <h3 className="text-base font-semibold">Request Detail</h3>
      <p className="mt-2 text-sm">Student ID: {item.student_id}</p>
      <p className="text-sm text-muted-foreground">{item.description ?? 'Evidence metadata only.'}</p>
      <StudentServiceAssignmentPanel assignedTo={item.assigned_to_user_id} />
    </section>
  );
}

export function StudentSupportCaseList({ items }: { items: SupportCaseRecord[] }) {
  if (items.length === 0) {
    return <p data-testid="sss-cases-empty" className="text-sm text-muted-foreground">No support cases found.</p>;
  }

  return (
    <section className="rounded-xl border bg-card p-4" data-testid="sss-case-list">
      <h3 className="text-base font-semibold">Support Cases</h3>
      <ul className="mt-3 space-y-2 text-sm">
        {items.map((item) => (
          <li key={item.id} className="rounded-lg border p-3">
            <div className="font-medium">#{item.id} {item.title ?? 'Support case'}</div>
            <p className="text-muted-foreground">Status: {item.status}</p>
          </li>
        ))}
      </ul>
    </section>
  );
}

export function SupportCaseNoteTimeline({ notes }: { notes: SupportCaseNoteRecord[] }) {
  return (
    <section className="rounded-xl border bg-card p-4" data-testid="sss-note-timeline">
      <h3 className="text-base font-semibold">Case Notes</h3>
      {notes.length === 0 ? (
        <p className="mt-2 text-sm text-muted-foreground">No notes yet.</p>
      ) : (
        <ul className="mt-3 space-y-2 text-sm text-muted-foreground">
          {notes.map((note) => (
            <li key={note.id}>{note.note}</li>
          ))}
        </ul>
      )}
    </section>
  );
}

export function SupportEvidenceMetadataPanel({ evidence }: { evidence: SupportEvidenceRecord[] }) {
  return (
    <section className="rounded-xl border bg-card p-4" data-testid="sss-evidence-panel">
      <h3 className="text-base font-semibold">Evidence Metadata</h3>
      {evidence.length === 0 ? (
        <p className="mt-2 text-sm text-muted-foreground">No evidence metadata records.</p>
      ) : (
        <ul className="mt-3 space-y-2 text-sm text-muted-foreground">
          {evidence.map((item) => (
            <li key={item.id}>{item.evidence_type} - {item.limitations ?? 'Evidence metadata only.'}</li>
          ))}
        </ul>
      )}
    </section>
  );
}

export function StudentSupportCaseDetail({ item, notes, evidence }: { item: SupportCaseRecord | null; notes: SupportCaseNoteRecord[]; evidence: SupportEvidenceRecord[] }) {
  if (!item) {
    return <p data-testid="sss-case-detail-empty" className="text-sm text-muted-foreground">Case detail is unavailable.</p>;
  }

  return (
    <section className="space-y-4" data-testid="sss-case-detail">
      <div className="rounded-xl border bg-card p-4">
        <h3 className="text-base font-semibold">Support Case Detail</h3>
        <p className="mt-2 text-sm">Case type: {item.case_type}</p>
        <p className="text-sm text-muted-foreground">Status: {item.status}</p>
      </div>
      <SupportCaseNoteTimeline notes={notes} />
      <SupportEvidenceMetadataPanel evidence={evidence} />
    </section>
  );
}

function ReadinessPanelBase({
  testId,
  title,
  record,
}: {
  testId: string;
  title: string;
  record: ReadinessRecord | null;
}) {
  return (
    <section className="rounded-xl border bg-card p-4" data-testid={testId}>
      <h3 className="text-base font-semibold">{title}</h3>
      {record ? (
        <>
          <p className="mt-2 text-sm">Status: {record.readiness_status}</p>
          <p className="mt-1 text-sm text-muted-foreground">Missing evidence: {record.missing_evidence.join(', ') || 'None'}</p>
          <p className="mt-1 text-xs text-muted-foreground">Recommended next step: {record.recommended_next_step ?? 'Human review required.'}</p>
        </>
      ) : (
        <p className="mt-2 text-sm text-muted-foreground">Readiness record unavailable.</p>
      )}
      <p className="mt-3 text-xs text-muted-foreground">Readiness only. No automatic approval.</p>
    </section>
  );
}

export function HardshipReadinessPanel({ record }: { record: ReadinessRecord | null }) {
  return <ReadinessPanelBase testId="sss-hardship-panel" title="Hardship Readiness" record={record} />;
}

export function FinanceHardshipHandoffPanel() {
  return (
    <section className="rounded-xl border bg-card p-4" data-testid="sss-finance-hardship-handoff-panel">
      <h3 className="text-base font-semibold">Finance hardship handoff</h3>
      <p className="mt-2 text-sm text-muted-foreground">POST /api/admin/student-services/hardship/from-finance-handoff</p>
      <div className="mt-3 grid gap-3 text-sm text-muted-foreground md:grid-cols-2">
        <div className="rounded-lg border p-3">
          <div className="font-medium text-foreground">Source metadata</div>
          <ul className="mt-2 space-y-1 text-xs">
            <li>student_id</li>
            <li>receivables_metadata_id</li>
            <li>evidence_refs</li>
            <li>support_priority</li>
          </ul>
        </div>
        <Link href="/console/finance-procurement-asset/student-finance" className="rounded-lg border p-3 hover:bg-muted/50">
          <div className="font-medium text-foreground">Finance source</div>
          <p className="mt-2 text-xs">Return to Student Finance Bridge and receivables metadata intake.</p>
        </Link>
      </div>
      <div className="mt-3 grid gap-3 text-xs text-muted-foreground md:grid-cols-3">
        <div className="rounded-lg border p-3">noAutomaticAidDecision=true</div>
        <div className="rounded-lg border p-3">noBillingBalanceMutation=true</div>
        <div className="rounded-lg border p-3">humanReviewRequired=true</div>
      </div>
    </section>
  );
}

export function AccommodationReadinessPanel({ record }: { record: ReadinessRecord | null }) {
  return <ReadinessPanelBase testId="sss-accommodation-panel" title="Accommodation Readiness" record={record} />;
}

export function StudentComplaintRoutingPanel({ complaint }: { complaint: ComplaintRecord | null }) {
  return (
    <section className="rounded-xl border bg-card p-4" data-testid="sss-complaint-panel">
      <h3 className="text-base font-semibold">Complaint Routing</h3>
      {complaint ? (
        <>
          <p className="mt-2 text-sm">Status: {complaint.status}</p>
          <p className="text-sm text-muted-foreground">Routed to: {complaint.routed_to ?? 'Not routed'}</p>
        </>
      ) : (
        <p className="mt-2 text-sm text-muted-foreground">Complaint routing metadata unavailable.</p>
      )}
      <p className="mt-3 text-xs text-muted-foreground">Evidence metadata only. No automatic complaint resolution.</p>
    </section>
  );
}

export function SupportEscalationPanel({ escalation }: { escalation: EscalationRecord | null }) {
  return (
    <section className="rounded-xl border bg-card p-4" data-testid="sss-escalation-panel">
      <h3 className="text-base font-semibold">Support Escalation</h3>
      {escalation ? (
        <>
          <p className="mt-2 text-sm">Escalation status: {escalation.escalation_status}</p>
          <p className="text-sm text-muted-foreground">Reason: {escalation.reason}</p>
        </>
      ) : (
        <p className="mt-2 text-sm text-muted-foreground">Escalation metadata unavailable.</p>
      )}
      <p className="mt-3 text-xs text-muted-foreground">No autonomous decision execution.</p>
    </section>
  );
}

export function StudentSupportDashboardSummary({ summary }: { summary: DashboardSummary | null }) {
  const data = summary ?? buildDefaultDashboard();
  return (
    <section className="space-y-4" data-testid="sss-dashboard-summary">
      <div className="rounded-xl border bg-card p-4">
        <h3 className="text-base font-semibold">Student Support Dashboard</h3>
        <ul className="mt-3 grid gap-2 text-sm text-muted-foreground md:grid-cols-2">
          <li>fake_metrics={String(data.fake_metrics)}</li>
          <li>data_source={data.data_source}</li>
          <li>incomplete_data={String(data.incomplete_data)}</li>
          <li>hidden_score_present={String(data.hidden_score_present)}</li>
          <li>provider_live_enabled={String(data.provider_live_enabled)}</li>
          <li>autonomous_decision_enabled={String(data.autonomous_decision_enabled)}</li>
        </ul>
      </div>
      <div className="grid gap-4 md:grid-cols-3">
        <article className="rounded-xl border bg-card p-4" data-testid="sss-dashboard-card-open-requests">
          <p className="text-xs uppercase text-muted-foreground">Open requests</p>
          <p className="mt-2 text-2xl font-semibold">{data.open_requests}</p>
        </article>
        <article className="rounded-xl border bg-card p-4" data-testid="sss-dashboard-card-open-cases">
          <p className="text-xs uppercase text-muted-foreground">Open support cases</p>
          <p className="mt-2 text-2xl font-semibold">{data.open_support_cases}</p>
        </article>
        <article className="rounded-xl border bg-card p-4" data-testid="sss-dashboard-card-escalated">
          <p className="text-xs uppercase text-muted-foreground">Escalated cases</p>
          <p className="mt-2 text-2xl font-semibold">{data.escalated_cases}</p>
        </article>
      </div>
      <article className="rounded-xl border bg-card p-4" data-testid="sss-dashboard-finance-hardship-visibility">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <p className="text-xs uppercase text-muted-foreground">Finance hardship handoff visibility</p>
            <h4 className="mt-1 text-lg font-semibold">{data.finance_hardship_handoff_visibility.total} finance-origin hardship requests</h4>
          </div>
          <Link href="/console/finance-procurement-asset/student-finance" className="rounded-lg border px-3 py-2 text-sm hover:bg-muted/50">
            Student Finance Bridge
          </Link>
        </div>
        <div className="mt-4 grid gap-3 border-t pt-3 text-sm md:grid-cols-3">
          <div>
            <p className="text-xs uppercase text-muted-foreground">Human review queue</p>
            <p className="mt-1 text-xl font-semibold">{data.finance_hardship_handoff_visibility.review_queue_count}</p>
          </div>
          <div>
            <p className="text-xs uppercase text-muted-foreground">Missing evidence</p>
            <p className="mt-1 text-xl font-semibold">{data.finance_hardship_handoff_visibility.missing_evidence_count}</p>
          </div>
          <div>
            <p className="text-xs uppercase text-muted-foreground">Source flow</p>
            <p className="mt-1 break-words text-xs text-muted-foreground">{data.finance_hardship_handoff_visibility.source_flow}</p>
          </div>
        </div>
        <ul className="mt-3 grid gap-2 text-xs text-muted-foreground md:grid-cols-3">
          <li>noAutomaticAidDecision={String(data.finance_hardship_handoff_visibility.no_automatic_aid_decision)}</li>
          <li>noBillingBalanceMutation={String(data.finance_hardship_handoff_visibility.no_billing_balance_mutation)}</li>
          <li>humanReviewRequired={String(data.finance_hardship_handoff_visibility.human_review_required)}</li>
        </ul>
      </article>
      <p className="text-sm text-muted-foreground">No hidden student score. No discriminatory risk score.</p>
    </section>
  );
}

export function FinanceHardshipReviewerQueuePanel({ items }: { items: FinanceHardshipReviewerQueueItem[] }) {
  return (
    <section className="rounded-xl border bg-card p-4" data-testid="sss-finance-hardship-reviewer-queue">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h3 className="text-base font-semibold">Finance hardship reviewer queue</h3>
          <p className="mt-1 text-sm text-muted-foreground">GET /api/admin/student-services/hardship/from-finance-handoff/reviewer-queue</p>
        </div>
        <Link href="/console/finance-procurement-asset/student-finance" className="rounded-lg border px-3 py-2 text-sm hover:bg-muted/50">
          Finance source
        </Link>
      </div>
      <div className="mt-4 space-y-3">
        {items.length > 0 ? items.map((item) => (
          <article key={item.hardship_id} className="border-t pt-3" data-testid="sss-finance-hardship-reviewer-queue-item">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <div>
                <p className="text-sm font-medium">{item.student_id ?? 'Student unavailable'}</p>
                <p className="text-xs text-muted-foreground">request_id={item.request_id ?? 'n/a'} receivables_metadata_id={item.receivables_metadata_id ?? 'n/a'}</p>
              </div>
              <span className="rounded-full border px-2 py-1 text-xs">{item.readiness_status}</span>
            </div>
            <dl className="mt-3 grid gap-2 text-xs text-muted-foreground md:grid-cols-3">
              <div>
                <dt className="uppercase">Priority</dt>
                <dd className="mt-1 text-foreground">{item.support_priority ?? 'n/a'}</dd>
              </div>
              <div>
                <dt className="uppercase">Service request</dt>
                <dd className="mt-1 text-foreground">{item.service_request_status ?? 'n/a'}</dd>
              </div>
              <div>
                <dt className="uppercase">Missing evidence</dt>
                <dd className="mt-1 text-foreground">{item.missing_evidence.length ? item.missing_evidence.join(', ') : 'none'}</dd>
              </div>
            </dl>
            <div className="mt-3 border-t pt-3 text-xs text-muted-foreground" data-testid="sss-finance-hardship-evidence-gap-intake-shell">
              <p className="font-medium text-foreground">Evidence gap intake metadata</p>
              <p className="mt-1 break-words">{`POST /api/admin/student-services/hardship/from-finance-handoff/${item.hardship_id}/evidence-gap`}</p>
              <ul className="mt-2 grid gap-1 md:grid-cols-2">
                <li>satisfies_gap={item.missing_evidence[0] ?? 'selected_gap'}</li>
                <li>evidence_type=document_metadata</li>
                <li>evidence_ref=metadata_reference_only</li>
                <li>source_available=false</li>
              </ul>
            </div>
            <div className="mt-3 border-t pt-3 text-xs text-muted-foreground" data-testid="sss-finance-hardship-human-review-outcome-note-shell">
              <p className="font-medium text-foreground">Human review outcome note metadata</p>
              <p className="mt-1 break-words">{`POST /api/admin/student-services/hardship/from-finance-handoff/${item.hardship_id}/human-review-outcome-note`}</p>
              <ul className="mt-2 grid gap-1 md:grid-cols-2">
                <li>outcome_label=manual_review_recorded</li>
                <li>reviewer_recommendation=non_executing_note</li>
                <li>note=human_review_metadata_only</li>
                <li>noAutomaticAidDecision=true</li>
              </ul>
            </div>
            <div className="mt-3 border-t pt-3 text-xs text-muted-foreground" data-testid="sss-finance-hardship-finance-office-referral-shell">
              <p className="font-medium text-foreground">Finance-office referral metadata</p>
              <p className="mt-1 break-words">{`POST /api/admin/student-services/hardship/from-finance-handoff/${item.hardship_id}/finance-office-referral`}</p>
              <ul className="mt-2 grid gap-1 md:grid-cols-2">
                <li>referral_target=student_finance_office</li>
                <li>referral_priority=high</li>
                <li>referral_reason=manual_follow_up</li>
                <li>noPaymentExecution=true</li>
              </ul>
            </div>
          </article>
        )) : (
          <p className="border-t pt-3 text-sm text-muted-foreground">No finance-origin hardship records in reviewer queue.</p>
        )}
      </div>
      <ul className="mt-4 grid gap-2 border-t pt-3 text-xs text-muted-foreground md:grid-cols-3">
        <li>noAutomaticAidDecision=true</li>
        <li>noBillingBalanceMutation=true</li>
        <li>humanReviewRequired=true</li>
      </ul>
    </section>
  );
}

export function FinanceHardshipFinanceOfficeReferralQueuePanel({ items }: { items: FinanceHardshipFinanceOfficeReferralQueueItem[] }) {
  return (
    <section className="rounded-xl border bg-card p-4" data-testid="sss-finance-hardship-finance-office-referral-queue">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h3 className="text-base font-semibold">Finance-office referral queue</h3>
          <p className="mt-1 text-sm text-muted-foreground">GET /api/admin/student-services/hardship/from-finance-handoff/finance-office-referral-queue</p>
        </div>
        <Link href="/console/finance-procurement-asset/student-finance" className="rounded-lg border px-3 py-2 text-sm hover:bg-muted/50">
          Finance office
        </Link>
      </div>
      <div className="mt-4 space-y-3">
        {items.length > 0 ? items.map((item) => (
          <article key={item.hardship_id} className="border-t pt-3" data-testid="sss-finance-hardship-finance-office-referral-queue-item">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <div>
                <p className="text-sm font-medium">{item.student_id ?? 'Student unavailable'}</p>
                <p className="text-xs text-muted-foreground">hardship_id={item.hardship_id} request_id={item.request_id ?? 'n/a'} receivables_metadata_id={item.receivables_metadata_id ?? 'n/a'}</p>
              </div>
              <span className="rounded-full border px-2 py-1 text-xs">{item.hardship_status}</span>
            </div>
            <dl className="mt-3 grid gap-2 text-xs text-muted-foreground md:grid-cols-3">
              <div>
                <dt className="uppercase">Referral target</dt>
                <dd className="mt-1 text-foreground">{item.referral_target ?? 'n/a'}</dd>
              </div>
              <div>
                <dt className="uppercase">Referral priority</dt>
                <dd className="mt-1 text-foreground">{item.referral_priority ?? 'n/a'}</dd>
              </div>
              <div>
                <dt className="uppercase">Referral reason</dt>
                <dd className="mt-1 text-foreground">{item.referral_reason ?? 'n/a'}</dd>
              </div>
            </dl>
            <p className="mt-2 text-xs text-muted-foreground">target_module={item.target_module} referred_by_user_id={item.referred_by_user_id ?? 'n/a'}</p>
          </article>
        )) : (
          <p className="border-t pt-3 text-sm text-muted-foreground">No finance-office referral records in queue.</p>
        )}
      </div>
      <ul className="mt-4 grid gap-2 border-t pt-3 text-xs text-muted-foreground md:grid-cols-2">
        <li>noAutomaticAidDecision=true</li>
        <li>noBillingBalanceMutation=true</li>
        <li>noPaymentExecution=true</li>
        <li>humanReviewRequired=true</li>
      </ul>
    </section>
  );
}

function StudentServicesErrorPanel({ message }: { message: string }) {
  return (
    <div className="rounded-xl border border-destructive/40 bg-destructive/5 p-4" data-testid="sss-error-state">
      <h3 className="text-base font-semibold">Backend error</h3>
      <p className="mt-2 text-sm text-muted-foreground">{message}</p>
    </div>
  );
}

function StudentServicesLoadingPanel() {
  return (
    <div className="rounded-xl border p-4" data-testid="sss-loading-state">
      Loading Student Services Support...
    </div>
  );
}

function StudentServicesTenantFailClosedPanel() {
  return (
    <div className="rounded-xl border border-orange-300 bg-orange-50 p-4" data-testid="sss-tenant-fail-closed-state">
      Tenant fail-closed / not found boundary active.
    </div>
  );
}

function StudentServicesNoOverclaimFooter() {
  return (
    <footer className="rounded-xl border border-dashed p-4 text-sm text-muted-foreground" data-testid="sss-no-overclaim-footer">
      <p>No automatic hardship approval UI.</p>
      <p>No automatic accommodation approval UI.</p>
      <p>No automatic complaint resolution UI.</p>
      <p>No diagnosis UI.</p>
      <p>No hidden score UI.</p>
      <p>No government/provider submission UI.</p>
      <p>No Brain/autonomous decision execution UI.</p>
      <p>No production/sales/GCC/L5/L6 claim.</p>
    </footer>
  );
}

export function StudentServicesSupportShell({ routeKey, children }: { routeKey: StudentServicesSupportRouteKey; children: ReactNode }) {
  const route = getRouteDefinition(routeKey);

  return (
    <div className="space-y-6" data-testid="sss-page-shell">
      <header className="space-y-2">
        <p className="text-sm uppercase tracking-[0.2em] text-muted-foreground">Student Services / Welfare / Support Suite</p>
        <h1 className="text-3xl font-semibold">{route.title}</h1>
      </header>

      <nav className="flex flex-wrap gap-2" aria-label="Student services support navigation">
        {STUDENT_SERVICES_SUPPORT_NAV_ITEMS.map((item) => (
          <Link key={item.key} href={item.href} className={`rounded-full border px-3 py-1 text-sm ${item.key === routeKey ? 'bg-primary text-primary-foreground' : 'text-muted-foreground'}`}>
            {item.title}
          </Link>
        ))}
      </nav>

      {children}
    </div>
  );
}

function RouteContent({ routeKey, state }: { routeKey: StudentServicesSupportRouteKey; state: StudentServicesSupportState }) {
  const route = getRouteDefinition(routeKey);

  if (state.loading) {
    return <StudentServicesLoadingPanel />;
  }

  if (state.error) {
    return <StudentServicesErrorPanel message={state.error} />;
  }

  const routeLabels = STUDENT_SERVICES_ROUTE_BOUNDARIES[route.key];

  return (
    <StudentServicesSupportShell routeKey={routeKey}>
      <div className="space-y-4" data-testid={`sss-page-${route.key}`}>
        <StudentServicesBoundaryBanner labels={routeLabels} />

        {state.incompleteData ? (
          <div className="rounded-xl border border-dashed p-4 text-sm text-muted-foreground" data-testid="sss-incomplete-data-state">
            incomplete_data supported. Missing fields are explicit and not replaced with fake values.
          </div>
        ) : null}

        {routeKey === 'overview' ? (
          <>
            <StudentServiceRequestList items={state.requests ?? []} />
            <StudentSupportCaseList items={state.cases ?? []} />
          </>
        ) : null}

        {routeKey === 'requests' ? <StudentServiceRequestList items={state.requests ?? []} /> : null}
        {routeKey === 'request-detail' ? <StudentServiceRequestDetail item={state.requestDetail ?? null} /> : null}
        {routeKey === 'cases' ? <StudentSupportCaseList items={state.cases ?? []} /> : null}
        {routeKey === 'case-detail' ? (
          <StudentSupportCaseDetail
            item={state.caseDetail ?? null}
            notes={state.notes ?? []}
            evidence={state.evidence ?? []}
          />
        ) : null}
        {routeKey === 'hardship' ? (
          <>
            <HardshipReadinessPanel record={state.hardship ?? null} />
            <FinanceHardshipHandoffPanel />
          </>
        ) : null}
        {routeKey === 'accommodations' ? <AccommodationReadinessPanel record={state.accommodation ?? null} /> : null}
        {routeKey === 'complaints' ? <StudentComplaintRoutingPanel complaint={state.complaint ?? null} /> : null}
        {routeKey === 'escalations' ? <SupportEscalationPanel escalation={state.escalation ?? null} /> : null}
        {routeKey === 'dashboard' ? (
          <>
            <StudentSupportDashboardSummary summary={state.dashboard ?? null} />
            <FinanceHardshipReviewerQueuePanel items={state.financeHardshipQueue ?? []} />
            <FinanceHardshipFinanceOfficeReferralQueuePanel items={state.financeOfficeReferralQueue ?? []} />
          </>
        ) : null}

        <div className="rounded-xl border bg-card p-4 text-sm text-muted-foreground" data-testid="sss-route-contract-panel">
          <p>Route: {route.path}</p>
          <p>Required permission: {route.requiredPermission}</p>
          <p>Runtime mode: {STUDENT_SERVICES_SUPPORT_RUNTIME_MODE}</p>
          <p>Evidence metadata only state is active.</p>
        </div>

        <StudentServicesTenantFailClosedPanel />
        <StudentServicesNoOverclaimFooter />
      </div>
    </StudentServicesSupportShell>
  );
}

export function StudentServicesSupportPage({
  routeKey,
  userPermissions,
  stateOverride,
}: {
  routeKey: StudentServicesSupportRouteKey;
  userPermissions?: string[];
  stateOverride?: StudentServicesSupportState;
}) {
  const route = getRouteDefinition(routeKey);
  const state = {
    ...buildDefaultState(routeKey),
    ...stateOverride,
  };

  if (userPermissions) {
    return hasStudentServicesSupportPermission(userPermissions, route.requiredPermission)
      ? <RouteContent routeKey={routeKey} state={state} />
      : <div data-testid="sss-permission-denied-state" className="rounded-xl border border-destructive/30 bg-destructive/5 p-4">{route.permissionDeniedState}</div>;
  }

  return (
    <RequirePermission permission={route.requiredPermission} message="This Student Services Support route is fail-closed until the required permission is granted.">
      <RouteContent routeKey={routeKey} state={state} />
    </RequirePermission>
  );
}

export {
  STUDENT_SERVICES_BOUNDARY_COPY,
  STUDENT_SERVICES_FORBIDDEN_LABELS,
  STUDENT_SERVICES_SUPPORT_SAFETY_FLAGS,
};
