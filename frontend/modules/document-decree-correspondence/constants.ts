import type { Permission } from '@/shared/config/permissions';
import {
  DOCUMENT_DECREE_CORRESPONDENCE_BOUNDARY_LABELS,
  getDdcBoundaryLabels,
} from './boundaryLabels';
import type {
  DdcDashboardWidget,
  DdcRouteDefinition,
  DdcRouteKey,
  DdcSafetyFlags,
  DdcWorkflowDefinition,
} from './types';

export const DOCUMENT_DECREE_CORRESPONDENCE_MODULE = 'document-decree-correspondence';
export const DOCUMENT_DECREE_CORRESPONDENCE_ROUTE_FAMILY = '/console/document-decree-correspondence';
export const DOCUMENT_DECREE_CORRESPONDENCE_API_BASE = '/api/admin/document-decree-correspondence';
export const DOCUMENT_DECREE_CORRESPONDENCE_PLANNED_ROUTE_COUNT = 23;
export const DOCUMENT_DECREE_CORRESPONDENCE_BACKEND_ROUTE_COUNT = 53;
export const DOCUMENT_DECREE_CORRESPONDENCE_PERMISSION_COUNT = 50;
export const DOCUMENT_DECREE_CORRESPONDENCE_RUNTIME_MODE = 'METADATA_EVIDENCE_READINESS_AUDIT_ARCHIVE_HUMAN_REVIEW_ONLY';
export const DOCUMENT_DECREE_CORRESPONDENCE_SOURCE_BACKEND_RUNTIME_COMMIT = 'b9a6188';
export const DOCUMENT_DECREE_CORRESPONDENCE_SOURCE_BACKEND_B1_COMMIT = 'd483c59';
export const DOCUMENT_DECREE_CORRESPONDENCE_DATA_SOURCE = 'computed_from_document_decree_correspondence_metadata';

export const fakeDocuments = false;
export const fakeDecrees = false;
export const fakeSignatures = false;
export const fakeDeliveryConfirmations = false;
export const fakeArchiveLegalRecord = false;
export const officialLegalEffect = false;
export const externalSubmissionEnabled = false;
export const automaticRectorDecisionEnabled = false;
export const automaticDecreeApprovalEnabled = false;
export const automaticDocumentSigningEnabled = false;
export const hiddenScorePresent = false;
export const humanReviewRequired = true;

export const DOCUMENT_DECREE_CORRESPONDENCE_SAFETY_FLAGS: DdcSafetyFlags = {
  fake_documents: false,
  fake_decrees: false,
  fake_signatures: false,
  fake_delivery_confirmations: false,
  fake_archive_legal_record: false,
  official_legal_effect: false,
  external_submission_enabled: false,
  automatic_rector_decision_enabled: false,
  automatic_decree_approval_enabled: false,
  automatic_document_signing_enabled: false,
  hidden_score_present: false,
  human_review_required: true,
  incomplete_data: true,
  limitations: [
    'Metadata/evidence/readiness/audit/archive/human-review-only runtime.',
    'No legal effect, signing execution, automatic approvals, external submission, or hidden score surfaces are implemented.',
  ],
};

