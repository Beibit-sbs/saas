"""Student Lifecycle Suite permission constants."""

from __future__ import annotations

APPLICANTS_READ = "student_lifecycle.applicants.read"
APPLICANTS_CREATE = "student_lifecycle.applicants.create"
APPLICANTS_UPDATE = "student_lifecycle.applicants.update"
APPLICANTS_STATUS_UPDATE = "student_lifecycle.applicants.status.update"

STUDENTS_READ = "student_lifecycle.students.read"
STUDENTS_CREATE = "student_lifecycle.students.create"
STUDENTS_UPDATE = "student_lifecycle.students.update"
STUDENTS_STATUS_UPDATE = "student_lifecycle.students.status.update"

ENROLLMENT_READ = "student_lifecycle.enrollment.read"
ENROLLMENT_CREATE = "student_lifecycle.enrollment.create"
ENROLLMENT_UPDATE = "student_lifecycle.enrollment.update"
ENROLLMENT_REVIEW = "student_lifecycle.enrollment.review"

RECORDS_READ = "student_lifecycle.records.read"
RECORDS_CREATE = "student_lifecycle.records.create"
RECORDS_RESULT_METADATA_WRITE = "student_lifecycle.records.result_metadata.write"

TRANSCRIPTS_READ = "student_lifecycle.transcripts.read"
TRANSCRIPTS_PREVIEW = "student_lifecycle.transcripts.preview"

DEGREE_PROGRESS_READ = "student_lifecycle.degree_progress.read"
DEGREE_PROGRESS_COMPUTE = "student_lifecycle.degree_progress.compute"
GRADUATION_READINESS_REVIEW = "student_lifecycle.graduation_readiness.review"

REQUESTS_READ = "student_lifecycle.requests.read"
REQUESTS_CREATE = "student_lifecycle.requests.create"
REQUESTS_REVIEW = "student_lifecycle.requests.review"

APPEALS_READ = "student_lifecycle.appeals.read"
APPEALS_CREATE = "student_lifecycle.appeals.create"
APPEALS_REVIEW = "student_lifecycle.appeals.review"

INTERVENTIONS_READ = "student_lifecycle.interventions.read"
INTERVENTIONS_SIGNAL_CREATE = "student_lifecycle.interventions.signal.create"
INTERVENTIONS_PLAN_CREATE = "student_lifecycle.interventions.plan.create"
INTERVENTIONS_FOLLOWUP_WRITE = "student_lifecycle.interventions.followup.write"

AUDIT_READ = "student_lifecycle.audit.read"
EVIDENCE_READ = "student_lifecycle.evidence.read"
EVIDENCE_ATTACH = "student_lifecycle.evidence.attach"
DASHBOARD_READ = "student_lifecycle.dashboard.read"
HEALTH_READ = "student_lifecycle.health.read"
ADMIN_READ = "student_lifecycle.admin.read"

ALL_PERMISSIONS: frozenset[str] = frozenset({
    APPLICANTS_READ,
    APPLICANTS_CREATE,
    APPLICANTS_UPDATE,
    APPLICANTS_STATUS_UPDATE,
    STUDENTS_READ,
    STUDENTS_CREATE,
    STUDENTS_UPDATE,
    STUDENTS_STATUS_UPDATE,
    ENROLLMENT_READ,
    ENROLLMENT_CREATE,
    ENROLLMENT_UPDATE,
    ENROLLMENT_REVIEW,
    RECORDS_READ,
    RECORDS_CREATE,
    RECORDS_RESULT_METADATA_WRITE,
    TRANSCRIPTS_READ,
    TRANSCRIPTS_PREVIEW,
    DEGREE_PROGRESS_READ,
    DEGREE_PROGRESS_COMPUTE,
    GRADUATION_READINESS_REVIEW,
    REQUESTS_READ,
    REQUESTS_CREATE,
    REQUESTS_REVIEW,
    APPEALS_READ,
    APPEALS_CREATE,
    APPEALS_REVIEW,
    INTERVENTIONS_READ,
    INTERVENTIONS_SIGNAL_CREATE,
    INTERVENTIONS_PLAN_CREATE,
    INTERVENTIONS_FOLLOWUP_WRITE,
    AUDIT_READ,
    EVIDENCE_READ,
    EVIDENCE_ATTACH,
    DASHBOARD_READ,
    HEALTH_READ,
    ADMIN_READ,
})

STUDENT_LIFECYCLE_PERMISSIONS = sorted(ALL_PERMISSIONS)