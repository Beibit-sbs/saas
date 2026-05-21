'use client';

import { RequirePermission, PermissionGate } from '@/shared/ui/permission-gate';
import { ErrorState, LoadingState } from '@/shared/ui/page-states';
import {
  STUDENT_LIFECYCLE_APPEAL_PERMISSIONS,
  STUDENT_LIFECYCLE_APPLICANT_PERMISSIONS,
  STUDENT_LIFECYCLE_AUDIT_PERMISSIONS,
  STUDENT_LIFECYCLE_DASHBOARD_PERMISSIONS,
  STUDENT_LIFECYCLE_DEGREE_PROGRESS_PERMISSIONS,
  STUDENT_LIFECYCLE_ENROLLMENT_PERMISSIONS,
  STUDENT_LIFECYCLE_INTERVENTION_PERMISSIONS,
  STUDENT_LIFECYCLE_RECORD_PERMISSIONS,
  STUDENT_LIFECYCLE_REQUEST_PERMISSIONS,
  STUDENT_LIFECYCLE_STUDENT_PERMISSIONS,
  STUDENT_LIFECYCLE_TRANSCRIPT_PERMISSIONS,
} from '../guards';
import {
  useApplicants,
  useCreateEnrollment,
  useDegreeProgress,
  useEnrollments,
  useInterventionPlans,
  useStudentAppeals,
  useStudentLifecycleAudit,
  useStudentLifecycleDashboard,
  useStudentLifecycleEvidence,
  useStudentLifecycleHealth,
  useStudentRequests,
  useStudents,
  useTranscriptPreviews,
  useAcademicRecords,
} from '../hooks';
import {
  HumanReviewRequiredBadge,
  MetadataOnlyNotice,
  NoAutomatedDecisionBadge,
  NoHiddenScoreBadge,
  StudentLifecycleBoundaryBanner,
  StudentLifecycleLimitationsPanel,
  SupportVisibilityOnlyBadge,
} from './boundaries';
import {
  AcademicRecordRegistry,
  ApplicantRegistry,
  DegreeProgressDashboard,
  EnrollmentRegistry,
  InterventionDashboard,
  StudentAppealRegistry,
  StudentLifecycleAuditLog,
  StudentRegistry,
  StudentRequestRegistry,
  TranscriptPreviewRegistry,
} from './registries';
import { AuditTrailPanel, EvidenceMetadataPanel } from './status';
import { StudentLifecycleOverviewDashboard } from './overview';
import {
  ApplicantStatusTimeline,
  EnrollmentReviewPanel,
  GraduationReadinessPanel,
  InterventionFollowupTimeline,
  InterventionPlanPanel,
  StudentAppealReviewPanel,
  StudentRequestReviewPanel,
  TranscriptPreviewPanel,
} from './workflow-panels';

function ModulePageShell({
  title,
  description,
  children,
}: {
  title: string;
  description: string;
  children: React.ReactNode;
}) {
  return (
    <div className="space-y-6" data-testid="student-lifecycle-page">
      <header className="space-y-2">
        <h1 className="text-2xl font-semibold">{title}</h1>
        <p className="text-sm text-muted-foreground">{description}</p>
      </header>
      {children}
    </div>
  );
}

function PageError(message: string, error: unknown) {
  return <ErrorState error={error} message={message} />;
}

export function StudentLifecycleOverviewPage() {
  const dashboard = useStudentLifecycleDashboard();
  const health = useStudentLifecycleHealth();

  if (dashboard.isPending || health.isPending) {
    return <LoadingState title="Loading Student Lifecycle overview" />;
  }

  if (dashboard.error) {
    return PageError('Failed to load Student Lifecycle overview.', dashboard.error);
  }

  if (health.error) {
    return PageError('Failed to load Student Lifecycle runtime health.', health.error);
  }

  if (!dashboard.data || !health.data) {
    return <ErrorState message="Student Lifecycle overview is unavailable." />;
  }

  return (
    <RequirePermission permission={STUDENT_LIFECYCLE_DASHBOARD_PERMISSIONS.read}>
      <ModulePageShell
        title="Student Lifecycle Suite"
        description="Controlled overview over applicants, students, enrollment, records, transcripts, degree progress, requests, appeals, interventions, and audit."
      >
        <StudentLifecycleOverviewDashboard dashboard={dashboard.data} health={health.data} />
      </ModulePageShell>
    </RequirePermission>
  );
}