export const DOCUMENT_DECREE_CORRESPONDENCE_PERMISSION_VALUES = {
  overviewRead: 'document_decree_correspondence.overview.read' as Permission,
  readinessRead: 'document_decree_correspondence.readiness.read' as Permission,
  limitationsRead: 'document_decree_correspondence.limitations.read' as Permission,
  dashboardRead: 'document_decree_correspondence.dashboard.read' as Permission,
  documentsRead: 'document_decree_correspondence.documents.read' as Permission,
  documentIntakeRead: 'document_decree_correspondence.document_intake.read' as Permission,
  documentIntakeManage: 'document_decree_correspondence.document_intake.manage' as Permission,
  documentRegistrationManage: 'document_decree_correspondence.document_registration.manage' as Permission,
  documentRoutingRead: 'document_decree_correspondence.document_routing.read' as Permission,
  documentRoutingManage: 'document_decree_correspondence.document_routing.manage' as Permission,
  rectorResolutionsRead: 'document_decree_correspondence.rector_resolutions.read' as Permission,
  rectorResolutionsMetadata: 'document_decree_correspondence.rector_resolutions.metadata' as Permission,
  decreesRead: 'document_decree_correspondence.decrees.read' as Permission,
  decreesMetadata: 'document_decree_correspondence.decrees.metadata' as Permission,
  decreeDraftsRead: 'document_decree_correspondence.decree_drafts.read' as Permission,
  decreeDraftsManage: 'document_decree_correspondence.decree_drafts.manage' as Permission,
  incomingCorrespondenceRead: 'document_decree_correspondence.incoming_correspondence.read' as Permission,
  incomingCorrespondenceManage: 'document_decree_correspondence.incoming_correspondence.manage' as Permission,
  outgoingCorrespondenceRead: 'document_decree_correspondence.outgoing_correspondence.read' as Permission,
  outgoingCorrespondenceManage: 'document_decree_correspondence.outgoing_correspondence.manage' as Permission,
  templatesRead: 'document_decree_correspondence.templates.read' as Permission,
  templatesMetadata: 'document_decree_correspondence.templates.metadata' as Permission,
  committeeDecisionsRead: 'document_decree_correspondence.committee_decisions.read' as Permission,
  committeeDecisionsBridge: 'document_decree_correspondence.committee_decisions.bridge' as Permission,
  assignmentsRead: 'document_decree_correspondence.assignments.read' as Permission,
  assignmentsBridge: 'document_decree_correspondence.assignments.bridge' as Permission,
  executionControlRead: 'document_decree_correspondence.execution_control.read' as Permission,
  executionControlMetadata: 'document_decree_correspondence.execution_control.metadata' as Permission,
  slaDeadlinesRead: 'document_decree_correspondence.sla_deadlines.read' as Permission,
  slaDeadlinesMetadata: 'document_decree_correspondence.sla_deadlines.metadata' as Permission,
  evidenceRead: 'document_decree_correspondence.evidence.read' as Permission,
  evidenceWrite: 'document_decree_correspondence.evidence.write' as Permission,
  attachmentsRead: 'document_decree_correspondence.attachments.read' as Permission,
  attachmentsMetadata: 'document_decree_correspondence.attachments.metadata' as Permission,
  auditRead: 'document_decree_correspondence.audit.read' as Permission,
  auditWrite: 'document_decree_correspondence.audit.write' as Permission,
  archiveRead: 'document_decree_correspondence.archive.read' as Permission,
  archiveReadiness: 'document_decree_correspondence.archive.readiness' as Permission,
  retentionRead: 'document_decree_correspondence.retention.read' as Permission,
  retentionMetadata: 'document_decree_correspondence.retention.metadata' as Permission,
  signatureReadinessRead: 'document_decree_correspondence.signature_readiness.read' as Permission,
  signatureReadinessEvidence: 'document_decree_correspondence.signature_readiness.evidence' as Permission,
  deliveryReadinessRead: 'document_decree_correspondence.delivery_readiness.read' as Permission,
  deliveryReadinessEvidence: 'document_decree_correspondence.delivery_readiness.evidence' as Permission,
  bridgesExecutiveRead: 'document_decree_correspondence.bridges.executive.read' as Permission,
  bridgesExecutiveWrite: 'document_decree_correspondence.bridges.executive.write' as Permission,
  bridgesAssignmentsRead: 'document_decree_correspondence.bridges.assignments.read' as Permission,
  bridgesAssignmentsWrite: 'document_decree_correspondence.bridges.assignments.write' as Permission,
  rolesRead: 'document_decree_correspondence.roles.read' as Permission,
  metadataRead: 'document_decree_correspondence.metadata.read' as Permission,
} as const;

function apiPath(path: string) {
  return `${DOCUMENT_DECREE_CORRESPONDENCE_API_BASE}${path}`;
}

function endpoint(method: 'GET' | 'POST', path: string) {
  return `${method} ${apiPath(path)}`;
}

function stateFromTitle(title: string) {
  return `${title} metadata is not populated yet. This runtime keeps incomplete data explicit and review-only.`;
}

function routeDefinition(
  key: DdcRouteKey,
  title: string,
  path: string,
  requiredPermission: Permission,
  backendEndpoints: string[],
  description: string,
  dashboardLike: boolean,
  sensitive: boolean,
): DdcRouteDefinition {
  return {
    key,
    title,
    path,
    requiredPermission,
    backendEndpoints,
    boundaryLabels: getDdcBoundaryLabels(key),
    description,
    dashboardLike,
    sensitive,
    humanReviewRequired: sensitive || key === 'limitations' || key === 'overview' || key === 'dashboard',
    emptyState: stateFromTitle(title),
    incompleteDataState: 'Incomplete data is expected and explicitly supported in this runtime.',
    permissionDeniedState: `This route is fail-closed and requires ${requiredPermission}.`,
  };
}

