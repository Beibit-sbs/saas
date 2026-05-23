import type { Permission } from '@/shared/config/permissions';
import { PERMISSIONS } from '@/shared/config/permissions';
import {
  EXPECTED_DATA_SOURCE,
  MASTER_MATRIX_COMMIT,
  MASTER_MATRIX_ROW_COUNT,
  RESEARCH_SCIENCE_BACKEND_ROUTE_COUNT,
  RESEARCH_SCIENCE_TABLE_COUNT,
} from './constants';
import { RESEARCH_SCIENCE_BOUNDARY_COPY, RESEARCH_SCIENCE_PAGE_BOUNDARY_LABELS, type ResearchSciencePageKey } from './boundaryLabels';
import type {
  ResearchScienceDashboardResponse,
  ResearchScienceHealthResponse,
  ResearchScienceMatrixSummaryResponse,
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
  for (const source of [user?.permissions, user?.rolePermissions, user?.grantedPermissions]) {
    for (const permission of source ?? []) {
      values.add(String(permission));
    }
  }
  return values;
}

export class ResearchScienceDataQualityError extends Error {}

export const RESEARCH_SCIENCE_PERMISSIONS = {
  overviewRead: PERMISSIONS.RESEARCH_SCIENCE_OVERVIEW_READ,
  dashboardRead: PERMISSIONS.RESEARCH_SCIENCE_DASHBOARD_READ,
  healthRead: PERMISSIONS.RESEARCH_SCIENCE_HEALTH_READ,
  matrixRead: PERMISSIONS.RESEARCH_SCIENCE_MATRIX_READ,
  limitationsRead: PERMISSIONS.RESEARCH_SCIENCE_LIMITATIONS_READ,
  projectsRead: PERMISSIONS.RESEARCH_SCIENCE_PROJECTS_READ,
  projectsCreate: PERMISSIONS.RESEARCH_SCIENCE_PROJECTS_CREATE,
  projectsUpdate: PERMISSIONS.RESEARCH_SCIENCE_PROJECTS_UPDATE,
  studentResearchRead: PERMISSIONS.RESEARCH_SCIENCE_STUDENT_RESEARCH_READ,
  studentResearchCreate: PERMISSIONS.RESEARCH_SCIENCE_STUDENT_RESEARCH_CREATE,
  studentResearchUpdate: PERMISSIONS.RESEARCH_SCIENCE_STUDENT_RESEARCH_UPDATE,
  supervisionRead: PERMISSIONS.RESEARCH_SCIENCE_SUPERVISION_READ,
  supervisionCreate: PERMISSIONS.RESEARCH_SCIENCE_SUPERVISION_CREATE,
  supervisionUpdate: PERMISSIONS.RESEARCH_SCIENCE_SUPERVISION_UPDATE,
  publicationsRead: PERMISSIONS.RESEARCH_SCIENCE_PUBLICATIONS_READ,
  publicationsCreate: PERMISSIONS.RESEARCH_SCIENCE_PUBLICATIONS_CREATE,
  publicationsUpdate: PERMISSIONS.RESEARCH_SCIENCE_PUBLICATIONS_UPDATE,
  conferencesRead: PERMISSIONS.RESEARCH_SCIENCE_CONFERENCES_READ,
  conferencesCreate: PERMISSIONS.RESEARCH_SCIENCE_CONFERENCES_CREATE,
  conferencesUpdate: PERMISSIONS.RESEARCH_SCIENCE_CONFERENCES_UPDATE,
  grantsRead: PERMISSIONS.RESEARCH_SCIENCE_GRANTS_READ,
  grantsCreate: PERMISSIONS.RESEARCH_SCIENCE_GRANTS_CREATE,
  grantsUpdate: PERMISSIONS.RESEARCH_SCIENCE_GRANTS_UPDATE,
  ethicsRead: PERMISSIONS.RESEARCH_SCIENCE_ETHICS_READ,
  ethicsCreate: PERMISSIONS.RESEARCH_SCIENCE_ETHICS_CREATE,
  ethicsUpdate: PERMISSIONS.RESEARCH_SCIENCE_ETHICS_UPDATE,
  evidenceRead: PERMISSIONS.RESEARCH_SCIENCE_EVIDENCE_READ,
  evidenceAttach: PERMISSIONS.RESEARCH_SCIENCE_EVIDENCE_ATTACH,
  auditRead: PERMISSIONS.RESEARCH_SCIENCE_AUDIT_READ,
  bridgesRead: PERMISSIONS.RESEARCH_SCIENCE_BRIDGES_READ,
  bridgesCreate: PERMISSIONS.RESEARCH_SCIENCE_BRIDGES_CREATE,
} as const;

