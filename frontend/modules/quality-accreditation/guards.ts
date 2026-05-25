import type { Permission } from '@/shared/config/permissions';
import { PERMISSIONS } from '@/shared/config/permissions';
import {
  DATA_SOURCE,
  QUALITY_ACCREDITATION_BACKEND_PERMISSION_COUNT,
  QUALITY_ACCREDITATION_BACKEND_ROUTE_COUNT,
  QUALITY_ACCREDITATION_BACKEND_TABLE_COUNT,
  QUALITY_ACCREDITATION_FORBIDDEN_ACTIONS,
  QUALITY_ACCREDITATION_LIMITATIONS,
  SOURCE_BACKEND_SPEC_COMMIT,
  SOURCE_PRODUCT_MAP_COMMIT,
  SOURCE_VERTICAL_SELECTION_COMMIT,
} from './constants';
import {
  QUALITY_ACCREDITATION_BOUNDARY_COPY,
  QUALITY_ACCREDITATION_PAGE_BOUNDARY_LABELS,
  type QualityAccreditationPageKey,
} from './boundaryLabels';
import type {
  QualityAccreditationDashboardResponse,
  QualityAccreditationHealthResponse,
  QualityAccreditationMatrixSummaryResponse,
  QualityAccreditationOverviewResponse,
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

export class QualityAccreditationDataQualityError extends Error {}

export const QUALITY_ACCREDITATION_PERMISSIONS = {
  overviewRead: PERMISSIONS.QUALITY_ACCREDITATION_OVERVIEW_READ,
  dashboardRead: PERMISSIONS.QUALITY_ACCREDITATION_DASHBOARD_READ,
  healthRead: PERMISSIONS.QUALITY_ACCREDITATION_HEALTH_READ,
  matrixRead: PERMISSIONS.QUALITY_ACCREDITATION_MATRIX_READ,
  limitationsRead: PERMISSIONS.QUALITY_ACCREDITATION_LIMITATIONS_READ,
  standardsRead: PERMISSIONS.QUALITY_ACCREDITATION_STANDARDS_READ,
  standardsCreate: PERMISSIONS.QUALITY_ACCREDITATION_STANDARDS_CREATE,
  standardsUpdate: PERMISSIONS.QUALITY_ACCREDITATION_STANDARDS_UPDATE,
  criteriaRead: PERMISSIONS.QUALITY_ACCREDITATION_CRITERIA_READ,
  criteriaCreate: PERMISSIONS.QUALITY_ACCREDITATION_CRITERIA_CREATE,
  criteriaUpdate: PERMISSIONS.QUALITY_ACCREDITATION_CRITERIA_UPDATE,
  evidenceRead: PERMISSIONS.QUALITY_ACCREDITATION_EVIDENCE_READ,
  evidenceAttach: PERMISSIONS.QUALITY_ACCREDITATION_EVIDENCE_ATTACH,
  evidenceReview: PERMISSIONS.QUALITY_ACCREDITATION_EVIDENCE_REVIEW,
  evidenceLimitationsManage: PERMISSIONS.QUALITY_ACCREDITATION_EVIDENCE_LIMITATIONS_MANAGE,
  programReadinessRead: PERMISSIONS.QUALITY_ACCREDITATION_PROGRAM_READINESS_READ,
  programReadinessUpdate: PERMISSIONS.QUALITY_ACCREDITATION_PROGRAM_READINESS_UPDATE,
  institutionalReadinessRead: PERMISSIONS.QUALITY_ACCREDITATION_INSTITUTIONAL_READINESS_READ,
  institutionalReadinessUpdate: PERMISSIONS.QUALITY_ACCREDITATION_INSTITUTIONAL_READINESS_UPDATE,
  selfAssessmentRead: PERMISSIONS.QUALITY_ACCREDITATION_SELF_ASSESSMENT_READ,
  selfAssessmentCreate: PERMISSIONS.QUALITY_ACCREDITATION_SELF_ASSESSMENT_CREATE,
  selfAssessmentUpdate: PERMISSIONS.QUALITY_ACCREDITATION_SELF_ASSESSMENT_UPDATE,
  improvementPlansRead: PERMISSIONS.QUALITY_ACCREDITATION_IMPROVEMENT_PLANS_READ,
  improvementPlansCreate: PERMISSIONS.QUALITY_ACCREDITATION_IMPROVEMENT_PLANS_CREATE,
  improvementPlansUpdate: PERMISSIONS.QUALITY_ACCREDITATION_IMPROVEMENT_PLANS_UPDATE,
  internalAuditsRead: PERMISSIONS.QUALITY_ACCREDITATION_INTERNAL_AUDITS_READ,
  internalAuditsCreate: PERMISSIONS.QUALITY_ACCREDITATION_INTERNAL_AUDITS_CREATE,
  internalAuditsUpdate: PERMISSIONS.QUALITY_ACCREDITATION_INTERNAL_AUDITS_UPDATE,
  auditFindingsRead: PERMISSIONS.QUALITY_ACCREDITATION_AUDIT_FINDINGS_READ,
  auditFindingsUpdate: PERMISSIONS.QUALITY_ACCREDITATION_AUDIT_FINDINGS_UPDATE,
  programReviewRead: PERMISSIONS.QUALITY_ACCREDITATION_PROGRAM_REVIEW_READ,
  programReviewCreate: PERMISSIONS.QUALITY_ACCREDITATION_PROGRAM_REVIEW_CREATE,
  programReviewUpdate: PERMISSIONS.QUALITY_ACCREDITATION_PROGRAM_REVIEW_UPDATE,
  learningOutcomesRead: PERMISSIONS.QUALITY_ACCREDITATION_LEARNING_OUTCOMES_READ,
  feedbackRead: PERMISSIONS.QUALITY_ACCREDITATION_FEEDBACK_READ,
  feedbackMetadataCreate: PERMISSIONS.QUALITY_ACCREDITATION_FEEDBACK_METADATA_CREATE,
  committeeRead: PERMISSIONS.QUALITY_ACCREDITATION_COMMITTEE_READ,
  committeeUpdate: PERMISSIONS.QUALITY_ACCREDITATION_COMMITTEE_UPDATE,
  externalReviewRead: PERMISSIONS.QUALITY_ACCREDITATION_EXTERNAL_REVIEW_READ,
  externalReviewCreate: PERMISSIONS.QUALITY_ACCREDITATION_EXTERNAL_REVIEW_CREATE,
  externalReviewUpdate: PERMISSIONS.QUALITY_ACCREDITATION_EXTERNAL_REVIEW_UPDATE,
  gapAnalysisRead: PERMISSIONS.QUALITY_ACCREDITATION_GAP_ANALYSIS_READ,
  gapAnalysisUpdate: PERMISSIONS.QUALITY_ACCREDITATION_GAP_ANALYSIS_UPDATE,
  calendarRead: PERMISSIONS.QUALITY_ACCREDITATION_CALENDAR_READ,
  calendarUpdate: PERMISSIONS.QUALITY_ACCREDITATION_CALENDAR_UPDATE,
  riskRegisterRead: PERMISSIONS.QUALITY_ACCREDITATION_RISK_REGISTER_READ,
  riskRegisterUpdate: PERMISSIONS.QUALITY_ACCREDITATION_RISK_REGISTER_UPDATE,
  bridgesRead: PERMISSIONS.QUALITY_ACCREDITATION_BRIDGES_READ,
  bridgesCreate: PERMISSIONS.QUALITY_ACCREDITATION_BRIDGES_CREATE,
  bridgesUpdate: PERMISSIONS.QUALITY_ACCREDITATION_BRIDGES_UPDATE,
  brainSignalsRead: PERMISSIONS.QUALITY_ACCREDITATION_BRAIN_SIGNALS_READ,
  auditRead: PERMISSIONS.QUALITY_ACCREDITATION_AUDIT_READ,
  statusHistoryRead: PERMISSIONS.QUALITY_ACCREDITATION_STATUS_HISTORY_READ,
  adminRead: PERMISSIONS.QUALITY_ACCREDITATION_ADMIN_READ,
  adminConfigure: PERMISSIONS.QUALITY_ACCREDITATION_ADMIN_CONFIGURE,
} as const;

export function hasQualityAccreditationPermission(user: PermissionUser, permission: Permission) {
  return permissionSet(user).has(permission);
}

export function canReadQualityAccreditationOverview(user: PermissionUser) {
  return hasQualityAccreditationPermission(user, QUALITY_ACCREDITATION_PERMISSIONS.overviewRead);
}

export function canReadQualityAccreditationDashboard(user: PermissionUser) {
  return hasQualityAccreditationPermission(user, QUALITY_ACCREDITATION_PERMISSIONS.dashboardRead);
}

export function canReadQualityAccreditationHealth(user: PermissionUser) {
  return hasQualityAccreditationPermission(user, QUALITY_ACCREDITATION_PERMISSIONS.healthRead);
}

export function canReadQualityAccreditationMatrix(user: PermissionUser) {
  return hasQualityAccreditationPermission(user, QUALITY_ACCREDITATION_PERMISSIONS.matrixRead);
}

export function canReadQualityAccreditationLimitations(user: PermissionUser) {
  return hasQualityAccreditationPermission(user, QUALITY_ACCREDITATION_PERMISSIONS.limitationsRead);
}

export function canReadQualityStandards(user: PermissionUser) {
  return hasQualityAccreditationPermission(user, QUALITY_ACCREDITATION_PERMISSIONS.standardsRead);
}

export function canReadQualityEvidence(user: PermissionUser) {
  return hasQualityAccreditationPermission(user, QUALITY_ACCREDITATION_PERMISSIONS.evidenceRead);
}

export function canReadProgramReadiness(user: PermissionUser) {
  return hasQualityAccreditationPermission(user, QUALITY_ACCREDITATION_PERMISSIONS.programReadinessRead);
}

export function canReadInstitutionalReadiness(user: PermissionUser) {
  return hasQualityAccreditationPermission(user, QUALITY_ACCREDITATION_PERMISSIONS.institutionalReadinessRead);
}

export function canReadSelfAssessment(user: PermissionUser) {
  return hasQualityAccreditationPermission(user, QUALITY_ACCREDITATION_PERMISSIONS.selfAssessmentRead);
}

export function canReadImprovementPlans(user: PermissionUser) {
  return hasQualityAccreditationPermission(user, QUALITY_ACCREDITATION_PERMISSIONS.improvementPlansRead);
}

export function canReadInternalAudits(user: PermissionUser) {
  return hasQualityAccreditationPermission(user, QUALITY_ACCREDITATION_PERMISSIONS.internalAuditsRead);
}

export function canReadProgramReview(user: PermissionUser) {
  return hasQualityAccreditationPermission(user, QUALITY_ACCREDITATION_PERMISSIONS.programReviewRead);
}

export function canReadLearningOutcomes(user: PermissionUser) {
  return hasQualityAccreditationPermission(user, QUALITY_ACCREDITATION_PERMISSIONS.learningOutcomesRead);
}

export function canReadStakeholderFeedback(user: PermissionUser) {
  return hasQualityAccreditationPermission(user, QUALITY_ACCREDITATION_PERMISSIONS.feedbackRead);
}

export function canReadCommittee(user: PermissionUser) {
  return hasQualityAccreditationPermission(user, QUALITY_ACCREDITATION_PERMISSIONS.committeeRead);
}

export function canReadExternalReview(user: PermissionUser) {
  return hasQualityAccreditationPermission(user, QUALITY_ACCREDITATION_PERMISSIONS.externalReviewRead);
}

export function canReadGapAnalysis(user: PermissionUser) {
  return hasQualityAccreditationPermission(user, QUALITY_ACCREDITATION_PERMISSIONS.gapAnalysisRead);
}

export function canReadQualityCalendar(user: PermissionUser) {
  return hasQualityAccreditationPermission(user, QUALITY_ACCREDITATION_PERMISSIONS.calendarRead);
}

export function canReadQualityRiskRegister(user: PermissionUser) {
  return hasQualityAccreditationPermission(user, QUALITY_ACCREDITATION_PERMISSIONS.riskRegisterRead);
}

export function canReadQualityBridges(user: PermissionUser) {
  return hasQualityAccreditationPermission(user, QUALITY_ACCREDITATION_PERMISSIONS.bridgesRead);
}

export function canReadQualityBrainSignals(user: PermissionUser) {
  return hasQualityAccreditationPermission(user, QUALITY_ACCREDITATION_PERMISSIONS.brainSignalsRead);
}

export function canReadQualityAudit(user: PermissionUser) {
  return hasQualityAccreditationPermission(user, QUALITY_ACCREDITATION_PERMISSIONS.auditRead);
}

export function canReadQualityStatusHistory(user: PermissionUser) {
  return hasQualityAccreditationPermission(user, QUALITY_ACCREDITATION_PERMISSIONS.statusHistoryRead);
}

export function canCreateQualityFramework(user: PermissionUser) {
  return hasQualityAccreditationPermission(user, QUALITY_ACCREDITATION_PERMISSIONS.standardsCreate);
}

export function canUpdateQualityFramework(user: PermissionUser) {
  return hasQualityAccreditationPermission(user, QUALITY_ACCREDITATION_PERMISSIONS.standardsUpdate);
}

export function canCreateAccreditationStandard(user: PermissionUser) {
  return hasQualityAccreditationPermission(user, QUALITY_ACCREDITATION_PERMISSIONS.standardsCreate);
}

export function canUpdateAccreditationStandard(user: PermissionUser) {
  return hasQualityAccreditationPermission(user, QUALITY_ACCREDITATION_PERMISSIONS.standardsUpdate);
}

export function canAttachQualityEvidence(user: PermissionUser) {
  return hasQualityAccreditationPermission(user, QUALITY_ACCREDITATION_PERMISSIONS.evidenceAttach);
}

export function canReviewQualityEvidence(user: PermissionUser) {
  return hasQualityAccreditationPermission(user, QUALITY_ACCREDITATION_PERMISSIONS.evidenceReview);
}

export function canUpdateProgramReadiness(user: PermissionUser) {
  return hasQualityAccreditationPermission(user, QUALITY_ACCREDITATION_PERMISSIONS.programReadinessUpdate);
}

export function canUpdateInstitutionalReadiness(user: PermissionUser) {
  return hasQualityAccreditationPermission(user, QUALITY_ACCREDITATION_PERMISSIONS.institutionalReadinessUpdate);
}

export function canCreateSelfAssessment(user: PermissionUser) {
  return hasQualityAccreditationPermission(user, QUALITY_ACCREDITATION_PERMISSIONS.selfAssessmentCreate);
}

export function canUpdateSelfAssessment(user: PermissionUser) {
  return hasQualityAccreditationPermission(user, QUALITY_ACCREDITATION_PERMISSIONS.selfAssessmentUpdate);
}

export function canCreateImprovementPlan(user: PermissionUser) {
  return hasQualityAccreditationPermission(user, QUALITY_ACCREDITATION_PERMISSIONS.improvementPlansCreate);
}

export function canUpdateImprovementPlan(user: PermissionUser) {
  return hasQualityAccreditationPermission(user, QUALITY_ACCREDITATION_PERMISSIONS.improvementPlansUpdate);
}

export function canCreateInternalAudit(user: PermissionUser) {
  return hasQualityAccreditationPermission(user, QUALITY_ACCREDITATION_PERMISSIONS.internalAuditsCreate);
}

export function canUpdateInternalAudit(user: PermissionUser) {
  return hasQualityAccreditationPermission(user, QUALITY_ACCREDITATION_PERMISSIONS.internalAuditsUpdate);
}

export function canCreateProgramReview(user: PermissionUser) {
  return hasQualityAccreditationPermission(user, QUALITY_ACCREDITATION_PERMISSIONS.programReviewCreate);
}

export function canUpdateProgramReview(user: PermissionUser) {
  return hasQualityAccreditationPermission(user, QUALITY_ACCREDITATION_PERMISSIONS.programReviewUpdate);
}

export function canCreateCommitteeWorkflow(user: PermissionUser) {
  return hasQualityAccreditationPermission(user, QUALITY_ACCREDITATION_PERMISSIONS.committeeUpdate);
}

export function canUpdateCommitteeWorkflow(user: PermissionUser) {
  return hasQualityAccreditationPermission(user, QUALITY_ACCREDITATION_PERMISSIONS.committeeUpdate);
}

export function canCreateExternalReview(user: PermissionUser) {
  return hasQualityAccreditationPermission(user, QUALITY_ACCREDITATION_PERMISSIONS.externalReviewCreate);
}

export function canUpdateExternalReview(user: PermissionUser) {
  return hasQualityAccreditationPermission(user, QUALITY_ACCREDITATION_PERMISSIONS.externalReviewUpdate);
}

export function canUpdateGapAnalysis(user: PermissionUser) {
  return hasQualityAccreditationPermission(user, QUALITY_ACCREDITATION_PERMISSIONS.gapAnalysisUpdate);
}

export function canUpdateQualityCalendar(user: PermissionUser) {
  return hasQualityAccreditationPermission(user, QUALITY_ACCREDITATION_PERMISSIONS.calendarUpdate);
}

export function canUpdateQualityRisk(user: PermissionUser) {
  return hasQualityAccreditationPermission(user, QUALITY_ACCREDITATION_PERMISSIONS.riskRegisterUpdate);
}

export function canCreateQualityBridge(user: PermissionUser) {
  return hasQualityAccreditationPermission(user, QUALITY_ACCREDITATION_PERMISSIONS.bridgesCreate);
}

export function isForbiddenQualityAccreditationAction(action: string) {
  return (QUALITY_ACCREDITATION_FORBIDDEN_ACTIONS as readonly string[]).includes(action);
}

export function getQualityAccreditationBoundaryLabels(page: QualityAccreditationPageKey | string) {
  return [...(QUALITY_ACCREDITATION_PAGE_BOUNDARY_LABELS[page as QualityAccreditationPageKey] ?? QUALITY_ACCREDITATION_BOUNDARY_COPY)];
}

function assertFalse(value: boolean, message: string) {
  if (value) {
    throw new QualityAccreditationDataQualityError(message);
  }
}

export function assertTrustedQualityAccreditationOverview(payload: QualityAccreditationOverviewResponse) {
  if (payload.table_count !== QUALITY_ACCREDITATION_BACKEND_TABLE_COUNT) {
    throw new QualityAccreditationDataQualityError(
      `Quality / Accreditation overview table count mismatch: expected ${QUALITY_ACCREDITATION_BACKEND_TABLE_COUNT}, received ${payload.table_count}`,
    );
  }
  if (payload.route_count !== QUALITY_ACCREDITATION_BACKEND_ROUTE_COUNT) {
    throw new QualityAccreditationDataQualityError(
      `Quality / Accreditation overview route count mismatch: expected ${QUALITY_ACCREDITATION_BACKEND_ROUTE_COUNT}, received ${payload.route_count}`,
    );
  }
}

export function assertTrustedQualityAccreditationDashboard(payload: QualityAccreditationDashboardResponse) {
  assertFalse(payload.fake_metrics !== false, 'Quality / Accreditation dashboard could not be verified: fake_metrics=true');
  assertFalse(payload.fake_evidence !== false, 'Quality / Accreditation dashboard could not be verified: fake_evidence=true');
  assertFalse(payload.provider_integration_enabled, 'Quality / Accreditation dashboard could not be verified: provider_integration_enabled=true');
  assertFalse(payload.external_database_sync_enabled, 'Quality / Accreditation dashboard could not be verified: external_database_sync_enabled=true');
  assertFalse(payload.official_accreditation_approval_enabled, 'Quality / Accreditation dashboard could not be verified: official_accreditation_approval_enabled=true');
  assertFalse(payload.official_ministry_submission_enabled, 'Quality / Accreditation dashboard could not be verified: official_ministry_submission_enabled=true');
  assertFalse(payload.official_ranking_claim_enabled, 'Quality / Accreditation dashboard could not be verified: official_ranking_claim_enabled=true');
  assertFalse(payload.automatic_accreditation_decision_enabled, 'Quality / Accreditation dashboard could not be verified: automatic_accreditation_decision_enabled=true');
  assertFalse(payload.hidden_score_present, 'Quality / Accreditation dashboard could not be verified: hidden_score_present=true');
  if (payload.data_source !== DATA_SOURCE) {
    throw new QualityAccreditationDataQualityError(`Quality / Accreditation dashboard data source mismatch: expected ${DATA_SOURCE}, received ${payload.data_source}`);
  }
  if (payload.source_product_map_commit !== SOURCE_PRODUCT_MAP_COMMIT) {
    throw new QualityAccreditationDataQualityError(
      `Quality / Accreditation dashboard product map mismatch: expected ${SOURCE_PRODUCT_MAP_COMMIT}, received ${payload.source_product_map_commit}`,
    );
  }
  if (payload.source_vertical_selection_commit !== SOURCE_VERTICAL_SELECTION_COMMIT) {
    throw new QualityAccreditationDataQualityError(
      `Quality / Accreditation dashboard vertical selection mismatch: expected ${SOURCE_VERTICAL_SELECTION_COMMIT}, received ${payload.source_vertical_selection_commit}`,
    );
  }
}

export function assertTrustedQualityAccreditationHealth(payload: QualityAccreditationHealthResponse) {
  assertFalse(payload.fake_metrics !== false, 'Quality / Accreditation health payload could not be verified: fake_metrics=true');
  assertFalse(payload.provider_integration_enabled, 'Quality / Accreditation health payload could not be verified: provider_integration_enabled=true');
  assertFalse(payload.external_database_sync_enabled, 'Quality / Accreditation health payload could not be verified: external_database_sync_enabled=true');
  assertFalse(payload.official_accreditation_approval_enabled, 'Quality / Accreditation health payload could not be verified: official_accreditation_approval_enabled=true');
  assertFalse(payload.official_ministry_submission_enabled, 'Quality / Accreditation health payload could not be verified: official_ministry_submission_enabled=true');
  assertFalse(payload.official_ranking_claim_enabled, 'Quality / Accreditation health payload could not be verified: official_ranking_claim_enabled=true');
  assertFalse(payload.hidden_score_present, 'Quality / Accreditation health payload could not be verified: hidden_score_present=true');
  if (payload.route_count !== QUALITY_ACCREDITATION_BACKEND_ROUTE_COUNT) {
    throw new QualityAccreditationDataQualityError(
      `Quality / Accreditation health route count mismatch: expected ${QUALITY_ACCREDITATION_BACKEND_ROUTE_COUNT}, received ${payload.route_count}`,
    );
  }
  if (payload.table_count !== QUALITY_ACCREDITATION_BACKEND_TABLE_COUNT) {
    throw new QualityAccreditationDataQualityError(
      `Quality / Accreditation health table count mismatch: expected ${QUALITY_ACCREDITATION_BACKEND_TABLE_COUNT}, received ${payload.table_count}`,
    );
  }
}

export function assertTrustedQualityAccreditationMatrixSummary(payload: QualityAccreditationMatrixSummaryResponse) {
  if (payload.source_spec_commit !== SOURCE_BACKEND_SPEC_COMMIT) {
    throw new QualityAccreditationDataQualityError(
      `Quality / Accreditation matrix spec commit mismatch: expected ${SOURCE_BACKEND_SPEC_COMMIT}, received ${payload.source_spec_commit}`,
    );
  }
  if (payload.source_product_map_commit !== SOURCE_PRODUCT_MAP_COMMIT) {
    throw new QualityAccreditationDataQualityError(
      `Quality / Accreditation matrix product map mismatch: expected ${SOURCE_PRODUCT_MAP_COMMIT}, received ${payload.source_product_map_commit}`,
    );
  }
  if (payload.source_vertical_selection_commit !== SOURCE_VERTICAL_SELECTION_COMMIT) {
    throw new QualityAccreditationDataQualityError(
      `Quality / Accreditation matrix vertical selection mismatch: expected ${SOURCE_VERTICAL_SELECTION_COMMIT}, received ${payload.source_vertical_selection_commit}`,
    );
  }
  if (payload.table_count_expected !== QUALITY_ACCREDITATION_BACKEND_TABLE_COUNT) {
    throw new QualityAccreditationDataQualityError(
      `Quality / Accreditation matrix table count mismatch: expected ${QUALITY_ACCREDITATION_BACKEND_TABLE_COUNT}, received ${payload.table_count_expected}`,
    );
  }
  if (payload.permission_count_expected !== QUALITY_ACCREDITATION_BACKEND_PERMISSION_COUNT) {
    throw new QualityAccreditationDataQualityError(
      `Quality / Accreditation matrix permission count mismatch: expected ${QUALITY_ACCREDITATION_BACKEND_PERMISSION_COUNT}, received ${payload.permission_count_expected}`,
    );
  }
}

export function getQualityAccreditationLimitations() {
  return [...QUALITY_ACCREDITATION_LIMITATIONS];
}