export const DOCUMENT_DECREE_CORRESPONDENCE_API_PATHS = {
  health: apiPath('/health'),
  overview: apiPath('/overview'),
  readiness: apiPath('/readiness'),
  limitations: apiPath('/limitations'),
  safetyBoundaries: apiPath('/safety-boundaries'),
  dashboard: apiPath('/dashboard'),
  documents: apiPath('/documents'),
  documentIntake: apiPath('/document-intake'),
  documentRegistration: apiPath('/document-registration'),
  documentRouting: apiPath('/document-routing'),
  rectorResolutions: apiPath('/rector-resolutions'),
  rectorResolutionsMetadata: apiPath('/rector-resolutions/metadata'),
  decrees: apiPath('/decrees'),
  decreesMetadata: apiPath('/decrees/metadata'),
  decreeDrafts: apiPath('/decree-drafts'),
  incomingCorrespondence: apiPath('/incoming-correspondence'),
  outgoingCorrespondence: apiPath('/outgoing-correspondence'),
  templates: apiPath('/templates'),
  templatesMetadata: apiPath('/templates/metadata'),
  committeeDecisions: apiPath('/committee-decisions'),
  committeeDecisionsBridge: apiPath('/committee-decisions/bridge'),
  assignments: apiPath('/assignments'),
  assignmentsBridge: apiPath('/assignments/bridge'),
  executionControl: apiPath('/execution-control'),
  executionControlMetadata: apiPath('/execution-control/metadata'),
  slaDeadlines: apiPath('/sla-deadlines'),
  evidence: apiPath('/evidence'),
  attachments: apiPath('/attachments'),
  attachmentsMetadata: apiPath('/attachments/metadata'),
  auditEvents: apiPath('/audit-events'),
  archive: apiPath('/archive'),
  archiveReadiness: apiPath('/archive/readiness'),
  retentionMetadata: apiPath('/retention/metadata'),
  signatureReadiness: apiPath('/signature-readiness'),
  signatureReadinessEvidence: apiPath('/signature-readiness/evidence'),
  deliveryReadiness: apiPath('/delivery-readiness'),
  deliveryReadinessEvidence: apiPath('/delivery-readiness/evidence'),
  bridgesExecutive: apiPath('/bridges/executive'),
  bridgesAssignments: apiPath('/bridges/assignments'),
  roles: apiPath('/roles'),
  permissions: apiPath('/permissions'),
  metadataContract: apiPath('/metadata-contract'),
} as const;