export function hasResearchSciencePermission(user: PermissionUser, permission: Permission) {
  return permissionSet(user).has(permission);
}

export function canReadResearchScienceOverview(user: PermissionUser) {
  return hasResearchSciencePermission(user, RESEARCH_SCIENCE_PERMISSIONS.overviewRead);
}

export function canReadResearchScienceDashboard(user: PermissionUser) {
  return hasResearchSciencePermission(user, RESEARCH_SCIENCE_PERMISSIONS.dashboardRead);
}

export function canReadResearchScienceHealth(user: PermissionUser) {
  return hasResearchSciencePermission(user, RESEARCH_SCIENCE_PERMISSIONS.healthRead);
}

export function canReadResearchScienceMatrix(user: PermissionUser) {
  return hasResearchSciencePermission(user, RESEARCH_SCIENCE_PERMISSIONS.matrixRead);
}

export function canReadResearchScienceLimitations(user: PermissionUser) {
  return hasResearchSciencePermission(user, RESEARCH_SCIENCE_PERMISSIONS.limitationsRead);
}

export function canReadResearchProjects(user: PermissionUser) {
  return hasResearchSciencePermission(user, RESEARCH_SCIENCE_PERMISSIONS.projectsRead);
}

export function canReadStudentResearch(user: PermissionUser) {
  return hasResearchSciencePermission(user, RESEARCH_SCIENCE_PERMISSIONS.studentResearchRead);
}

export function canReadScientificSupervision(user: PermissionUser) {
  return hasResearchSciencePermission(user, RESEARCH_SCIENCE_PERMISSIONS.supervisionRead);
}

export function canReadPublications(user: PermissionUser) {
  return hasResearchSciencePermission(user, RESEARCH_SCIENCE_PERMISSIONS.publicationsRead);
}

export function canReadConferences(user: PermissionUser) {
  return hasResearchSciencePermission(user, RESEARCH_SCIENCE_PERMISSIONS.conferencesRead);
}

export function canReadGrants(user: PermissionUser) {
  return hasResearchSciencePermission(user, RESEARCH_SCIENCE_PERMISSIONS.grantsRead);
}

export function canReadEthics(user: PermissionUser) {
  return hasResearchSciencePermission(user, RESEARCH_SCIENCE_PERMISSIONS.ethicsRead);
}

export function canReadEvidence(user: PermissionUser) {
  return hasResearchSciencePermission(user, RESEARCH_SCIENCE_PERMISSIONS.evidenceRead);
}

export function canReadAudit(user: PermissionUser) {
  return hasResearchSciencePermission(user, RESEARCH_SCIENCE_PERMISSIONS.auditRead);
}

export function canReadBridges(user: PermissionUser) {
  return hasResearchSciencePermission(user, RESEARCH_SCIENCE_PERMISSIONS.bridgesRead);
}

export function canCreateResearchProject(user: PermissionUser) {
  return hasResearchSciencePermission(user, RESEARCH_SCIENCE_PERMISSIONS.projectsCreate);
}

export function canUpdateResearchProject(user: PermissionUser) {
  return hasResearchSciencePermission(user, RESEARCH_SCIENCE_PERMISSIONS.projectsUpdate);
}

export function canCreateStudentResearchWork(user: PermissionUser) {
  return hasResearchSciencePermission(user, RESEARCH_SCIENCE_PERMISSIONS.studentResearchCreate);
}

export function canUpdateStudentResearchWork(user: PermissionUser) {
  return hasResearchSciencePermission(user, RESEARCH_SCIENCE_PERMISSIONS.studentResearchUpdate);
}

export function canCreatePublicationMetadata(user: PermissionUser) {
  return hasResearchSciencePermission(user, RESEARCH_SCIENCE_PERMISSIONS.publicationsCreate);
}

export function canUpdatePublicationMetadata(user: PermissionUser) {
  return hasResearchSciencePermission(user, RESEARCH_SCIENCE_PERMISSIONS.publicationsUpdate);
}

export function canCreateGrantApplication(user: PermissionUser) {
  return hasResearchSciencePermission(user, RESEARCH_SCIENCE_PERMISSIONS.grantsCreate);
}

export function canUpdateGrantApplication(user: PermissionUser) {
  return hasResearchSciencePermission(user, RESEARCH_SCIENCE_PERMISSIONS.grantsUpdate);
}

export function canCreateEthicsRequest(user: PermissionUser) {
  return hasResearchSciencePermission(user, RESEARCH_SCIENCE_PERMISSIONS.ethicsCreate);
}

export function canUpdateEthicsRequest(user: PermissionUser) {
  return hasResearchSciencePermission(user, RESEARCH_SCIENCE_PERMISSIONS.ethicsUpdate);
}

