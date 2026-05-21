import type { Permission } from '@/shared/config/permissions';
import { PERMISSIONS } from '@/shared/config/permissions';
import {
  AUTONOMOUS_DECISION_ENABLED,
  EXPECTED_DATA_SOURCE,
  HIDDEN_SCORE_ENABLED,
  OFFICIAL_TRANSCRIPT_ISSUING_ENABLED,
  PROVIDER_INTEGRATION_ENABLED,
} from './constants';
import type {
  DegreeProgressSnapshotResponse,
  StudentLifecycleDashboardResponse,
  StudentLifecycleHealthResponse,
} from './types';

type PermissionUser =
  | {
      permissions?: Array<string | Permission>;
      rolePermissions?: Array<string | Permission>;
      grantedPermissions?: Array<string | Permission>;
    }
  | null
  | undefined;

function permissionSet(user: PermissionUser) {
  const values = new Set<string>();
  const sources = [user?.permissions, user?.rolePermissions, user?.grantedPermissions];
  for (const source of sources) {
    for (const permission of source ?? []) {
      values.add(String(permission));
    }
  }
  return values;
}

export class StudentLifecycleDataQualityError extends Error {}

export const STUDENT_LIFECYCLE_DASHBOARD_PERMISSIONS = {
  read: PERMISSIONS.STUDENT_LIFECYCLE_DASHBOARD_READ,
  health: PERMISSIONS.STUDENT_LIFECYCLE_HEALTH_READ,
  admin: PERMISSIONS.STUDENT_LIFECYCLE_ADMIN_READ,
} as const;

export const STUDENT_LIFECYCLE_APPLICANT_PERMISSIONS = {
  read: PERMISSIONS.STUDENT_LIFECYCLE_APPLICANTS_READ,
  create: PERMISSIONS.STUDENT_LIFECYCLE_APPLICANTS_CREATE,
  update: PERMISSIONS.STUDENT_LIFECYCLE_APPLICANTS_UPDATE,
  statusUpdate: PERMISSIONS.STUDENT_LIFECYCLE_APPLICANTS_STATUS_UPDATE,
} as const;

export const STUDENT_LIFECYCLE_STUDENT_PERMISSIONS = {
  read: PERMISSIONS.STUDENT_LIFECYCLE_STUDENTS_READ,
  create: PERMISSIONS.STUDENT_LIFECYCLE_STUDENTS_CREATE,
  update: PERMISSIONS.STUDENT_LIFECYCLE_STUDENTS_UPDATE,
  statusUpdate: PERMISSIONS.STUDENT_LIFECYCLE_STUDENTS_STATUS_UPDATE,
} as const;

export const STUDENT_LIFECYCLE_ENROLLMENT_PERMISSIONS = {
  read: PERMISSIONS.STUDENT_LIFECYCLE_ENROLLMENT_READ,
  create: PERMISSIONS.STUDENT_LIFECYCLE_ENROLLMENT_CREATE,
  update: PERMISSIONS.STUDENT_LIFECYCLE_ENROLLMENT_UPDATE,
  review: PERMISSIONS.STUDENT_LIFECYCLE_ENROLLMENT_REVIEW,
} as const;

export const STUDENT_LIFECYCLE_RECORD_PERMISSIONS = {
  read: PERMISSIONS.STUDENT_LIFECYCLE_RECORDS_READ,
  create: PERMISSIONS.STUDENT_LIFECYCLE_RECORDS_CREATE,
  resultMetadataWrite: PERMISSIONS.STUDENT_LIFECYCLE_RECORDS_RESULT_METADATA_WRITE,
} as const;

export const STUDENT_LIFECYCLE_TRANSCRIPT_PERMISSIONS = {
  read: PERMISSIONS.STUDENT_LIFECYCLE_TRANSCRIPTS_READ,
  preview: PERMISSIONS.STUDENT_LIFECYCLE_TRANSCRIPTS_PREVIEW,
} as const;

export const STUDENT_LIFECYCLE_DEGREE_PROGRESS_PERMISSIONS = {
  read: PERMISSIONS.STUDENT_LIFECYCLE_DEGREE_PROGRESS_READ,
  compute: PERMISSIONS.STUDENT_LIFECYCLE_DEGREE_PROGRESS_COMPUTE,
  review: PERMISSIONS.STUDENT_LIFECYCLE_GRADUATION_READINESS_REVIEW,
} as const;