export const DOCUMENT_DECREE_CORRESPONDENCE_ROUTES: DdcRouteDefinition[] = [
  routeDefinition('overview', 'Document / Decree / Correspondence Suite', DOCUMENT_DECREE_CORRESPONDENCE_ROUTE_FAMILY, DOCUMENT_DECREE_CORRESPONDENCE_PERMISSION_VALUES.overviewRead, [endpoint('GET', '/overview'), endpoint('GET', '/readiness'), endpoint('GET', '/limitations')], 'Operational overview of document, decree, and correspondence metadata and boundaries.', true, true),
  routeDefinition('dashboard', 'Document Dashboard', `${DOCUMENT_DECREE_CORRESPONDENCE_ROUTE_FAMILY}/dashboard`, DOCUMENT_DECREE_CORRESPONDENCE_PERMISSION_VALUES.dashboardRead, [endpoint('GET', '/dashboard')], 'Dashboard visibility across intake, routing, decrees, correspondence, evidence, archive, and bridges.', true, true),
  routeDefinition('documents', 'Document Registration', `${DOCUMENT_DECREE_CORRESPONDENCE_ROUTE_FAMILY}/documents`, DOCUMENT_DECREE_CORRESPONDENCE_PERMISSION_VALUES.documentsRead, [endpoint('GET', '/documents'), endpoint('POST', '/document-registration')], 'Document registry metadata and references.', false, false),
  routeDefinition('intake', 'Document Intake', `${DOCUMENT_DECREE_CORRESPONDENCE_ROUTE_FAMILY}/intake`, DOCUMENT_DECREE_CORRESPONDENCE_PERMISSION_VALUES.documentIntakeRead, [endpoint('GET', '/document-intake'), endpoint('POST', '/document-intake')], 'Intake metadata capture under human review.', false, true),
  routeDefinition('routing', 'Document Routing', `${DOCUMENT_DECREE_CORRESPONDENCE_ROUTE_FAMILY}/routing`, DOCUMENT_DECREE_CORRESPONDENCE_PERMISSION_VALUES.documentRoutingRead, [endpoint('GET', '/document-routing'), endpoint('POST', '/document-routing')], 'Routing metadata and reviewer hop visibility.', false, true),
  routeDefinition('rector-resolutions', 'Rector Resolution Metadata', `${DOCUMENT_DECREE_CORRESPONDENCE_ROUTE_FAMILY}/rector-resolutions`, DOCUMENT_DECREE_CORRESPONDENCE_PERMISSION_VALUES.rectorResolutionsRead, [endpoint('GET', '/rector-resolutions'), endpoint('POST', '/rector-resolutions/metadata')], 'Rector resolution metadata only, no automatic decision.', false, true),
  routeDefinition('decrees', 'Decree Registry Metadata', `${DOCUMENT_DECREE_CORRESPONDENCE_ROUTE_FAMILY}/decrees`, DOCUMENT_DECREE_CORRESPONDENCE_PERMISSION_VALUES.decreesRead, [endpoint('GET', '/decrees'), endpoint('POST', '/decrees/metadata')], 'Decree registry metadata only, no legal effect.', false, true),
  routeDefinition('decree-drafts', 'Decree Drafts', `${DOCUMENT_DECREE_CORRESPONDENCE_ROUTE_FAMILY}/decree-drafts`, DOCUMENT_DECREE_CORRESPONDENCE_PERMISSION_VALUES.decreeDraftsRead, [endpoint('GET', '/decree-drafts'), endpoint('POST', '/decree-drafts')], 'Draft metadata and versions under review.', false, true),
  routeDefinition('incoming', 'Incoming Correspondence', `${DOCUMENT_DECREE_CORRESPONDENCE_ROUTE_FAMILY}/incoming`, DOCUMENT_DECREE_CORRESPONDENCE_PERMISSION_VALUES.incomingCorrespondenceRead, [endpoint('GET', '/incoming-correspondence'), endpoint('POST', '/incoming-correspondence')], 'Incoming correspondence metadata references.', false, false),
  routeDefinition('outgoing', 'Outgoing Correspondence', `${DOCUMENT_DECREE_CORRESPONDENCE_ROUTE_FAMILY}/outgoing`, DOCUMENT_DECREE_CORRESPONDENCE_PERMISSION_VALUES.outgoingCorrespondenceRead, [endpoint('GET', '/outgoing-correspondence'), endpoint('POST', '/outgoing-correspondence')], 'Outgoing correspondence metadata without delivery execution.', false, true),
  routeDefinition('templates', 'Template Metadata', `${DOCUMENT_DECREE_CORRESPONDENCE_ROUTE_FAMILY}/templates`, DOCUMENT_DECREE_CORRESPONDENCE_PERMISSION_VALUES.templatesRead, [endpoint('GET', '/templates'), endpoint('POST', '/templates/metadata')], 'Template metadata and review notes.', false, true),
  routeDefinition('committee-decisions', 'Committee Decision Bridges', `${DOCUMENT_DECREE_CORRESPONDENCE_ROUTE_FAMILY}/committee-decisions`, DOCUMENT_DECREE_CORRESPONDENCE_PERMISSION_VALUES.committeeDecisionsRead, [endpoint('GET', '/committee-decisions'), endpoint('POST', '/committee-decisions/bridge')], 'Committee decision bridge metadata.', false, true),
  routeDefinition('assignments', 'Assignment Bridges', `${DOCUMENT_DECREE_CORRESPONDENCE_ROUTE_FAMILY}/assignments`, DOCUMENT_DECREE_CORRESPONDENCE_PERMISSION_VALUES.assignmentsRead, [endpoint('GET', '/assignments'), endpoint('POST', '/assignments/bridge')], 'Assignment bridge metadata and visibility.', false, true),
  routeDefinition('execution-control', 'Execution Control Metadata', `${DOCUMENT_DECREE_CORRESPONDENCE_ROUTE_FAMILY}/execution-control`, DOCUMENT_DECREE_CORRESPONDENCE_PERMISSION_VALUES.executionControlRead, [endpoint('GET', '/execution-control'), endpoint('POST', '/execution-control/metadata')], 'Execution-control metadata without automatic actions.', false, true),
  routeDefinition('sla-deadlines', 'SLA Deadlines', `${DOCUMENT_DECREE_CORRESPONDENCE_ROUTE_FAMILY}/sla-deadlines`, DOCUMENT_DECREE_CORRESPONDENCE_PERMISSION_VALUES.slaDeadlinesRead, [endpoint('GET', '/sla-deadlines'), endpoint('POST', '/sla-deadlines')], 'SLA deadline metadata and overdue explanation.', false, true),
  routeDefinition('evidence', 'Evidence Items', `${DOCUMENT_DECREE_CORRESPONDENCE_ROUTE_FAMILY}/evidence`, DOCUMENT_DECREE_CORRESPONDENCE_PERMISSION_VALUES.evidenceRead, [endpoint('GET', '/evidence'), endpoint('POST', '/evidence')], 'Evidence metadata records only.', false, true),
  routeDefinition('attachments', 'Attachment Metadata', `${DOCUMENT_DECREE_CORRESPONDENCE_ROUTE_FAMILY}/attachments`, DOCUMENT_DECREE_CORRESPONDENCE_PERMISSION_VALUES.attachmentsRead, [endpoint('GET', '/attachments'), endpoint('POST', '/attachments/metadata')], 'Attachment pointers and metadata only.', false, false),
  routeDefinition('audit', 'Audit Events', `${DOCUMENT_DECREE_CORRESPONDENCE_ROUTE_FAMILY}/audit`, DOCUMENT_DECREE_CORRESPONDENCE_PERMISSION_VALUES.auditRead, [endpoint('GET', '/audit-events'), endpoint('POST', '/audit-events')], 'Audit trail records and actor visibility.', false, true),
  routeDefinition('archive', 'Archive Readiness', `${DOCUMENT_DECREE_CORRESPONDENCE_ROUTE_FAMILY}/archive`, DOCUMENT_DECREE_CORRESPONDENCE_PERMISSION_VALUES.archiveRead, [endpoint('GET', '/archive'), endpoint('POST', '/archive/readiness'), endpoint('POST', '/retention/metadata')], 'Archive and retention readiness metadata, non-legal.', false, true),
  routeDefinition('signature-readiness', 'Signature Readiness', `${DOCUMENT_DECREE_CORRESPONDENCE_ROUTE_FAMILY}/signature-readiness`, DOCUMENT_DECREE_CORRESPONDENCE_PERMISSION_VALUES.signatureReadinessRead, [endpoint('GET', '/signature-readiness'), endpoint('POST', '/signature-readiness/evidence')], 'Signature readiness only, no signing action.', false, true),
  routeDefinition('delivery-readiness', 'Delivery Readiness', `${DOCUMENT_DECREE_CORRESPONDENCE_ROUTE_FAMILY}/delivery-readiness`, DOCUMENT_DECREE_CORRESPONDENCE_PERMISSION_VALUES.deliveryReadinessRead, [endpoint('GET', '/delivery-readiness'), endpoint('POST', '/delivery-readiness/evidence')], 'Delivery readiness only, no external dispatch execution.', false, true),
  routeDefinition('bridges', 'Bridge Visibility', `${DOCUMENT_DECREE_CORRESPONDENCE_ROUTE_FAMILY}/bridges`, DOCUMENT_DECREE_CORRESPONDENCE_PERMISSION_VALUES.bridgesExecutiveRead, [endpoint('GET', '/bridges/executive'), endpoint('GET', '/bridges/assignments'), endpoint('POST', '/bridges/executive'), endpoint('POST', '/bridges/assignments')], 'Read-only-first bridge surfaces across executive and assignments contexts.', false, false),
  routeDefinition('limitations', 'Limitations / Safety Boundaries', `${DOCUMENT_DECREE_CORRESPONDENCE_ROUTE_FAMILY}/limitations`, DOCUMENT_DECREE_CORRESPONDENCE_PERMISSION_VALUES.limitationsRead, [endpoint('GET', '/limitations'), endpoint('GET', '/safety-boundaries'), endpoint('GET', '/metadata-contract'), endpoint('POST', '/limitations')], 'Explicit boundaries and no-overclaim contract for frontend runtime.', false, true),
];

