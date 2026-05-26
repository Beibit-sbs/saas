"""HR / Staff Governance backend foundation permission constants."""

from __future__ import annotations

OVERVIEW_READ = "hr_staff_governance.overview.read"
DASHBOARD_READ = "hr_staff_governance.dashboard.read"
HEALTH_READ = "hr_staff_governance.health.read"
LIMITATIONS_READ = "hr_staff_governance.limitations.read"
AUDIT_READ = "hr_staff_governance.audit.read"

STAFF_PROFILES_READ = "hr_staff_governance.staff_profiles.read"
STAFF_PROFILES_CREATE = "hr_staff_governance.staff_profiles.create"
STAFF_PROFILES_UPDATE = "hr_staff_governance.staff_profiles.update"
EMPLOYEE_RECORDS_READ = "hr_staff_governance.employee_records.read"
EMPLOYEE_RECORDS_CREATE = "hr_staff_governance.employee_records.create"
EMPLOYEE_RECORDS_UPDATE = "hr_staff_governance.employee_records.update"
FACULTY_PROFILES_READ = "hr_staff_governance.faculty_profiles.read"
FACULTY_PROFILES_UPDATE = "hr_staff_governance.faculty_profiles.update"

RECRUITMENT_READ = "hr_staff_governance.recruitment.read"
RECRUITMENT_CREATE = "hr_staff_governance.recruitment.create"
RECRUITMENT_REVIEW = "hr_staff_governance.recruitment.review"
HIRING_EVIDENCE_READ = "hr_staff_governance.hiring_evidence.read"
HIRING_EVIDENCE_CREATE = "hr_staff_governance.hiring_evidence.create"
ONBOARDING_READ = "hr_staff_governance.onboarding.read"
ONBOARDING_CREATE = "hr_staff_governance.onboarding.create"
ONBOARDING_UPDATE = "hr_staff_governance.onboarding.update"
PROBATION_READ = "hr_staff_governance.probation.read"
PROBATION_REVIEW = "hr_staff_governance.probation.review"

LEAVE_READ = "hr_staff_governance.leave.read"
LEAVE_CREATE = "hr_staff_governance.leave.create"
LEAVE_REVIEW = "hr_staff_governance.leave.review"
ATTENDANCE_READ = "hr_staff_governance.attendance.read"
STAFF_REQUESTS_READ = "hr_staff_governance.staff_requests.read"
STAFF_REQUESTS_CREATE = "hr_staff_governance.staff_requests.create"
STAFF_REQUESTS_REVIEW = "hr_staff_governance.staff_requests.review"
STAFF_APPEALS_READ = "hr_staff_governance.staff_appeals.read"
STAFF_APPEALS_CREATE = "hr_staff_governance.staff_appeals.create"
STAFF_APPEALS_REVIEW = "hr_staff_governance.staff_appeals.review"
POLICY_EXCEPTIONS_READ = "hr_staff_governance.policy_exceptions.read"
POLICY_EXCEPTIONS_CREATE = "hr_staff_governance.policy_exceptions.create"
POLICY_EXCEPTIONS_REVIEW = "hr_staff_governance.policy_exceptions.review"

APPRAISALS_READ = "hr_staff_governance.appraisals.read"
APPRAISALS_CREATE = "hr_staff_governance.appraisals.create"
APPRAISALS_REVIEW = "hr_staff_governance.appraisals.review"
TRAINING_READ = "hr_staff_governance.training.read"
TRAINING_CREATE = "hr_staff_governance.training.create"
TRAINING_UPDATE = "hr_staff_governance.training.update"
DISCIPLINARY_CASES_READ = "hr_staff_governance.disciplinary_cases.read"
DISCIPLINARY_CASES_CREATE = "hr_staff_governance.disciplinary_cases.create"
DISCIPLINARY_CASES_REVIEW = "hr_staff_governance.disciplinary_cases.review"
DISCIPLINARY_EVIDENCE_READ = "hr_staff_governance.disciplinary_evidence.read"
DISCIPLINARY_EVIDENCE_CREATE = "hr_staff_governance.disciplinary_evidence.create"

OFFBOARDING_READ = "hr_staff_governance.offboarding.read"
OFFBOARDING_CREATE = "hr_staff_governance.offboarding.create"
OFFBOARDING_UPDATE = "hr_staff_governance.offboarding.update"
ACCESS_LIFECYCLE_READ = "hr_staff_governance.access_lifecycle.read"
ACCESS_LIFECYCLE_REVIEW = "hr_staff_governance.access_lifecycle.review"
WORKLOAD_BRIDGE_READ = "hr_staff_governance.workload_bridge.read"
PAYROLL_READINESS_READ = "hr_staff_governance.payroll_readiness.read"
PAYROLL_READINESS_REVIEW = "hr_staff_governance.payroll_readiness.review"
PROVIDER_READINESS_READ = "hr_staff_governance.provider_readiness.read"

ALL_PERMISSIONS: frozenset[str] = frozenset(
    {
        OVERVIEW_READ,
        DASHBOARD_READ,
        HEALTH_READ,
        LIMITATIONS_READ,
        AUDIT_READ,
        STAFF_PROFILES_READ,
        STAFF_PROFILES_CREATE,
        STAFF_PROFILES_UPDATE,
        EMPLOYEE_RECORDS_READ,
        EMPLOYEE_RECORDS_CREATE,
        EMPLOYEE_RECORDS_UPDATE,
        FACULTY_PROFILES_READ,
        FACULTY_PROFILES_UPDATE,
        RECRUITMENT_READ,
        RECRUITMENT_CREATE,
        RECRUITMENT_REVIEW,
        HIRING_EVIDENCE_READ,
        HIRING_EVIDENCE_CREATE,
        ONBOARDING_READ,
        ONBOARDING_CREATE,
        ONBOARDING_UPDATE,
        PROBATION_READ,
        PROBATION_REVIEW,
        LEAVE_READ,
        LEAVE_CREATE,
        LEAVE_REVIEW,
        ATTENDANCE_READ,
        STAFF_REQUESTS_READ,
        STAFF_REQUESTS_CREATE,
        STAFF_REQUESTS_REVIEW,
        STAFF_APPEALS_READ,
        STAFF_APPEALS_CREATE,
        STAFF_APPEALS_REVIEW,
        POLICY_EXCEPTIONS_READ,
        POLICY_EXCEPTIONS_CREATE,
        POLICY_EXCEPTIONS_REVIEW,
        APPRAISALS_READ,
        APPRAISALS_CREATE,
        APPRAISALS_REVIEW,
        TRAINING_READ,
        TRAINING_CREATE,
        TRAINING_UPDATE,
        DISCIPLINARY_CASES_READ,
        DISCIPLINARY_CASES_CREATE,
        DISCIPLINARY_CASES_REVIEW,
        DISCIPLINARY_EVIDENCE_READ,
        DISCIPLINARY_EVIDENCE_CREATE,
        OFFBOARDING_READ,
        OFFBOARDING_CREATE,
        OFFBOARDING_UPDATE,
        ACCESS_LIFECYCLE_READ,
        ACCESS_LIFECYCLE_REVIEW,
        WORKLOAD_BRIDGE_READ,
        PAYROLL_READINESS_READ,
        PAYROLL_READINESS_REVIEW,
        PROVIDER_READINESS_READ,
    }
)

HR_STAFF_GOVERNANCE_PERMISSIONS = sorted(ALL_PERMISSIONS)
HR_STAFF_GOVERNANCE_PERMISSION_COUNT = 56