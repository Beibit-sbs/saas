import type {
  ApplicantStatusHistoryResponse,
  DegreeProgressSnapshotResponse,
  InterventionPlanResponse,
  StudentAppealResponse,
  StudentEnrollmentResponse,
  StudentLifecycleAuditEventResponse,
  StudentRequestResponse,
  TranscriptPreviewResponse,
} from '../types';
import {
  HumanReviewRequiredBadge,
  MetadataOnlyNotice,
  NoAutomatedDecisionBadge,
  NoHiddenScoreBadge,
  SourceUnavailableNotice,
  SupportVisibilityOnlyBadge,
  UnofficialPreviewBadge,
} from './boundaries';
import { AuditTrailPanel, StudentLifecycleStatusBadge, StudentLifecycleStatusTimeline } from './status';

export function ApplicantStatusTimeline({ history }: { history: ApplicantStatusHistoryResponse[] }) {
  return (
    <section className="rounded-lg border p-4" data-testid="applicant-status-timeline">
      <div className="mb-3 flex gap-2">
        <HumanReviewRequiredBadge />
        <NoAutomatedDecisionBadge />
      </div>
      <StudentLifecycleStatusTimeline entries={history} />
    </section>
  );
}

export function EnrollmentReviewPanel({ enrollment }: { enrollment?: StudentEnrollmentResponse | null }) {
  return (
    <section className="rounded-lg border p-4" data-testid="enrollment-review-panel">
      <div className="mb-3 flex gap-2">
        <HumanReviewRequiredBadge />
        <MetadataOnlyNotice />
      </div>
      {enrollment ? (
        <div className="space-y-2 text-sm">
          <p>Student: #{enrollment.student_id}</p>
          <p>Term: {enrollment.term_code}</p>
          <StudentLifecycleStatusBadge status={enrollment.status} />
        </div>
      ) : (
        <p className="text-sm text-muted-foreground">No enrollment selected.</p>
      )}
    </section>
  );
}

export function TranscriptPreviewPanel({ preview }: { preview?: TranscriptPreviewResponse | null }) {
  return (
    <section className="rounded-lg border p-4" data-testid="transcript-preview-panel">
      <div className="mb-3 flex flex-wrap gap-2">
        <UnofficialPreviewBadge />
        <MetadataOnlyNotice />
      </div>
      {preview ? (
        <div className="space-y-2 text-sm">
          <p>Official document not issued: {String(!preview.official_document)}</p>
          <p>Digital signature not enabled</p>
          <StudentLifecycleStatusBadge status={preview.status} />
        </div>
      ) : (
        <p className="text-sm text-muted-foreground">No transcript preview selected.</p>
      )}
    </section>
  );
}

export function GraduationReadinessPanel({ snapshot }: { snapshot?: DegreeProgressSnapshotResponse | null }) {
  return (
    <section className="rounded-lg border p-4" data-testid="graduation-readiness-panel">
      <div className="mb-3 flex flex-wrap gap-2">
        <HumanReviewRequiredBadge />
        <NoAutomatedDecisionBadge />
      </div>
      {snapshot ? (
        <div className="space-y-2 text-sm">
          <StudentLifecycleStatusBadge status={snapshot.status} />
          <p>No automatic graduation eligibility decision</p>
          {snapshot.incomplete_data ? <SourceUnavailableNotice /> : null}
        </div>
      ) : (
        <p className="text-sm text-muted-foreground">No degree progress snapshot selected.</p>
      )}
    </section>
  );
}

export function StudentRequestReviewPanel({ request }: { request?: StudentRequestResponse | null }) {
  return (
    <section className="rounded-lg border p-4" data-testid="student-request-review-panel">
      <div className="mb-3 flex gap-2">
        <HumanReviewRequiredBadge />
        <MetadataOnlyNotice />
      </div>
      {request ? (
        <div className="space-y-2 text-sm">
          <StudentLifecycleStatusBadge status={request.status} />
          <p>{request.description}</p>
          <p>Decision metadata only</p>
        </div>
      ) : (
        <p className="text-sm text-muted-foreground">No request selected.</p>
      )}
    </section>
  );
}

export function StudentAppealReviewPanel({ appeal }: { appeal?: StudentAppealResponse | null }) {
  return (
    <section className="rounded-lg border p-4" data-testid="student-appeal-review-panel">
      <div className="mb-3 flex gap-2">
        <HumanReviewRequiredBadge />
        <NoAutomatedDecisionBadge />
      </div>
      {appeal ? (
        <div className="space-y-2 text-sm">
          <StudentLifecycleStatusBadge status={appeal.status} />
          <p>{appeal.description}</p>
          <p>No autonomous appeal decision</p>
        </div>
      ) : (
        <p className="text-sm text-muted-foreground">No appeal selected.</p>
      )}
    </section>
  );
}

export function InterventionPlanPanel({ plan }: { plan?: InterventionPlanResponse | null }) {
  return (
    <section className="rounded-lg border p-4" data-testid="intervention-plan-panel">
      <div className="mb-3 flex gap-2">
        <NoHiddenScoreBadge />
        <SupportVisibilityOnlyBadge />
      </div>
      {plan ? (
        <div className="space-y-2 text-sm">
          <StudentLifecycleStatusBadge status={plan.status} />
          <p>{plan.plan_summary}</p>
          <p>No punitive automation</p>
        </div>
      ) : (
        <p className="text-sm text-muted-foreground">No intervention selected.</p>
      )}
    </section>
  );
}

export function InterventionFollowupTimeline({ plan }: { plan?: InterventionPlanResponse | null }) {
  if (!plan?.followups.length) {
    return <p className="text-sm text-muted-foreground">No intervention follow-ups recorded yet.</p>;
  }

  return (
    <section className="rounded-lg border p-4" data-testid="intervention-followup-timeline">
      <h3 className="text-sm font-semibold">Follow-up timeline</h3>
      <ul className="mt-3 space-y-3 text-sm">
        {plan.followups.map((followup, index) => (
          <li key={index} className="rounded-md border border-dashed p-3">
            <pre className="overflow-x-auto text-xs">{JSON.stringify(followup, null, 2)}</pre>
          </li>
        ))}
      </ul>
    </section>
  );
}

export function AuditPanel({ audit }: { audit: StudentLifecycleAuditEventResponse[] }) {
  return <AuditTrailPanel events={audit} />;
}