export const STUDENT_LIFECYCLE_REQUEST_PERMISSIONS = {
  read: PERMISSIONS.STUDENT_LIFECYCLE_REQUESTS_READ,
  create: PERMISSIONS.STUDENT_LIFECYCLE_REQUESTS_CREATE,
  review: PERMISSIONS.STUDENT_LIFECYCLE_REQUESTS_REVIEW,
} as const;

export const STUDENT_LIFECYCLE_APPEAL_PERMISSIONS = {
  read: PERMISSIONS.STUDENT_LIFECYCLE_APPEALS_READ,
  create: PERMISSIONS.STUDENT_LIFECYCLE_APPEALS_CREATE,
  review: PERMISSIONS.STUDENT_LIFECYCLE_APPEALS_REVIEW,
} as const;

export const STUDENT_LIFECYCLE_INTERVENTION_PERMISSIONS = {
  read: PERMISSIONS.STUDENT_LIFECYCLE_INTERVENTIONS_READ,
  signalCreate: PERMISSIONS.STUDENT_LIFECYCLE_INTERVENTIONS_SIGNAL_CREATE,
  planCreate: PERMISSIONS.STUDENT_LIFECYCLE_INTERVENTIONS_PLAN_CREATE,
  followupWrite: PERMISSIONS.STUDENT_LIFECYCLE_INTERVENTIONS_FOLLOWUP_WRITE,
} as const;

export const STUDENT_LIFECYCLE_AUDIT_PERMISSIONS = {
  read: PERMISSIONS.STUDENT_LIFECYCLE_AUDIT_READ,
  evidenceRead: PERMISSIONS.STUDENT_LIFECYCLE_EVIDENCE_READ,
  evidenceAttach: PERMISSIONS.STUDENT_LIFECYCLE_EVIDENCE_ATTACH,
} as const;

export function hasStudentLifecyclePermission(user: PermissionUser, permission: Permission) {
  return permissionSet(user).has(permission);
}

export function canViewStudentLifecycleDashboard(user: PermissionUser) {
  return hasStudentLifecyclePermission(user, STUDENT_LIFECYCLE_DASHBOARD_PERMISSIONS.read);
}

export function canViewApplicants(user: PermissionUser) {
  return hasStudentLifecyclePermission(user, STUDENT_LIFECYCLE_APPLICANT_PERMISSIONS.read);
}

export function canManageApplicants(user: PermissionUser) {
  return hasStudentLifecyclePermission(user, STUDENT_LIFECYCLE_APPLICANT_PERMISSIONS.create)
    || hasStudentLifecyclePermission(user, STUDENT_LIFECYCLE_APPLICANT_PERMISSIONS.update)
    || hasStudentLifecyclePermission(user, STUDENT_LIFECYCLE_APPLICANT_PERMISSIONS.statusUpdate);
}

export function canViewStudents(user: PermissionUser) {
  return hasStudentLifecyclePermission(user, STUDENT_LIFECYCLE_STUDENT_PERMISSIONS.read);
}

export function canManageStudents(user: PermissionUser) {
  return hasStudentLifecyclePermission(user, STUDENT_LIFECYCLE_STUDENT_PERMISSIONS.create)
    || hasStudentLifecyclePermission(user, STUDENT_LIFECYCLE_STUDENT_PERMISSIONS.update)
    || hasStudentLifecyclePermission(user, STUDENT_LIFECYCLE_STUDENT_PERMISSIONS.statusUpdate);
}

export function canViewEnrollment(user: PermissionUser) {
  return hasStudentLifecyclePermission(user, STUDENT_LIFECYCLE_ENROLLMENT_PERMISSIONS.read);
}

export function canReviewEnrollment(user: PermissionUser) {
  return hasStudentLifecyclePermission(user, STUDENT_LIFECYCLE_ENROLLMENT_PERMISSIONS.review);
}

export function canViewAcademicRecords(user: PermissionUser) {
  return hasStudentLifecyclePermission(user, STUDENT_LIFECYCLE_RECORD_PERMISSIONS.read);
}

export function canCreateTranscriptPreview(user: PermissionUser) {
  return hasStudentLifecyclePermission(user, STUDENT_LIFECYCLE_TRANSCRIPT_PERMISSIONS.preview);
}

export function canReviewGraduationReadiness(user: PermissionUser) {
  return hasStudentLifecyclePermission(user, STUDENT_LIFECYCLE_DEGREE_PROGRESS_PERMISSIONS.review);
}

export function canViewRequests(user: PermissionUser) {
  return hasStudentLifecyclePermission(user, STUDENT_LIFECYCLE_REQUEST_PERMISSIONS.read);
}

