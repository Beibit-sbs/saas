import type {
  AcademicRecordResponse,
  ApplicantResponse,
  DegreeProgressSnapshotResponse,
  InterventionPlanResponse,
  StudentAppealResponse,
  StudentEnrollmentResponse,
  StudentLifecycleAuditEventResponse,
  StudentProfileResponse,
  StudentRequestResponse,
  TranscriptPreviewResponse,
} from '../types';
import { MetadataOnlyNotice, StudentLifecycleBoundaryBanner, SupportVisibilityOnlyBadge, UnofficialPreviewBadge } from './boundaries';
import { AuditTrailPanel, StudentLifecycleStatusBadge } from './status';

function formatDate(value?: string | null) {
  if (!value) return 'Unavailable';
  try {
    return new Date(value).toLocaleDateString();
  } catch {
    return value;
  }
}

function RegistryShell({ title, description, children }: { title: string; description: string; children: React.ReactNode }) {
  return (
    <section className="space-y-4" data-testid={`${title.toLowerCase().replace(/[^a-z0-9]+/g, '-')}-registry`}>
      <div>
        <h3 className="text-lg font-semibold">{title}</h3>
        <p className="text-sm text-muted-foreground">{description}</p>
      </div>
      {children}
    </section>
  );
}

function RegistryTable({
  headers,
  rows,
  emptyMessage,
}: {
  headers: string[];
  rows: Array<Array<React.ReactNode>>;
  emptyMessage: string;
}) {
  if (!rows.length) {
    return <p className="rounded-lg border border-dashed p-4 text-sm text-muted-foreground">{emptyMessage}</p>;
  }

  return (
    <div className="overflow-x-auto rounded-lg border">
      <table className="min-w-full divide-y">
        <thead className="bg-muted/30">
          <tr>
            {headers.map((header) => (
              <th key={header} className="px-4 py-3 text-left text-xs uppercase tracking-wide text-muted-foreground">
                {header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y">
          {rows.map((row, index) => (
            <tr key={index}>
              {row.map((cell, cellIndex) => (
                <td key={cellIndex} className="px-4 py-3 text-sm">
                  {cell}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export function ApplicantRegistry({ applicants }: { applicants: ApplicantResponse[] }) {
  return (
    <RegistryShell title="Applicants" description="Metadata-backed applicant registry.">
      <RegistryTable
        headers={["Code", "Program", "Status", "Updated"]}
        rows={applicants.map((applicant) => [
          applicant.applicant_code,
          applicant.program_interest,
          <StudentLifecycleStatusBadge key={`${applicant.id}-status`} status={applicant.status} />,
          formatDate(applicant.updated_at),
        ])}
        emptyMessage="No applicants found."
      />
    </RegistryShell>
  );
}

export function StudentRegistry({ students }: { students: StudentProfileResponse[] }) {
  return (
    <RegistryShell title="Students" description="Student profiles from the runtime subset.">
      <RegistryTable
        headers={["Code", "Program", "Status", "Updated"]}
        rows={students.map((student) => [
          student.student_code,
          student.program_code,
          <StudentLifecycleStatusBadge key={`${student.id}-status`} status={student.status} />,
          formatDate(student.updated_at),
        ])}
        emptyMessage="No students found."
      />
    </RegistryShell>
  );
}

export function EnrollmentRegistry({ enrollments }: { enrollments: StudentEnrollmentResponse[] }) {
  return (
    <RegistryShell title="Enrollment" description="Registrar-reviewed enrollment records.">
      <RegistryTable
        headers={["Student", "Term", "Status", "Updated"]}
        rows={enrollments.map((item) => [
          `#${item.student_id}`,
          item.term_code,
          <StudentLifecycleStatusBadge key={`${item.id}-status`} status={item.status} />,
          formatDate(item.updated_at),
        ])}
        emptyMessage="No enrollment records found."
      />
    </RegistryShell>
  );
}

export function AcademicRecordRegistry({ records }: { records: AcademicRecordResponse[] }) {
  return (
    <RegistryShell title="Academic records" description="Academic record metadata only.">
      <div className="mb-3 flex gap-2">
        <MetadataOnlyNotice />
      </div>
      <RegistryTable
        headers={["Student", "Record", "Status", "Source"]}
        rows={records.map((record) => [
          `#${record.student_id}`,
          record.record_name,
          <StudentLifecycleStatusBadge key={`${record.id}-status`} status={record.status} />,
          record.source_available ? 'Available' : 'Unavailable',
        ])}
        emptyMessage="No academic records found."
      />
    </RegistryShell>
  );
}

export function TranscriptPreviewRegistry({ transcripts }: { transcripts: TranscriptPreviewResponse[] }) {
  return (
    <RegistryShell title="Transcript previews" description="Unofficial preview-only transcript visibility.">
      <div className="mb-3 flex gap-2">
        <UnofficialPreviewBadge />
        <MetadataOnlyNotice />
      </div>
      <RegistryTable
        headers={["Student", "Record", "Status", "Official"]}
        rows={transcripts.map((preview) => [
          `#${preview.student_id}`,
          `#${preview.academic_record_id}`,
          <StudentLifecycleStatusBadge key={`${preview.id}-status`} status={preview.status} />,
          String(preview.official_document),
        ])}
        emptyMessage="No transcript previews found."
      />
    </RegistryShell>
  );
}

export function DegreeProgressDashboard({ snapshot }: { snapshot?: DegreeProgressSnapshotResponse | null }) {
  return (
    <RegistryShell title="Degree progress" description="Computed from available sources only.">
      {snapshot ? (
        <div className="rounded-lg border p-4" data-testid="degree-progress-dashboard">
          <div className="flex flex-wrap gap-2">
            <StudentLifecycleStatusBadge status={snapshot.status} />
            {snapshot.incomplete_data ? <MetadataOnlyNotice /> : null}
          </div>
          <pre className="mt-4 overflow-x-auto rounded-md bg-muted/30 p-3 text-xs">{JSON.stringify(snapshot.completion_summary, null, 2)}</pre>
        </div>
      ) : (
        <p className="rounded-lg border border-dashed p-4 text-sm text-muted-foreground">No degree progress snapshot available yet.</p>
      )}
    </RegistryShell>
  );
}

export function StudentRequestRegistry({ requests }: { requests: StudentRequestResponse[] }) {
  return (
    <RegistryShell title="Student requests" description="Human-reviewed student requests.">
      <RegistryTable
        headers={["Student", "Type", "Status", "Updated"]}
        rows={requests.map((request) => [
          `#${request.student_id}`,
          request.request_type,
          <StudentLifecycleStatusBadge key={`${request.id}-status`} status={request.status} />,
          formatDate(request.updated_at),
        ])}
        emptyMessage="No student requests found."
      />
    </RegistryShell>
  );
}

export function StudentAppealRegistry({ appeals }: { appeals: StudentAppealResponse[] }) {
  return (
    <RegistryShell title="Student appeals" description="Appeal workflow with explicit review boundaries.">
      <RegistryTable
        headers={["Student", "Type", "Status", "Updated"]}
        rows={appeals.map((appeal) => [
          `#${appeal.student_id}`,
          appeal.appeal_type,
          <StudentLifecycleStatusBadge key={`${appeal.id}-status`} status={appeal.status} />,
          formatDate(appeal.updated_at),
        ])}
        emptyMessage="No student appeals found."
      />
    </RegistryShell>
  );
}

export function InterventionDashboard({ plans }: { plans: InterventionPlanResponse[] }) {
  return (
    <RegistryShell title="Interventions" description="Support visibility only. No hidden score or punitive automation.">
      <div className="mb-3 flex gap-2">
        <SupportVisibilityOnlyBadge />
      </div>
      <RegistryTable
        headers={["Student", "Signal", "Status", "Follow-ups"]}
        rows={plans.map((plan) => [
          `#${plan.student_id}`,
          plan.signal_type,
          <StudentLifecycleStatusBadge key={`${plan.id}-status`} status={plan.status} />,
          plan.followups.length,
        ])}
        emptyMessage="No intervention plans found."
      />
    </RegistryShell>
  );
}

export function StudentLifecycleAuditLog({ audit }: { audit: StudentLifecycleAuditEventResponse[] }) {
  return (
    <RegistryShell title="Audit log" description="Audit-backed transitions. No hard delete controls.">
      <StudentLifecycleBoundaryBanner labels={['Audit-backed transition', 'No hard delete']} />
      <AuditTrailPanel events={audit} />
    </RegistryShell>
  );
}