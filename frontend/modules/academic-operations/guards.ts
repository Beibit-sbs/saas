import type { Permission } from '@/shared/config/permissions';
import { PERMISSIONS } from '@/shared/config/permissions';
import type { AcademicOperationsDashboard, AcademicOperationsHealth, AcademicOperationsMatrixSummary } from './types';
import {
  ACADEMIC_OPERATIONS_BACKEND_PERMISSION_COUNT,
  ACADEMIC_OPERATIONS_BACKEND_ROUTE_COUNT,
  MASTER_MATRIX_COMMIT,
  MASTER_MATRIX_ROW_COUNT,
} from './constants';
import { ACADEMIC_OPERATIONS_BOUNDARY_COPY, ACADEMIC_OPERATIONS_PAGE_BOUNDARY_LABELS, type AcademicOperationsPageKey } from './boundaryLabels';

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

export class AcademicOperationsDataQualityError extends Error {}

export const ACADEMIC_OPERATIONS_PERMISSIONS = {
  overviewRead: PERMISSIONS.ACADEMIC_OPERATIONS_OVERVIEW_READ,
  dashboardRead: PERMISSIONS.ACADEMIC_OPERATIONS_DASHBOARD_READ,
  healthRead: PERMISSIONS.ACADEMIC_OPERATIONS_HEALTH_READ,
  auditRead: PERMISSIONS.ACADEMIC_OPERATIONS_AUDIT_READ,
  evidenceRead: PERMISSIONS.ACADEMIC_OPERATIONS_EVIDENCE_READ,
  evidenceAttach: PERMISSIONS.ACADEMIC_OPERATIONS_EVIDENCE_ATTACH,
  canonicalBridgeRead: PERMISSIONS.ACADEMIC_OPERATIONS_CANONICAL_BRIDGE_READ,
  canonicalBridgeCreate: PERMISSIONS.ACADEMIC_OPERATIONS_CANONICAL_BRIDGE_CREATE,
  canonicalBridgeUpdate: PERMISSIONS.ACADEMIC_OPERATIONS_CANONICAL_BRIDGE_UPDATE,
  studentLifecycleBridgeRead: PERMISSIONS.ACADEMIC_OPERATIONS_STUDENT_LIFECYCLE_BRIDGE_READ,
  documentWorkflowBridgeRead: PERMISSIONS.ACADEMIC_OPERATIONS_DOCUMENT_WORKFLOW_BRIDGE_READ,
  executiveGovernanceBridgeRead: PERMISSIONS.ACADEMIC_OPERATIONS_EXECUTIVE_GOVERNANCE_BRIDGE_READ,
  qualityAccreditationBridgeRead: PERMISSIONS.ACADEMIC_OPERATIONS_QUALITY_ACCREDITATION_BRIDGE_READ,
  academicGroupsRead: PERMISSIONS.ACADEMIC_OPERATIONS_ACADEMIC_GROUPS_READ,
  academicGroupsCreate: PERMISSIONS.ACADEMIC_OPERATIONS_ACADEMIC_GROUPS_CREATE,
  academicGroupsUpdate: PERMISSIONS.ACADEMIC_OPERATIONS_ACADEMIC_GROUPS_UPDATE,
  cohortsRead: PERMISSIONS.ACADEMIC_OPERATIONS_COHORTS_READ,
  cohortsCreate: PERMISSIONS.ACADEMIC_OPERATIONS_COHORTS_CREATE,
  cohortsUpdate: PERMISSIONS.ACADEMIC_OPERATIONS_COHORTS_UPDATE,
  gradebookMetadataRead: PERMISSIONS.ACADEMIC_OPERATIONS_GRADEBOOK_METADATA_READ,
  gradebookMetadataCreate: PERMISSIONS.ACADEMIC_OPERATIONS_GRADEBOOK_METADATA_CREATE,
  gradebookMetadataUpdate: PERMISSIONS.ACADEMIC_OPERATIONS_GRADEBOOK_METADATA_UPDATE,
  retakeManagementRead: PERMISSIONS.ACADEMIC_OPERATIONS_RETAKE_MANAGEMENT_READ,
  retakeManagementCreate: PERMISSIONS.ACADEMIC_OPERATIONS_RETAKE_MANAGEMENT_CREATE,
  retakeManagementUpdate: PERMISSIONS.ACADEMIC_OPERATIONS_RETAKE_MANAGEMENT_UPDATE,
  summerSemesterRead: PERMISSIONS.ACADEMIC_OPERATIONS_SUMMER_SEMESTER_READ,
  summerSemesterCreate: PERMISSIONS.ACADEMIC_OPERATIONS_SUMMER_SEMESTER_CREATE,
  summerSemesterUpdate: PERMISSIONS.ACADEMIC_OPERATIONS_SUMMER_SEMESTER_UPDATE,
  advisorTutorRead: PERMISSIONS.ACADEMIC_OPERATIONS_ADVISOR_TUTOR_READ,
  advisorTutorCreate: PERMISSIONS.ACADEMIC_OPERATIONS_ADVISOR_TUTOR_CREATE,
  advisorTutorUpdate: PERMISSIONS.ACADEMIC_OPERATIONS_ADVISOR_TUTOR_UPDATE,
} as const;