export function canReviewRequests(user: PermissionUser) {
  return hasStudentLifecyclePermission(user, STUDENT_LIFECYCLE_REQUEST_PERMISSIONS.review);
}

export function canViewAppeals(user: PermissionUser) {
  return hasStudentLifecyclePermission(user, STUDENT_LIFECYCLE_APPEAL_PERMISSIONS.read);
}

export function canReviewAppeals(user: PermissionUser) {
  return hasStudentLifecyclePermission(user, STUDENT_LIFECYCLE_APPEAL_PERMISSIONS.review);
}

export function canViewInterventions(user: PermissionUser) {
  return hasStudentLifecyclePermission(user, STUDENT_LIFECYCLE_INTERVENTION_PERMISSIONS.read);
}

export function canManageInterventions(user: PermissionUser) {
  return hasStudentLifecyclePermission(user, STUDENT_LIFECYCLE_INTERVENTION_PERMISSIONS.planCreate)
    || hasStudentLifecyclePermission(user, STUDENT_LIFECYCLE_INTERVENTION_PERMISSIONS.followupWrite);
}

export function canViewStudentLifecycleAudit(user: PermissionUser) {
  return hasStudentLifecyclePermission(user, STUDENT_LIFECYCLE_AUDIT_PERMISSIONS.read);
}

function assertSafetyBooleans(payload: {
  provider_integration_enabled?: boolean;
  hidden_score_present?: boolean;
}) {
  if (payload.provider_integration_enabled !== PROVIDER_INTEGRATION_ENABLED) {
    throw new StudentLifecycleDataQualityError('Student Lifecycle payload could not be verified: provider_integration_enabled=true');
  }
  if (payload.hidden_score_present !== undefined && payload.hidden_score_present !== HIDDEN_SCORE_ENABLED) {
    throw new StudentLifecycleDataQualityError('Student Lifecycle payload could not be verified: hidden_score_present=true');
  }
}

export function assertTrustedStudentLifecycleDashboard(payload: StudentLifecycleDashboardResponse) {
  if (payload.fake_metrics !== false) {
    throw new StudentLifecycleDataQualityError('Student Lifecycle dashboard could not be verified: fake_metrics=true');
  }
  if (payload.data_source !== EXPECTED_DATA_SOURCE) {
    throw new StudentLifecycleDataQualityError(
      `Student Lifecycle dashboard data source mismatch: expected ${EXPECTED_DATA_SOURCE}, received ${payload.data_source}`,
    );
  }
  if (payload.automated_decision_count !== 0 || AUTONOMOUS_DECISION_ENABLED) {
    throw new StudentLifecycleDataQualityError('Student Lifecycle dashboard could not be verified: automated decisions are not allowed');
  }
  assertSafetyBooleans(payload);
}

export function assertTrustedStudentLifecycleHealth(payload: StudentLifecycleHealthResponse) {
  if (payload.fake_metrics !== false) {
    throw new StudentLifecycleDataQualityError('Student Lifecycle health payload could not be verified: fake_metrics=true');
  }
  if (payload.data_source !== EXPECTED_DATA_SOURCE) {
    throw new StudentLifecycleDataQualityError(
      `Student Lifecycle health data source mismatch: expected ${EXPECTED_DATA_SOURCE}, received ${payload.data_source}`,
    );
  }
  if (payload.automated_decision_count !== 0) {
    throw new StudentLifecycleDataQualityError('Student Lifecycle health payload could not be verified: automated decisions are not allowed');
  }
  assertSafetyBooleans(payload);
}

export function assertTrustedDegreeProgress(payload: DegreeProgressSnapshotResponse) {
  if (payload.data_source !== EXPECTED_DATA_SOURCE) {
    throw new StudentLifecycleDataQualityError(
      `Degree progress data source mismatch: expected ${EXPECTED_DATA_SOURCE}, received ${payload.data_source}`,
    );
  }
  if (payload.hidden_score_present !== HIDDEN_SCORE_ENABLED) {
    throw new StudentLifecycleDataQualityError('Degree progress payload could not be verified: hidden_score_present=true');
  }
  assertSafetyBooleans(payload);
}

export function canIssueOfficialTranscript() {
  return OFFICIAL_TRANSCRIPT_ISSUING_ENABLED;
}

export function canSyncProvider() {
  return PROVIDER_INTEGRATION_ENABLED;
}

export function canAutoDecide() {
  return AUTONOMOUS_DECISION_ENABLED;
}