export function ApplicantsPage() {
  const applicants = useApplicants();

  if (applicants.isPending) return <LoadingState title="Loading applicants" />;
  if (applicants.error) return PageError('Failed to load applicants.', applicants.error);

  const firstApplicant = applicants.data?.[0];
  const timeline = firstApplicant
    ? [
        {
          id: firstApplicant.id,
          tenant_id: firstApplicant.tenant_id,
          applicant_id: firstApplicant.id,
          previous_status: null,
          new_status: firstApplicant.status,
          created_at: firstApplicant.updated_at,
          reason: 'Current applicant status snapshot',
        },
      ]
    : [];

  return (
    <RequirePermission permission={STUDENT_LIFECYCLE_APPLICANT_PERMISSIONS.read}>
      <ModulePageShell title="Applicants" description="Applicant registry with explicit human-review boundaries.">
        <StudentLifecycleBoundaryBanner labels={['Human review required', 'No automated decision is made', 'Metadata only']} />
        <ApplicantRegistry applicants={applicants.data ?? []} />
        <ApplicantStatusTimeline history={timeline} />
      </ModulePageShell>
    </RequirePermission>
  );
}

export function StudentsPage() {
  const students = useStudents();

  if (students.isPending) return <LoadingState title="Loading students" />;
  if (students.error) return PageError('Failed to load students.', students.error);

  return (
    <RequirePermission permission={STUDENT_LIFECYCLE_STUDENT_PERMISSIONS.read}>
      <ModulePageShell title="Students" description="Student profiles from the Student Lifecycle backend foundation.">
        <StudentLifecycleBoundaryBanner labels={['Human review required', 'Provider integration not enabled', 'Metadata only']} />
        <StudentRegistry students={students.data ?? []} />
      </ModulePageShell>
    </RequirePermission>
  );
}

export function EnrollmentPage() {
  const enrollments = useEnrollments();
  const createEnrollment = useCreateEnrollment();

  if (enrollments.isPending) return <LoadingState title="Loading enrollment" />;
  if (enrollments.error) return PageError('Failed to load enrollment.', enrollments.error);

  return (
    <RequirePermission permission={STUDENT_LIFECYCLE_ENROLLMENT_PERMISSIONS.read}>
      <ModulePageShell title="Enrollment" description="Registrar-reviewed enrollment records only.">
        <StudentLifecycleBoundaryBanner labels={['Human review required', 'Metadata only', 'Audit-backed transition']} />
        <PermissionGate permission={STUDENT_LIFECYCLE_ENROLLMENT_PERMISSIONS.create} fallback={null}>
          <button className="rounded-md border px-3 py-2 text-sm" disabled={createEnrollment.isPending} type="button">
            Create enrollment
          </button>
        </PermissionGate>
        <EnrollmentRegistry enrollments={enrollments.data ?? []} />
        <EnrollmentReviewPanel enrollment={enrollments.data?.[0] ?? null} />
      </ModulePageShell>
    </RequirePermission>
  );
}

export function AcademicRecordsPage() {
  const records = useAcademicRecords();

  if (records.isPending) return <LoadingState title="Loading academic records" />;
  if (records.error) return PageError('Failed to load academic records.', records.error);

  return (
    <RequirePermission permission={STUDENT_LIFECYCLE_RECORD_PERMISSIONS.read}>
      <ModulePageShell title="Academic records" description="Academic record metadata only. No fake grades or unsupported source claims.">
        <StudentLifecycleBoundaryBanner labels={['Metadata only', 'Source unavailable', 'Human review required']} />
        <AcademicRecordRegistry records={records.data ?? []} />
      </ModulePageShell>
    </RequirePermission>
  );
}

export function TranscriptPreviewsPage() {
  const previews = useTranscriptPreviews();

  if (previews.isPending) return <LoadingState title="Loading transcript previews" />;
  if (previews.error) return PageError('Failed to load transcript previews.', previews.error);

  return (
    <RequirePermission permission={STUDENT_LIFECYCLE_TRANSCRIPT_PERMISSIONS.read}>
      <ModulePageShell title="Transcript previews" description="Unofficial transcript previews only. Official issuing is intentionally out of scope.">
        <StudentLifecycleBoundaryBanner labels={['Unofficial preview', 'Official document not issued', 'Digital signature not enabled']} />
        <PermissionGate permission={STUDENT_LIFECYCLE_TRANSCRIPT_PERMISSIONS.preview} fallback={null}>
          <button className="rounded-md border px-3 py-2 text-sm" type="button">Create transcript preview</button>
        </PermissionGate>
        <TranscriptPreviewRegistry transcripts={previews.data ?? []} />
        <TranscriptPreviewPanel preview={previews.data?.[0] ?? null} />
      </ModulePageShell>
    </RequirePermission>
  );
}