export function hasAcademicOperationsPermission(user: PermissionUser, permission: Permission) {
  return permissionSet(user).has(permission);
}

export function canReadAcademicOperations(user: PermissionUser) {
  return hasAcademicOperationsPermission(user, ACADEMIC_OPERATIONS_PERMISSIONS.overviewRead);
}

export function canReadDashboard(user: PermissionUser) {
  return hasAcademicOperationsPermission(user, ACADEMIC_OPERATIONS_PERMISSIONS.dashboardRead);
}

export function canReadMatrixSummary(user: PermissionUser) {
  return hasAcademicOperationsPermission(user, ACADEMIC_OPERATIONS_PERMISSIONS.overviewRead);
}

export function canReadAcademicGroups(user: PermissionUser) {
  return hasAcademicOperationsPermission(user, ACADEMIC_OPERATIONS_PERMISSIONS.academicGroupsRead);
}

export function canReadCohorts(user: PermissionUser) {
  return hasAcademicOperationsPermission(user, ACADEMIC_OPERATIONS_PERMISSIONS.cohortsRead);
}

export function canReadGradebookMetadata(user: PermissionUser) {
  return hasAcademicOperationsPermission(user, ACADEMIC_OPERATIONS_PERMISSIONS.gradebookMetadataRead);
}

export function canReadRetakes(user: PermissionUser) {
  return hasAcademicOperationsPermission(user, ACADEMIC_OPERATIONS_PERMISSIONS.retakeManagementRead);
}

export function canReadSummerSemesters(user: PermissionUser) {
  return hasAcademicOperationsPermission(user, ACADEMIC_OPERATIONS_PERMISSIONS.summerSemesterRead);
}

export function canReadAdvisorTutor(user: PermissionUser) {
  return hasAcademicOperationsPermission(user, ACADEMIC_OPERATIONS_PERMISSIONS.advisorTutorRead);
}

export function canReadBridges(user: PermissionUser) {
  return hasAcademicOperationsPermission(user, ACADEMIC_OPERATIONS_PERMISSIONS.canonicalBridgeRead)
    || hasAcademicOperationsPermission(user, ACADEMIC_OPERATIONS_PERMISSIONS.studentLifecycleBridgeRead)
    || hasAcademicOperationsPermission(user, ACADEMIC_OPERATIONS_PERMISSIONS.documentWorkflowBridgeRead)
    || hasAcademicOperationsPermission(user, ACADEMIC_OPERATIONS_PERMISSIONS.executiveGovernanceBridgeRead)
    || hasAcademicOperationsPermission(user, ACADEMIC_OPERATIONS_PERMISSIONS.qualityAccreditationBridgeRead);
}