export const DOCUMENT_DECREE_CORRESPONDENCE_ROUTE_COUNT = DOCUMENT_DECREE_CORRESPONDENCE_ROUTES.length;

export const DOCUMENT_DECREE_CORRESPONDENCE_NAV_ITEMS = DOCUMENT_DECREE_CORRESPONDENCE_ROUTES.map((route) => ({
  key: route.key,
  title: route.title,
  href: route.path,
}));

export const DOCUMENT_DECREE_CORRESPONDENCE_DASHBOARD_WIDGETS: DdcDashboardWidget[] = [
  { key: 'document-intake', title: 'Document Intake', description: 'Intake metadata and review posture.', endpointRefs: [endpoint('GET', '/dashboard'), endpoint('GET', '/document-intake')], sourcePermission: DOCUMENT_DECREE_CORRESPONDENCE_PERMISSION_VALUES.documentIntakeRead, drilldownPath: `${DOCUMENT_DECREE_CORRESPONDENCE_ROUTE_FAMILY}/intake`, forbiddenAction: 'No fake document intake', boundaryLabels: [DOCUMENT_DECREE_CORRESPONDENCE_BOUNDARY_LABELS.noFakeOfficialDocuments], relatedRoutes: ['dashboard', 'intake'] },
  { key: 'document-routing', title: 'Document Routing', description: 'Routing metadata and assignment readiness.', endpointRefs: [endpoint('GET', '/dashboard'), endpoint('GET', '/document-routing')], sourcePermission: DOCUMENT_DECREE_CORRESPONDENCE_PERMISSION_VALUES.documentRoutingRead, drilldownPath: `${DOCUMENT_DECREE_CORRESPONDENCE_ROUTE_FAMILY}/routing`, forbiddenAction: 'No automatic routing decisions', boundaryLabels: [DOCUMENT_DECREE_CORRESPONDENCE_BOUNDARY_LABELS.humanReviewRequired], relatedRoutes: ['dashboard', 'routing'] },
  { key: 'decree-registry', title: 'Decree Registry', description: 'Decree metadata and review status.', endpointRefs: [endpoint('GET', '/dashboard'), endpoint('GET', '/decrees')], sourcePermission: DOCUMENT_DECREE_CORRESPONDENCE_PERMISSION_VALUES.decreesRead, drilldownPath: `${DOCUMENT_DECREE_CORRESPONDENCE_ROUTE_FAMILY}/decrees`, forbiddenAction: 'No official legal effect', boundaryLabels: [DOCUMENT_DECREE_CORRESPONDENCE_BOUNDARY_LABELS.noOfficialLegalEffect], relatedRoutes: ['dashboard', 'decrees'] },
  { key: 'decree-drafts', title: 'Decree Drafts', description: 'Draft metadata with manual review.', endpointRefs: [endpoint('GET', '/dashboard'), endpoint('GET', '/decree-drafts')], sourcePermission: DOCUMENT_DECREE_CORRESPONDENCE_PERMISSION_VALUES.decreeDraftsRead, drilldownPath: `${DOCUMENT_DECREE_CORRESPONDENCE_ROUTE_FAMILY}/decree-drafts`, forbiddenAction: 'No automatic decree approval', boundaryLabels: [DOCUMENT_DECREE_CORRESPONDENCE_BOUNDARY_LABELS.noAutomaticDecreeApproval], relatedRoutes: ['dashboard', 'decree-drafts'] },
  { key: 'correspondence-stream', title: 'Correspondence Streams', description: 'Incoming/outgoing correspondence metadata.', endpointRefs: [endpoint('GET', '/incoming-correspondence'), endpoint('GET', '/outgoing-correspondence')], sourcePermission: DOCUMENT_DECREE_CORRESPONDENCE_PERMISSION_VALUES.incomingCorrespondenceRead, drilldownPath: `${DOCUMENT_DECREE_CORRESPONDENCE_ROUTE_FAMILY}/incoming`, forbiddenAction: 'No external delivery execution', boundaryLabels: [DOCUMENT_DECREE_CORRESPONDENCE_BOUNDARY_LABELS.noExternalMinistrySubmission], relatedRoutes: ['dashboard', 'incoming', 'outgoing'] },
  { key: 'template-governance', title: 'Template Governance', description: 'Template metadata and controls.', endpointRefs: [endpoint('GET', '/templates')], sourcePermission: DOCUMENT_DECREE_CORRESPONDENCE_PERMISSION_VALUES.templatesRead, drilldownPath: `${DOCUMENT_DECREE_CORRESPONDENCE_ROUTE_FAMILY}/templates`, forbiddenAction: 'No hidden score-based template ranking', boundaryLabels: [DOCUMENT_DECREE_CORRESPONDENCE_BOUNDARY_LABELS.noHiddenStaffDepartmentScore], relatedRoutes: ['dashboard', 'templates'] },
  { key: 'audit-evidence', title: 'Audit / Evidence', description: 'Audit and evidence insert-only posture.', endpointRefs: [endpoint('GET', '/audit-events'), endpoint('GET', '/evidence')], sourcePermission: DOCUMENT_DECREE_CORRESPONDENCE_PERMISSION_VALUES.auditRead, drilldownPath: `${DOCUMENT_DECREE_CORRESPONDENCE_ROUTE_FAMILY}/audit`, forbiddenAction: 'No legal archive confirmation execution', boundaryLabels: [DOCUMENT_DECREE_CORRESPONDENCE_BOUNDARY_LABELS.humanReviewRequired], relatedRoutes: ['dashboard', 'audit', 'evidence'] },
  { key: 'archive-retention', title: 'Archive / Retention Readiness', description: 'Archive and retention readiness visibility.', endpointRefs: [endpoint('GET', '/archive')], sourcePermission: DOCUMENT_DECREE_CORRESPONDENCE_PERMISSION_VALUES.archiveRead, drilldownPath: `${DOCUMENT_DECREE_CORRESPONDENCE_ROUTE_FAMILY}/archive`, forbiddenAction: 'No legal-effect archive certification', boundaryLabels: [DOCUMENT_DECREE_CORRESPONDENCE_BOUNDARY_LABELS.archiveReadinessOnly], relatedRoutes: ['dashboard', 'archive'] },
  { key: 'signature-readiness', title: 'Signature Readiness', description: 'Readiness evidence without signing.', endpointRefs: [endpoint('GET', '/signature-readiness')], sourcePermission: DOCUMENT_DECREE_CORRESPONDENCE_PERMISSION_VALUES.signatureReadinessRead, drilldownPath: `${DOCUMENT_DECREE_CORRESPONDENCE_ROUTE_FAMILY}/signature-readiness`, forbiddenAction: 'No document signing action', boundaryLabels: [DOCUMENT_DECREE_CORRESPONDENCE_BOUNDARY_LABELS.signatureReadinessOnly], relatedRoutes: ['dashboard', 'signature-readiness'] },
  { key: 'delivery-readiness', title: 'Delivery Readiness', description: 'Readiness evidence without dispatch.', endpointRefs: [endpoint('GET', '/delivery-readiness')], sourcePermission: DOCUMENT_DECREE_CORRESPONDENCE_PERMISSION_VALUES.deliveryReadinessRead, drilldownPath: `${DOCUMENT_DECREE_CORRESPONDENCE_ROUTE_FAMILY}/delivery-readiness`, forbiddenAction: 'No external ministry submission execution', boundaryLabels: [DOCUMENT_DECREE_CORRESPONDENCE_BOUNDARY_LABELS.deliveryReadinessOnly], relatedRoutes: ['dashboard', 'delivery-readiness'] },
  { key: 'bridge-visibility', title: 'Bridge Visibility', description: 'Executive and assignment bridge summaries.', endpointRefs: [endpoint('GET', '/bridges/executive'), endpoint('GET', '/bridges/assignments')], sourcePermission: DOCUMENT_DECREE_CORRESPONDENCE_PERMISSION_VALUES.bridgesExecutiveRead, drilldownPath: `${DOCUMENT_DECREE_CORRESPONDENCE_ROUTE_FAMILY}/bridges`, forbiddenAction: 'No cross-module mutation', boundaryLabels: [DOCUMENT_DECREE_CORRESPONDENCE_BOUNDARY_LABELS.bridgeFirstReadOnlyFirst], relatedRoutes: ['dashboard', 'bridges'] },
  { key: 'limitations', title: 'Limitations / Boundaries', description: 'No-overclaim and safety boundaries.', endpointRefs: [endpoint('GET', '/limitations'), endpoint('GET', '/metadata-contract')], sourcePermission: DOCUMENT_DECREE_CORRESPONDENCE_PERMISSION_VALUES.limitationsRead, drilldownPath: `${DOCUMENT_DECREE_CORRESPONDENCE_ROUTE_FAMILY}/limitations`, forbiddenAction: 'No production/sales/GCC/L5/L6 claim', boundaryLabels: [DOCUMENT_DECREE_CORRESPONDENCE_BOUNDARY_LABELS.noProductionReadyClaim], relatedRoutes: ['dashboard', 'limitations', 'overview'] },
];