export function DegreeProgressPage() {
  const students = useStudents();
  const studentId = students.data?.[0]?.id;
  const progress = useDegreeProgress(studentId ?? '');

  if (students.isPending || (studentId && progress.isPending)) {
    return <LoadingState title="Loading degree progress" />;
  }

  if (students.error) return PageError('Failed to load students for degree progress.', students.error);
  if (progress.error) return PageError('Failed to load degree progress.', progress.error);

  return (
    <RequirePermission permission={STUDENT_LIFECYCLE_DEGREE_PROGRESS_PERMISSIONS.read}>
      <ModulePageShell title="Degree progress" description="Computed from available sources only, bounded by human review.">
        <StudentLifecycleBoundaryBanner labels={['Human review required', 'No automatic graduation eligibility decision', 'Incomplete data']} />
        <DegreeProgressDashboard snapshot={progress.data ?? null} />
        <GraduationReadinessPanel snapshot={progress.data ?? null} />
        {progress.data?.limitations?.length ? <StudentLifecycleLimitationsPanel limitations={progress.data.limitations} /> : null}
      </ModulePageShell>
    </RequirePermission>
  );
}

export function StudentRequestsPage() {
  const requests = useStudentRequests();

  if (requests.isPending) return <LoadingState title="Loading student requests" />;
  if (requests.error) return PageError('Failed to load student requests.', requests.error);

  return (
    <RequirePermission permission={STUDENT_LIFECYCLE_REQUEST_PERMISSIONS.read}>
      <ModulePageShell title="Student requests" description="Request workflow with decision metadata only.">
        <StudentLifecycleBoundaryBanner labels={['Human review required', 'No automated decision is made', 'Metadata only']} />
        <StudentRequestRegistry requests={requests.data ?? []} />
        <StudentRequestReviewPanel request={requests.data?.[0] ?? null} />
      </ModulePageShell>
    </RequirePermission>
  );
}

export function StudentAppealsPage() {
  const appeals = useStudentAppeals();

  if (appeals.isPending) return <LoadingState title="Loading student appeals" />;
  if (appeals.error) return PageError('Failed to load student appeals.', appeals.error);

  return (
    <RequirePermission permission={STUDENT_LIFECYCLE_APPEAL_PERMISSIONS.read}>
      <ModulePageShell title="Student appeals" description="Appeal workflow with explicit human-review boundaries and no autonomous decisions.">
        <StudentLifecycleBoundaryBanner labels={['Human review required', 'No autonomous appeal decision', 'Metadata only']} />
        <StudentAppealRegistry appeals={appeals.data ?? []} />
        <StudentAppealReviewPanel appeal={appeals.data?.[0] ?? null} />
      </ModulePageShell>
    </RequirePermission>
  );
}

export function InterventionsPage() {
  const plans = useInterventionPlans();

  if (plans.isPending) return <LoadingState title="Loading interventions" />;
  if (plans.error) return PageError('Failed to load interventions.', plans.error);

  return (
    <RequirePermission permission={STUDENT_LIFECYCLE_INTERVENTION_PERMISSIONS.read}>
      <ModulePageShell title="Interventions" description="Support visibility only. No hidden score or punitive automation.">
        <StudentLifecycleBoundaryBanner labels={['Support visibility only', 'No hidden risk score', 'Human review required']}>
          <div className="flex gap-2">
            <NoHiddenScoreBadge />
            <SupportVisibilityOnlyBadge />
          </div>
        </StudentLifecycleBoundaryBanner>
        <InterventionDashboard plans={plans.data ?? []} />
        <InterventionPlanPanel plan={plans.data?.[0] ?? null} />
        <InterventionFollowupTimeline plan={plans.data?.[0] ?? null} />
      </ModulePageShell>
    </RequirePermission>
  );
}

export function StudentLifecycleAuditPage() {
  const audit = useStudentLifecycleAudit();
  const evidence = useStudentLifecycleEvidence();

  if (audit.isPending || evidence.isPending) return <LoadingState title="Loading student lifecycle audit" />;
  if (audit.error) return PageError('Failed to load student lifecycle audit.', audit.error);
  if (evidence.error) return PageError('Failed to load evidence metadata.', evidence.error);

  return (
    <RequirePermission permission={STUDENT_LIFECYCLE_AUDIT_PERMISSIONS.read}>
      <ModulePageShell title="Audit" description="Audit-backed transitions and evidence metadata only.">
        <StudentLifecycleBoundaryBanner labels={['Audit-backed transition', 'Metadata only', 'No hard delete']}>
          <div className="flex gap-2">
            <MetadataOnlyNotice />
            <HumanReviewRequiredBadge />
            <NoAutomatedDecisionBadge />
          </div>
        </StudentLifecycleBoundaryBanner>
        <StudentLifecycleAuditLog audit={audit.data ?? []} />
        <AuditTrailPanel events={audit.data ?? []} />
        <EvidenceMetadataPanel evidence={evidence.data ?? []} />
      </ModulePageShell>
    </RequirePermission>
  );
}