export function canReadAuditEvidence(user: PermissionUser) {
  return hasAcademicOperationsPermission(user, ACADEMIC_OPERATIONS_PERMISSIONS.auditRead)
    || hasAcademicOperationsPermission(user, ACADEMIC_OPERATIONS_PERMISSIONS.evidenceRead);
}

export function isForbiddenAcademicOperationsAction(action: string) {
  return [
    'delete',
    'publish official grade',
    'calculate official grade',
    'approve grade',
    'sanction student',
    'dismiss student',
    'sync with platonus',
    'sync with sis',
    'provider dispatch',
    'generate official transcript',
    'generate official order/decree',
    'hidden scoring',
  ].includes(action.toLowerCase());
}

export function getAcademicOperationsBoundaryLabels(page: AcademicOperationsPageKey | string) {
  return [...(ACADEMIC_OPERATIONS_PAGE_BOUNDARY_LABELS[page as AcademicOperationsPageKey] ?? ACADEMIC_OPERATIONS_BOUNDARY_COPY)];
}

function assertFalse(value: boolean, message: string) {
  if (value) {
    throw new AcademicOperationsDataQualityError(message);
  }
}

export function assertTrustedAcademicOperationsDashboard(payload: AcademicOperationsDashboard) {
  assertFalse(payload.fake_metrics !== false, 'Academic Operations dashboard could not be verified: fake_metrics=true');
  if (payload.master_matrix_commit !== MASTER_MATRIX_COMMIT) {
    throw new AcademicOperationsDataQualityError(`Academic Operations dashboard matrix commit mismatch: expected ${MASTER_MATRIX_COMMIT}, received ${payload.master_matrix_commit}`);
  }
  if (payload.master_matrix_rows !== MASTER_MATRIX_ROW_COUNT) {
    throw new AcademicOperationsDataQualityError(`Academic Operations dashboard matrix row count mismatch: expected ${MASTER_MATRIX_ROW_COUNT}, received ${payload.master_matrix_rows}`);
  }
}

export function assertTrustedAcademicOperationsHealth(payload: AcademicOperationsHealth) {
  assertFalse(payload.fake_metrics !== false, 'Academic Operations health payload could not be verified: fake_metrics=true');
  assertFalse(payload.provider_integration_enabled, 'Academic Operations health payload could not be verified: provider_integration_enabled=true');
  assertFalse(payload.platonus_sync_enabled, 'Academic Operations health payload could not be verified: platonus_sync_enabled=true');
  assertFalse(payload.sis_sync_enabled, 'Academic Operations health payload could not be verified: sis_sync_enabled=true');
  assertFalse(payload.hidden_score_present, 'Academic Operations health payload could not be verified: hidden_score_present=true');
  if (payload.route_count !== ACADEMIC_OPERATIONS_BACKEND_ROUTE_COUNT) {
    throw new AcademicOperationsDataQualityError(`Academic Operations health route count mismatch: expected ${ACADEMIC_OPERATIONS_BACKEND_ROUTE_COUNT}, received ${payload.route_count}`);
  }
}

export function assertTrustedAcademicOperationsMatrixSummary(payload: AcademicOperationsMatrixSummary) {
  if (payload.master_matrix_commit !== MASTER_MATRIX_COMMIT) {
    throw new AcademicOperationsDataQualityError(`Academic Operations matrix commit mismatch: expected ${MASTER_MATRIX_COMMIT}, received ${payload.master_matrix_commit}`);
  }
  if (payload.master_matrix_rows !== MASTER_MATRIX_ROW_COUNT) {
    throw new AcademicOperationsDataQualityError(`Academic Operations matrix row count mismatch: expected ${MASTER_MATRIX_ROW_COUNT}, received ${payload.master_matrix_rows}`);
  }
  if (payload.forbidden_runtime_claims.length > ACADEMIC_OPERATIONS_BACKEND_PERMISSION_COUNT) {
    throw new AcademicOperationsDataQualityError('Academic Operations matrix summary looks inconsistent with the backend contract.');
  }
}