export function canAttachResearchEvidence(user: PermissionUser) {
  return hasResearchSciencePermission(user, RESEARCH_SCIENCE_PERMISSIONS.evidenceAttach);
}

export function canCreateResearchBridge(user: PermissionUser) {
  return hasResearchSciencePermission(user, RESEARCH_SCIENCE_PERMISSIONS.bridgesCreate);
}

export function isForbiddenResearchScienceAction(_action: string) {
  return false;
}

export function getResearchScienceBoundaryLabels(page: ResearchSciencePageKey | string) {
  return [...(RESEARCH_SCIENCE_PAGE_BOUNDARY_LABELS[page as ResearchSciencePageKey] ?? RESEARCH_SCIENCE_BOUNDARY_COPY)];
}

function assertFalse(value: boolean, message: string) {
  if (value) {
    throw new ResearchScienceDataQualityError(message);
  }
}

export function assertTrustedResearchScienceDashboard(payload: ResearchScienceDashboardResponse) {
  assertFalse(payload.fake_metrics !== false, 'Research Science dashboard could not be verified: fake_metrics=true');
  assertFalse(payload.provider_integration_enabled, 'Research Science dashboard could not be verified: provider_integration_enabled=true');
  assertFalse(payload.external_database_sync_enabled, 'Research Science dashboard could not be verified: external_database_sync_enabled=true');
  assertFalse(payload.official_verification_enabled, 'Research Science dashboard could not be verified: official_verification_enabled=true');
  assertFalse(payload.hidden_score_present, 'Research Science dashboard could not be verified: hidden_score_present=true');
  if (payload.master_matrix_commit !== MASTER_MATRIX_COMMIT) {
    throw new ResearchScienceDataQualityError(`Research Science dashboard matrix commit mismatch: expected ${MASTER_MATRIX_COMMIT}, received ${payload.master_matrix_commit}`);
  }
  if (payload.master_matrix_rows !== MASTER_MATRIX_ROW_COUNT) {
    throw new ResearchScienceDataQualityError(`Research Science dashboard matrix row count mismatch: expected ${MASTER_MATRIX_ROW_COUNT}, received ${payload.master_matrix_rows}`);
  }
  if (payload.data_source !== EXPECTED_DATA_SOURCE) {
    throw new ResearchScienceDataQualityError(`Research Science dashboard data source mismatch: expected ${EXPECTED_DATA_SOURCE}, received ${payload.data_source}`);
  }
}

export function assertTrustedResearchScienceHealth(payload: ResearchScienceHealthResponse) {
  assertFalse(payload.fake_metrics !== false, 'Research Science health payload could not be verified: fake_metrics=true');
  assertFalse(payload.provider_integration_enabled, 'Research Science health payload could not be verified: provider_integration_enabled=true');
  assertFalse(payload.external_database_sync_enabled, 'Research Science health payload could not be verified: external_database_sync_enabled=true');
  assertFalse(payload.official_verification_enabled, 'Research Science health payload could not be verified: official_verification_enabled=true');
  assertFalse(payload.hidden_score_present, 'Research Science health payload could not be verified: hidden_score_present=true');
  if (payload.route_count !== RESEARCH_SCIENCE_BACKEND_ROUTE_COUNT) {
    throw new ResearchScienceDataQualityError(`Research Science health route count mismatch: expected ${RESEARCH_SCIENCE_BACKEND_ROUTE_COUNT}, received ${payload.route_count}`);
  }
  if (payload.table_count !== RESEARCH_SCIENCE_TABLE_COUNT) {
    throw new ResearchScienceDataQualityError(`Research Science health table count mismatch: expected ${RESEARCH_SCIENCE_TABLE_COUNT}, received ${payload.table_count}`);
  }
}

export function assertTrustedResearchScienceMatrixSummary(payload: ResearchScienceMatrixSummaryResponse) {
  if (payload.master_matrix_commit !== MASTER_MATRIX_COMMIT) {
    throw new ResearchScienceDataQualityError(`Research Science matrix commit mismatch: expected ${MASTER_MATRIX_COMMIT}, received ${payload.master_matrix_commit}`);
  }
  if (payload.master_matrix_rows !== MASTER_MATRIX_ROW_COUNT) {
    throw new ResearchScienceDataQualityError(`Research Science matrix row count mismatch: expected ${MASTER_MATRIX_ROW_COUNT}, received ${payload.master_matrix_rows}`);
  }
  if (payload.table_count_expected !== RESEARCH_SCIENCE_TABLE_COUNT) {
    throw new ResearchScienceDataQualityError(`Research Science matrix table count mismatch: expected ${RESEARCH_SCIENCE_TABLE_COUNT}, received ${payload.table_count_expected}`);
  }
}