export const DOCUMENT_DECREE_CORRESPONDENCE_WORKFLOWS: DdcWorkflowDefinition[] = [
  { key: 'overview-readiness-boundaries', title: 'Overview -> Readiness -> Boundaries', description: 'Inspect suite overview and boundary posture together.', routeKeys: ['overview', 'limitations'], endpointRefs: [endpoint('GET', '/overview'), endpoint('GET', '/readiness'), endpoint('GET', '/limitations')], requiredPermissions: [DOCUMENT_DECREE_CORRESPONDENCE_PERMISSION_VALUES.overviewRead, DOCUMENT_DECREE_CORRESPONDENCE_PERMISSION_VALUES.limitationsRead], humanReviewPoint: 'Boundary banner marks the slice as human-review-only.', noOverclaimBoundary: 'No signing/legal effect/external submission controls.', futureE2eAssertion: 'Boundary labels render together on overview and limitations.' },
  { key: 'intake-to-routing', title: 'Intake -> Routing', description: 'Capture intake metadata and route for review.', routeKeys: ['intake', 'routing'], endpointRefs: [endpoint('GET', '/document-intake'), endpoint('POST', '/document-intake'), endpoint('GET', '/document-routing'), endpoint('POST', '/document-routing')], requiredPermissions: [DOCUMENT_DECREE_CORRESPONDENCE_PERMISSION_VALUES.documentIntakeRead, DOCUMENT_DECREE_CORRESPONDENCE_PERMISSION_VALUES.documentRoutingRead], humanReviewPoint: 'Routing remains review-only.', noOverclaimBoundary: 'No automatic rector/decree decisions.', futureE2eAssertion: 'Human review badge visible for intake/routing routes.' },
  { key: 'decree-metadata-lifecycle', title: 'Decree Registry -> Decree Drafts', description: 'Manage decree metadata and drafts under manual review.', routeKeys: ['decrees', 'decree-drafts'], endpointRefs: [endpoint('GET', '/decrees'), endpoint('POST', '/decrees/metadata'), endpoint('GET', '/decree-drafts'), endpoint('POST', '/decree-drafts')], requiredPermissions: [DOCUMENT_DECREE_CORRESPONDENCE_PERMISSION_VALUES.decreesRead, DOCUMENT_DECREE_CORRESPONDENCE_PERMISSION_VALUES.decreeDraftsRead], humanReviewPoint: 'No automatic decree approval or legal effect.', noOverclaimBoundary: 'No legal-effect issuance actions.', futureE2eAssertion: 'No approve/issue buttons on decree surfaces.' },
  { key: 'correspondence-flow', title: 'Incoming -> Outgoing Correspondence', description: 'Review correspondence metadata stream with non-execution delivery boundary.', routeKeys: ['incoming', 'outgoing'], endpointRefs: [endpoint('GET', '/incoming-correspondence'), endpoint('POST', '/incoming-correspondence'), endpoint('GET', '/outgoing-correspondence'), endpoint('POST', '/outgoing-correspondence')], requiredPermissions: [DOCUMENT_DECREE_CORRESPONDENCE_PERMISSION_VALUES.incomingCorrespondenceRead, DOCUMENT_DECREE_CORRESPONDENCE_PERMISSION_VALUES.outgoingCorrespondenceRead], humanReviewPoint: 'Outgoing remains metadata only.', noOverclaimBoundary: 'No external delivery execution.', futureE2eAssertion: 'No send external delivery controls rendered.' },
  { key: 'template-committee-assignment-bridge', title: 'Templates -> Committee -> Assignment Bridges', description: 'Track template and decision/assignment bridge metadata.', routeKeys: ['templates', 'committee-decisions', 'assignments'], endpointRefs: [endpoint('GET', '/templates'), endpoint('GET', '/committee-decisions'), endpoint('GET', '/assignments')], requiredPermissions: [DOCUMENT_DECREE_CORRESPONDENCE_PERMISSION_VALUES.templatesRead, DOCUMENT_DECREE_CORRESPONDENCE_PERMISSION_VALUES.committeeDecisionsRead, DOCUMENT_DECREE_CORRESPONDENCE_PERMISSION_VALUES.assignmentsRead], humanReviewPoint: 'Bridge outputs are read-only-first.', noOverclaimBoundary: 'No hidden scoring or autonomous bridge mutation.', futureE2eAssertion: 'Bridge cards rendered as read-only-first.' },
  { key: 'execution-sla-governance', title: 'Execution Control -> SLA Deadlines', description: 'Execution-control and SLA metadata remain manual and explicit.', routeKeys: ['execution-control', 'sla-deadlines'], endpointRefs: [endpoint('GET', '/execution-control'), endpoint('GET', '/sla-deadlines')], requiredPermissions: [DOCUMENT_DECREE_CORRESPONDENCE_PERMISSION_VALUES.executionControlRead, DOCUMENT_DECREE_CORRESPONDENCE_PERMISSION_VALUES.slaDeadlinesRead], humanReviewPoint: 'No automatic rector decision or decree approval.', noOverclaimBoundary: 'No autonomous execution controls.', futureE2eAssertion: 'No automatic control action labels rendered.' },
  { key: 'audit-evidence-attachments', title: 'Audit -> Evidence -> Attachments', description: 'Capture audit/evidence metadata and attachment references.', routeKeys: ['audit', 'evidence', 'attachments'], endpointRefs: [endpoint('GET', '/audit-events'), endpoint('GET', '/evidence'), endpoint('GET', '/attachments')], requiredPermissions: [DOCUMENT_DECREE_CORRESPONDENCE_PERMISSION_VALUES.auditRead, DOCUMENT_DECREE_CORRESPONDENCE_PERMISSION_VALUES.evidenceRead, DOCUMENT_DECREE_CORRESPONDENCE_PERMISSION_VALUES.attachmentsRead], humanReviewPoint: 'Audit and evidence remain metadata-only.', noOverclaimBoundary: 'No legal archive confirmation.', futureE2eAssertion: 'Audit/evidence tables rendered without execution actions.' },
  { key: 'archive-retention-readiness', title: 'Archive -> Retention Readiness', description: 'Maintain readiness and retention metadata without legal archive effect.', routeKeys: ['archive'], endpointRefs: [endpoint('GET', '/archive'), endpoint('POST', '/archive/readiness'), endpoint('POST', '/retention/metadata')], requiredPermissions: [DOCUMENT_DECREE_CORRESPONDENCE_PERMISSION_VALUES.archiveRead], humanReviewPoint: 'Archive readiness remains non-legal.', noOverclaimBoundary: 'No legal archive confirmation action.', futureE2eAssertion: 'Archive readiness label present and legal-effect labels absent.' },
  { key: 'signature-delivery-readiness', title: 'Signature -> Delivery Readiness', description: 'Maintain readiness evidence without signing or delivery execution.', routeKeys: ['signature-readiness', 'delivery-readiness'], endpointRefs: [endpoint('GET', '/signature-readiness'), endpoint('GET', '/delivery-readiness')], requiredPermissions: [DOCUMENT_DECREE_CORRESPONDENCE_PERMISSION_VALUES.signatureReadinessRead, DOCUMENT_DECREE_CORRESPONDENCE_PERMISSION_VALUES.deliveryReadinessRead], humanReviewPoint: 'Readiness evidence remains manual.', noOverclaimBoundary: 'No sign/send actions.', futureE2eAssertion: 'Signature/delivery badges visible with no execution controls.' },
  { key: 'bridge-views', title: 'Executive/Assignments Bridge Views', description: 'Inspect bridge outputs in read-only-first mode.', routeKeys: ['bridges'], endpointRefs: [endpoint('GET', '/bridges/executive'), endpoint('GET', '/bridges/assignments')], requiredPermissions: [DOCUMENT_DECREE_CORRESPONDENCE_PERMISSION_VALUES.bridgesExecutiveRead], humanReviewPoint: 'Bridge insights inform human review only.', noOverclaimBoundary: 'No cross-module mutation controls.', futureE2eAssertion: 'Bridge cards render with read-only language.' },
];
