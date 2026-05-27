import { expect, test, type Browser, type Page, type Route } from '@playwright/test';

const API_BASE = '/api/admin/document-decree-correspondence';
const BFF_BASE = '/api/bff/admin/document-decree-correspondence';
const BASE_URL = process.env.E2E_BASE_URL ?? 'https://nginx';

const FULL_PERMISSIONS = [
  'platform.admin.read',
  'document_decree_correspondence.overview.read',
  'document_decree_correspondence.readiness.read',
  'document_decree_correspondence.limitations.read',
  'document_decree_correspondence.dashboard.read',
  'document_decree_correspondence.documents.read',
  'document_decree_correspondence.document_intake.read',
  'document_decree_correspondence.document_intake.manage',
  'document_decree_correspondence.document_registration.manage',
  'document_decree_correspondence.document_routing.read',
  'document_decree_correspondence.document_routing.manage',
  'document_decree_correspondence.rector_resolutions.read',
  'document_decree_correspondence.rector_resolutions.metadata',
  'document_decree_correspondence.decrees.read',
  'document_decree_correspondence.decrees.metadata',
  'document_decree_correspondence.decree_drafts.read',
  'document_decree_correspondence.decree_drafts.manage',
  'document_decree_correspondence.incoming_correspondence.read',
  'document_decree_correspondence.incoming_correspondence.manage',
  'document_decree_correspondence.outgoing_correspondence.read',
  'document_decree_correspondence.outgoing_correspondence.manage',
  'document_decree_correspondence.templates.read',
  'document_decree_correspondence.templates.metadata',
  'document_decree_correspondence.committee_decisions.read',
  'document_decree_correspondence.committee_decisions.bridge',
  'document_decree_correspondence.assignments.read',
  'document_decree_correspondence.assignments.bridge',
  'document_decree_correspondence.execution_control.read',
  'document_decree_correspondence.execution_control.metadata',
  'document_decree_correspondence.sla_deadlines.read',
  'document_decree_correspondence.sla_deadlines.metadata',
  'document_decree_correspondence.evidence.read',
  'document_decree_correspondence.evidence.write',
  'document_decree_correspondence.attachments.read',
  'document_decree_correspondence.attachments.metadata',
  'document_decree_correspondence.audit.read',
  'document_decree_correspondence.audit.write',
  'document_decree_correspondence.archive.read',
  'document_decree_correspondence.archive.readiness',
  'document_decree_correspondence.retention.read',
  'document_decree_correspondence.retention.metadata',
  'document_decree_correspondence.signature_readiness.read',
  'document_decree_correspondence.signature_readiness.evidence',
  'document_decree_correspondence.delivery_readiness.read',
  'document_decree_correspondence.delivery_readiness.evidence',
  'document_decree_correspondence.bridges.executive.read',
  'document_decree_correspondence.bridges.executive.write',
  'document_decree_correspondence.bridges.assignments.read',
  'document_decree_correspondence.bridges.assignments.write',
  'document_decree_correspondence.roles.read',
  'document_decree_correspondence.metadata.read',
] as const;

const REQUIRED_BOUNDARY_LABELS = [
  'Metadata/evidence-only document foundation',
  'Human review required',
  'No fake official documents',
  'No fake decrees',
  'No fake signatures',
  'No fake delivery confirmations',
  'No official legal effect',
  'No automatic rector decision',
  'No automatic decree approval',
  'No automatic document signing',
  'No external ministry/eGov submission',
  'No hidden staff/department score',
  'Signature readiness only',
  'Delivery readiness only',
  'Archive readiness only',
  'Incomplete data supported',
  'Bridge-first / read-only-first',
  'No production-ready claim',
  'No sales-ready claim',
  'No GCC-ready claim',
  'fakeDocuments=false',
  'fakeDecrees=false',
  'fakeSignatures=false',
  'fakeDeliveryConfirmations=false',
  'fakeArchiveLegalRecord=false',
  'officialLegalEffect=false',
  'externalSubmissionEnabled=false',
  'automaticRectorDecisionEnabled=false',
  'automaticDecreeApprovalEnabled=false',
  'automaticDocumentSigningEnabled=false',
  'hiddenScorePresent=false',
] as const;

const FORBIDDEN_DOM_LABELS = [
  'Sign document',
  'Issue official decree',
  'Approve decree automatically',
  'Rector decision auto',
  'Submit to ministry',
  'Send external delivery',
  'Confirm legal archive',
  'Fake signature',
  'Fake decree',
  'Fake document',
  'Hidden staff score',
  'Hidden department score',
  'Production ready',
  'Sales ready',
  'GCC ready',
  'L5/L6 ready',
  'Document signed',
  'Decree issued',
  'Rector decision completed automatically',
  'Ministry submitted',
  'External delivery sent',
  'Legal archive confirmed',
  'Hidden score published',
  'EDS signed',
  'Official legal effect granted',
] as const;

const FORBIDDEN_EXACT_TEXTS = [
  /^Sign document$/i,
  /^Issue official decree$/i,
  /^Approve decree automatically$/i,
  /^Rector decision auto$/i,
  /^Submit to ministry$/i,
  /^Send external delivery$/i,
  /^Confirm legal archive$/i,
  /^Document signed$/i,
  /^Decree issued$/i,
  /^Rector decision completed automatically$/i,
  /^Ministry submitted$/i,
  /^External delivery sent$/i,
  /^Legal archive confirmed$/i,
  /^Hidden score published$/i,
  /^EDS signed$/i,
  /^Official legal effect granted$/i,
  /^Production ready$/i,
  /^Sales ready$/i,
  /^GCC ready$/i,
  /^L5\/L6 ready$/i,
] as const;

const BASE_FLAGS = {
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
  created_at: '2026-05-27T00:00:00Z',
  updated_at: '2026-05-27T00:00:00Z',
} as const;

type DdcRouteKey =
  | 'overview'
  | 'dashboard'
  | 'documents'
  | 'intake'
  | 'routing'
  | 'rector-resolutions'
  | 'decrees'
  | 'decree-drafts'
  | 'incoming'
  | 'outgoing'
  | 'templates'
  | 'committee-decisions'
  | 'assignments'
  | 'execution-control'
  | 'sla-deadlines'
  | 'evidence'
  | 'attachments'
  | 'audit'
  | 'archive'
  | 'signature-readiness'
  | 'delivery-readiness'
  | 'bridges'
  | 'limitations';

interface DdcRouteSpec {
  path: string;
  routeKey: DdcRouteKey;
  title: string;
  requiredPermission: string;
  expectedBoundaryLabels: readonly string[];
  endpoints: readonly string[];
  dashboardLike: boolean;
  sensitive: boolean;
  humanReviewRequired: boolean;
}

function escapeRegExp(value: string) {
  return value.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

function pageUrl(path: string) {
  return new URL(path, BASE_URL).toString();
}

function makeRecord(id: number, key: string, title: string, description: string, extra: Record<string, unknown> = {}) {
  return {
    id,
    tenant_id: 1,
    key,
    title,
    description,
    status: 'ACTIVE',
    review_mode: 'HUMAN_REVIEW_ONLY',
    metadata_only: true,
    mutation_allowed: false,
    ...BASE_FLAGS,
    ...extra,
  };
}

const overviewFixture = {
  tenant_id: 1,
  module: 'document_decree_correspondence',
  product_vertical: 'Document / Decree / Correspondence Suite',
  runtime_mode: 'METADATA_EVIDENCE_READINESS_AUDIT_ARCHIVE_HUMAN_REVIEW_ONLY',
  table_count: 26,
  route_count: 23,
  permission_count: 50,
  planned_route_count: 23,
  backend_route_count: 53,
  backend_permission_count: 50,
  boundary_summary: {
    no_legal_effect: true,
    no_signing: true,
    no_external_submission: true,
    no_automatic_decisions: true,
  },
  ...BASE_FLAGS,
};

const readinessFixture = {
  runtime_mode: 'METADATA_EVIDENCE_READINESS_AUDIT_ARCHIVE_HUMAN_REVIEW_ONLY',
  backend_route_count: 53,
  backend_permission_count: 50,
  bridge_targets: ['EXECUTIVE', 'ASSIGNMENTS'],
  statuses: {
    signature_readiness_only: 'ACTIVE',
    delivery_readiness_only: 'ACTIVE',
    archive_readiness_only: 'ACTIVE',
  },
  ...BASE_FLAGS,
};

const limitationsFixture = {
  items: [
    'No fake official documents, decrees, signatures, or delivery confirmations are generated in this runtime.',
    'No official legal effect, automatic rector/decree approval, document signing, or external submission is implemented.',
    'No hidden staff/department score and no production/sales/GCC/L5/L6 claim is implemented.',
  ],
};

const dashboardFixture = {
  tenant_id: 1,
  generated_at: '2026-05-27T00:00:00Z',
  route_count: 23,
  permission_count: 50,
  cards: {
    intake: 1,
    routing: 1,
    decrees: 1,
    correspondence: 1,
    evidence: 1,
    archive: 1,
    bridges: 1,
  },
  boundary_summary: {
    fake_documents: false,
    fake_decrees: false,
    fake_signatures: false,
  },
  ...BASE_FLAGS,
};

const DDC_FIXTURES = {
  health: { ok: true, module: 'document_decree_correspondence', ...BASE_FLAGS },
  overview: overviewFixture,
  readiness: readinessFixture,
  limitations: limitationsFixture,
  safetyBoundaries: { labels: REQUIRED_BOUNDARY_LABELS, ...BASE_FLAGS },
  dashboard: dashboardFixture,
  documents: { items: [makeRecord(1, 'DOC-001', 'Document registration metadata', 'Document registry metadata only.')], ...BASE_FLAGS },
  documentIntake: { items: [makeRecord(2, 'INT-001', 'Intake metadata', 'Intake metadata under human review.')], ...BASE_FLAGS },
  documentRegistration: { ok: true, accepted: true, mutation_applied: false, ...BASE_FLAGS },
  documentRouting: { items: [makeRecord(3, 'ROUTE-001', 'Routing metadata', 'Routing metadata and reviewer hops.')], ...BASE_FLAGS },
  rectorResolutions: { items: [makeRecord(4, 'RECTOR-001', 'Rector resolution metadata', 'No automatic rector decision.')], ...BASE_FLAGS },
  decrees: { items: [makeRecord(5, 'DEC-001', 'Decree registry metadata', 'No official legal effect.')], ...BASE_FLAGS },
  decreeDrafts: { items: [makeRecord(6, 'DRAFT-001', 'Decree draft metadata', 'Manual review draft lifecycle only.')], ...BASE_FLAGS },
  incomingCorrespondence: { items: [makeRecord(7, 'IN-001', 'Incoming correspondence', 'Incoming metadata only.')], ...BASE_FLAGS },
  outgoingCorrespondence: { items: [makeRecord(8, 'OUT-001', 'Outgoing correspondence', 'Outgoing metadata only, no external dispatch.')], ...BASE_FLAGS },
  templates: { items: [makeRecord(9, 'TPL-001', 'Template metadata', 'Template metadata only.')], ...BASE_FLAGS },
  committeeDecisions: { items: [makeRecord(10, 'COM-001', 'Committee bridge metadata', 'Committee decision bridge summary.')], ...BASE_FLAGS },
  committeeDecisionsBridge: { ok: true, accepted: true, mutation_applied: false, ...BASE_FLAGS },
  assignments: { items: [makeRecord(11, 'ASG-001', 'Assignment bridge metadata', 'Assignment bridge summary.')], ...BASE_FLAGS },
  assignmentsBridge: { ok: true, accepted: true, mutation_applied: false, ...BASE_FLAGS },
  executionControl: { items: [makeRecord(12, 'EXE-001', 'Execution control metadata', 'Execution-control metadata, no automation.')], ...BASE_FLAGS },
  slaDeadlines: { items: [makeRecord(13, 'SLA-001', 'SLA deadline metadata', 'SLA/deadline metadata with incomplete data support.')], ...BASE_FLAGS },
  evidence: { items: [makeRecord(14, 'EVD-001', 'Evidence item metadata', 'Evidence metadata only.')], ...BASE_FLAGS },
  attachments: { items: [makeRecord(15, 'ATT-001', 'Attachment metadata', 'Attachment references metadata only.')], ...BASE_FLAGS },
  auditEvents: { items: [makeRecord(16, 'AUD-001', 'Audit event metadata', 'Audit trail metadata only.')], ...BASE_FLAGS },
  archive: { items: [makeRecord(17, 'ARC-001', 'Archive readiness metadata', 'Archive readiness only, no legal archive confirmation.')], ...BASE_FLAGS },
  archiveReadiness: { ok: true, accepted: true, mutation_applied: false, ...BASE_FLAGS },
  retentionMetadata: { ok: true, accepted: true, mutation_applied: false, ...BASE_FLAGS },
  signatureReadiness: { items: [makeRecord(18, 'SIG-001', 'Signature readiness metadata', 'Signature readiness only, no signing.')], ...BASE_FLAGS },
  signatureReadinessEvidence: { ok: true, accepted: true, mutation_applied: false, ...BASE_FLAGS },
  deliveryReadiness: { items: [makeRecord(19, 'DEL-001', 'Delivery readiness metadata', 'Delivery readiness only, no external delivery execution.')], ...BASE_FLAGS },
  deliveryReadinessEvidence: { ok: true, accepted: true, mutation_applied: false, ...BASE_FLAGS },
  bridgesExecutive: { items: [makeRecord(20, 'BR-EXEC-001', 'Executive bridge metadata', 'Read-only-first executive bridge.')], ...BASE_FLAGS },
  bridgesAssignments: { items: [makeRecord(21, 'BR-ASG-001', 'Assignments bridge metadata', 'Read-only-first assignment bridge.')], ...BASE_FLAGS },
  roles: {
    items: [
      {
        key: 'document_decree_correspondence_admin',
        title: 'Document Decree Correspondence Admin',
        permissions: FULL_PERMISSIONS,
      },
    ],
  },
  permissions: { items: FULL_PERMISSIONS.map((value) => ({ value })) },
  metadataContract: {
    module: 'document_decree_correspondence',
    route_count: 23,
    permission_count: 50,
    runtime_mode: 'METADATA_EVIDENCE_READINESS_AUDIT_ARCHIVE_HUMAN_REVIEW_ONLY',
    forbidden_actions: [...FORBIDDEN_DOM_LABELS],
    boundary_labels: [...REQUIRED_BOUNDARY_LABELS],
    ...BASE_FLAGS,
  },
} as const;

const fullAccessDdcAdminFixture = {
  sub: 'document-decree-correspondence-admin',
  displayName: 'Document Decree Correspondence E2E Admin',
  roles: ['admin'],
  permissions: FULL_PERMISSIONS,
  tenantId: 1,
} as const;

const restrictedUserFixture = {
  sub: 'document-decree-correspondence-restricted',
  displayName: 'Document Decree Correspondence Restricted User',
  roles: ['admin'],
  permissions: ['platform.admin.read'],
  tenantId: 1,
} as const;

const DDC_ROUTES = [
  {
    path: '/console/document-decree-correspondence',
    routeKey: 'overview',
    title: 'Document / Decree / Correspondence Suite',
    requiredPermission: 'document_decree_correspondence.overview.read',
    expectedBoundaryLabels: ['Metadata/evidence-only document foundation', 'Human review required', 'fakeDocuments=false'],
    endpoints: ['GET /api/admin/document-decree-correspondence/overview', 'GET /api/admin/document-decree-correspondence/readiness', 'GET /api/admin/document-decree-correspondence/limitations'],
    dashboardLike: true,
    sensitive: true,
    humanReviewRequired: true,
  },
  {
    path: '/console/document-decree-correspondence/dashboard',
    routeKey: 'dashboard',
    title: 'Document Dashboard',
    requiredPermission: 'document_decree_correspondence.dashboard.read',
    expectedBoundaryLabels: ['Metadata/evidence-only document foundation', 'Human review required', 'Incomplete data supported'],
    endpoints: ['GET /api/admin/document-decree-correspondence/dashboard'],
    dashboardLike: true,
    sensitive: true,
    humanReviewRequired: true,
  },
  {
    path: '/console/document-decree-correspondence/documents',
    routeKey: 'documents',
    title: 'Document Registration',
    requiredPermission: 'document_decree_correspondence.documents.read',
    expectedBoundaryLabels: ['Metadata/evidence-only document foundation', 'No fake official documents'],
    endpoints: ['GET /api/admin/document-decree-correspondence/documents', 'POST /api/admin/document-decree-correspondence/document-registration'],
    dashboardLike: false,
    sensitive: false,
    humanReviewRequired: false,
  },
  {
    path: '/console/document-decree-correspondence/intake',
    routeKey: 'intake',
    title: 'Document Intake',
    requiredPermission: 'document_decree_correspondence.document_intake.read',
    expectedBoundaryLabels: ['Human review required', 'No fake official documents'],
    endpoints: ['GET /api/admin/document-decree-correspondence/document-intake', 'POST /api/admin/document-decree-correspondence/document-intake'],
    dashboardLike: false,
    sensitive: true,
    humanReviewRequired: true,
  },
  {
    path: '/console/document-decree-correspondence/routing',
    routeKey: 'routing',
    title: 'Document Routing',
    requiredPermission: 'document_decree_correspondence.document_routing.read',
    expectedBoundaryLabels: ['Human review required', 'Bridge-first / read-only-first'],
    endpoints: ['GET /api/admin/document-decree-correspondence/document-routing', 'POST /api/admin/document-decree-correspondence/document-routing'],
    dashboardLike: false,
    sensitive: true,
    humanReviewRequired: true,
  },
  {
    path: '/console/document-decree-correspondence/rector-resolutions',
    routeKey: 'rector-resolutions',
    title: 'Rector Resolution Metadata',
    requiredPermission: 'document_decree_correspondence.rector_resolutions.read',
    expectedBoundaryLabels: ['No automatic rector decision', 'Human review required'],
    endpoints: ['GET /api/admin/document-decree-correspondence/rector-resolutions', 'POST /api/admin/document-decree-correspondence/rector-resolutions/metadata'],
    dashboardLike: false,
    sensitive: true,
    humanReviewRequired: true,
  },
  {
    path: '/console/document-decree-correspondence/decrees',
    routeKey: 'decrees',
    title: 'Decree Registry Metadata',
    requiredPermission: 'document_decree_correspondence.decrees.read',
    expectedBoundaryLabels: ['No automatic decree approval', 'No official legal effect'],
    endpoints: ['GET /api/admin/document-decree-correspondence/decrees', 'POST /api/admin/document-decree-correspondence/decrees/metadata'],
    dashboardLike: false,
    sensitive: true,
    humanReviewRequired: true,
  },
  {
    path: '/console/document-decree-correspondence/decree-drafts',
    routeKey: 'decree-drafts',
    title: 'Decree Drafts',
    requiredPermission: 'document_decree_correspondence.decree_drafts.read',
    expectedBoundaryLabels: ['Human review required', 'No automatic decree approval'],
    endpoints: ['GET /api/admin/document-decree-correspondence/decree-drafts', 'POST /api/admin/document-decree-correspondence/decree-drafts'],
    dashboardLike: false,
    sensitive: true,
    humanReviewRequired: true,
  },
  {
    path: '/console/document-decree-correspondence/incoming',
    routeKey: 'incoming',
    title: 'Incoming Correspondence',
    requiredPermission: 'document_decree_correspondence.incoming_correspondence.read',
    expectedBoundaryLabels: ['Metadata/evidence-only document foundation', 'Incomplete data supported'],
    endpoints: ['GET /api/admin/document-decree-correspondence/incoming-correspondence', 'POST /api/admin/document-decree-correspondence/incoming-correspondence'],
    dashboardLike: false,
    sensitive: false,
    humanReviewRequired: false,
  },
  {
    path: '/console/document-decree-correspondence/outgoing',
    routeKey: 'outgoing',
    title: 'Outgoing Correspondence',
    requiredPermission: 'document_decree_correspondence.outgoing_correspondence.read',
    expectedBoundaryLabels: ['Metadata/evidence-only document foundation', 'No external ministry/eGov submission'],
    endpoints: ['GET /api/admin/document-decree-correspondence/outgoing-correspondence', 'POST /api/admin/document-decree-correspondence/outgoing-correspondence'],
    dashboardLike: false,
    sensitive: true,
    humanReviewRequired: true,
  },
  {
    path: '/console/document-decree-correspondence/templates',
    routeKey: 'templates',
    title: 'Template Metadata',
    requiredPermission: 'document_decree_correspondence.templates.read',
    expectedBoundaryLabels: ['Metadata/evidence-only document foundation', 'Human review required'],
    endpoints: ['GET /api/admin/document-decree-correspondence/templates', 'POST /api/admin/document-decree-correspondence/templates/metadata'],
    dashboardLike: false,
    sensitive: true,
    humanReviewRequired: true,
  },
  {
    path: '/console/document-decree-correspondence/committee-decisions',
    routeKey: 'committee-decisions',
    title: 'Committee Decision Bridges',
    requiredPermission: 'document_decree_correspondence.committee_decisions.read',
    expectedBoundaryLabels: ['Human review required', 'Bridge-first / read-only-first'],
    endpoints: ['GET /api/admin/document-decree-correspondence/committee-decisions', 'POST /api/admin/document-decree-correspondence/committee-decisions/bridge'],
    dashboardLike: false,
    sensitive: true,
    humanReviewRequired: true,
  },
  {
    path: '/console/document-decree-correspondence/assignments',
    routeKey: 'assignments',
    title: 'Assignment Bridges',
    requiredPermission: 'document_decree_correspondence.assignments.read',
    expectedBoundaryLabels: ['Human review required', 'Bridge-first / read-only-first'],
    endpoints: ['GET /api/admin/document-decree-correspondence/assignments', 'POST /api/admin/document-decree-correspondence/assignments/bridge'],
    dashboardLike: false,
    sensitive: true,
    humanReviewRequired: true,
  },
  {
    path: '/console/document-decree-correspondence/execution-control',
    routeKey: 'execution-control',
    title: 'Execution Control Metadata',
    requiredPermission: 'document_decree_correspondence.execution_control.read',
    expectedBoundaryLabels: ['Human review required', 'No automatic document signing'],
    endpoints: ['GET /api/admin/document-decree-correspondence/execution-control', 'POST /api/admin/document-decree-correspondence/execution-control/metadata'],
    dashboardLike: false,
    sensitive: true,
    humanReviewRequired: true,
  },
  {
    path: '/console/document-decree-correspondence/sla-deadlines',
    routeKey: 'sla-deadlines',
    title: 'SLA Deadlines',
    requiredPermission: 'document_decree_correspondence.sla_deadlines.read',
    expectedBoundaryLabels: ['Human review required', 'Incomplete data supported'],
    endpoints: ['GET /api/admin/document-decree-correspondence/sla-deadlines', 'POST /api/admin/document-decree-correspondence/sla-deadlines'],
    dashboardLike: false,
    sensitive: true,
    humanReviewRequired: true,
  },
  {
    path: '/console/document-decree-correspondence/evidence',
    routeKey: 'evidence',
    title: 'Evidence Items',
    requiredPermission: 'document_decree_correspondence.evidence.read',
    expectedBoundaryLabels: ['Metadata/evidence-only document foundation', 'Human review required'],
    endpoints: ['GET /api/admin/document-decree-correspondence/evidence', 'POST /api/admin/document-decree-correspondence/evidence'],
    dashboardLike: false,
    sensitive: true,
    humanReviewRequired: true,
  },
  {
    path: '/console/document-decree-correspondence/attachments',
    routeKey: 'attachments',
    title: 'Attachment Metadata',
    requiredPermission: 'document_decree_correspondence.attachments.read',
    expectedBoundaryLabels: ['Metadata/evidence-only document foundation', 'Incomplete data supported'],
    endpoints: ['GET /api/admin/document-decree-correspondence/attachments', 'POST /api/admin/document-decree-correspondence/attachments/metadata'],
    dashboardLike: false,
    sensitive: false,
    humanReviewRequired: false,
  },
  {
    path: '/console/document-decree-correspondence/audit',
    routeKey: 'audit',
    title: 'Audit Events',
    requiredPermission: 'document_decree_correspondence.audit.read',
    expectedBoundaryLabels: ['Human review required', 'Metadata/evidence-only document foundation'],
    endpoints: ['GET /api/admin/document-decree-correspondence/audit-events', 'POST /api/admin/document-decree-correspondence/audit-events'],
    dashboardLike: false,
    sensitive: true,
    humanReviewRequired: true,
  },
  {
    path: '/console/document-decree-correspondence/archive',
    routeKey: 'archive',
    title: 'Archive Readiness',
    requiredPermission: 'document_decree_correspondence.archive.read',
    expectedBoundaryLabels: ['Archive readiness only', 'No official legal effect'],
    endpoints: ['GET /api/admin/document-decree-correspondence/archive', 'POST /api/admin/document-decree-correspondence/archive/readiness', 'POST /api/admin/document-decree-correspondence/retention/metadata'],
    dashboardLike: false,
    sensitive: true,
    humanReviewRequired: true,
  },
  {
    path: '/console/document-decree-correspondence/signature-readiness',
    routeKey: 'signature-readiness',
    title: 'Signature Readiness',
    requiredPermission: 'document_decree_correspondence.signature_readiness.read',
    expectedBoundaryLabels: ['Signature readiness only', 'No automatic document signing'],
    endpoints: ['GET /api/admin/document-decree-correspondence/signature-readiness', 'POST /api/admin/document-decree-correspondence/signature-readiness/evidence'],
    dashboardLike: false,
    sensitive: true,
    humanReviewRequired: true,
  },
  {
    path: '/console/document-decree-correspondence/delivery-readiness',
    routeKey: 'delivery-readiness',
    title: 'Delivery Readiness',
    requiredPermission: 'document_decree_correspondence.delivery_readiness.read',
    expectedBoundaryLabels: ['Delivery readiness only', 'No external ministry/eGov submission'],
    endpoints: ['GET /api/admin/document-decree-correspondence/delivery-readiness', 'POST /api/admin/document-decree-correspondence/delivery-readiness/evidence'],
    dashboardLike: false,
    sensitive: true,
    humanReviewRequired: true,
  },
  {
    path: '/console/document-decree-correspondence/bridges',
    routeKey: 'bridges',
    title: 'Bridge Visibility',
    requiredPermission: 'document_decree_correspondence.bridges.executive.read',
    expectedBoundaryLabels: ['Bridge-first / read-only-first', 'No hidden staff/department score'],
    endpoints: ['GET /api/admin/document-decree-correspondence/bridges/executive', 'GET /api/admin/document-decree-correspondence/bridges/assignments', 'POST /api/admin/document-decree-correspondence/bridges/executive', 'POST /api/admin/document-decree-correspondence/bridges/assignments'],
    dashboardLike: false,
    sensitive: false,
    humanReviewRequired: false,
  },
  {
    path: '/console/document-decree-correspondence/limitations',
    routeKey: 'limitations',
    title: 'Limitations / Safety Boundaries',
    requiredPermission: 'document_decree_correspondence.limitations.read',
    expectedBoundaryLabels: [...REQUIRED_BOUNDARY_LABELS],
    endpoints: ['GET /api/admin/document-decree-correspondence/limitations', 'GET /api/admin/document-decree-correspondence/safety-boundaries', 'GET /api/admin/document-decree-correspondence/metadata-contract', 'POST /api/admin/document-decree-correspondence/limitations'],
    dashboardLike: false,
    sensitive: true,
    humanReviewRequired: true,
  },
] as const satisfies readonly DdcRouteSpec[];

const ROUTE_TITLE_GROUPS = [
  { label: 'A', routes: DDC_ROUTES.slice(0, 6) },
  { label: 'B', routes: DDC_ROUTES.slice(6, 12) },
  { label: 'C', routes: DDC_ROUTES.slice(12, 18) },
  { label: 'D', routes: DDC_ROUTES.slice(18, 23) },
] as const;

if (DDC_ROUTES.length !== 23) {
  throw new Error(`Document decree correspondence browser route flow must stay at 23, received ${DDC_ROUTES.length}`);
}

async function forceEnglishLocale(page: Page) {
  const url = pageUrl('/');
  const parsedUrl = new URL(url);
  const cookieOrigins = new Set<string>([
    `${parsedUrl.protocol}//${parsedUrl.host}`,
    `http://${parsedUrl.host}`,
    `https://${parsedUrl.host}`,
  ]);

  await page.context().addCookies(
    Array.from(cookieOrigins).map((origin) => ({
      name: 'app.locale',
      value: 'en',
      url: origin,
      httpOnly: false,
      secure: new URL(origin).protocol === 'https:',
      sameSite: 'Lax' as const,
    })),
  );

  await page.addInitScript(() => {
    document.cookie = 'app.locale=en; Path=/; SameSite=Lax';
    window.localStorage.setItem('app.language', 'en');
  });
}

async function stubSharedBootstrap(page: Page) {
  await page.route('**/api/auth/csrf*', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ csrfToken: 'document-decree-correspondence-csrf-token' }),
    });
  });

  await page.route('**/api/auth/me/preferences/language*', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ ok: true, language: 'en' }),
    });
  });

  await page.route('**/api/public/tenants/login-directory*', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        items: [
          {
            tenantId: 1,
            tenantCode: 'document-decree-correspondence-demo',
            tenantName: 'Document Decree Correspondence Demo Tenant',
            authMethods: ['password'],
          },
        ],
      }),
    });
  });

  await page.route('**/api/i18n/languages*', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        languages: [
          { code: 'en', label: 'English', default: true },
          { code: 'ru', label: 'Russian', default: false },
        ],
      }),
    });
  });
}

async function stubAuth(page: Page, userFixture: typeof fullAccessDdcAdminFixture | typeof restrictedUserFixture) {
  const parsedUrl = new URL(BASE_URL);
  const cookieOrigins = new Set<string>([
    `${parsedUrl.protocol}//${parsedUrl.host}`,
    `http://${parsedUrl.host}`,
    `https://${parsedUrl.host}`,
  ]);

  const payloadJson = JSON.stringify({
    sub: userFixture.sub,
    display_name: userFixture.displayName,
    roles: userFixture.roles,
    permissions: userFixture.permissions,
    tenant_id: userFixture.tenantId,
    exp: Math.floor(Date.now() / 1000) + 3600,
  });
  const payload = Buffer.from(payloadJson).toString('base64url');
  const fakeToken = `fakeheader.${payload}.fakesig`;

  await page.context().addCookies(
    Array.from(cookieOrigins).flatMap((origin) => {
      const secure = new URL(origin).protocol === 'https:';
      return [
        { name: 'admin_token', value: fakeToken, url: origin, httpOnly: true, secure, sameSite: 'Lax' as const },
        { name: 'app_access_token', value: fakeToken, url: origin, httpOnly: true, secure, sameSite: 'Lax' as const },
      ];
    }),
  );

  for (const pattern of ['**/api/auth/me*', '**/api/bff/auth/me*']) {
    await page.route(pattern, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          authenticated: true,
          user: userFixture,
        }),
      });
    });
  }
}

function matchDdcFixture(path: string) {
  if (path === `${API_BASE}/health` || path === `${BFF_BASE}/health`) return DDC_FIXTURES.health;
  if (path === `${API_BASE}/overview` || path === `${BFF_BASE}/overview`) return DDC_FIXTURES.overview;
  if (path === `${API_BASE}/readiness` || path === `${BFF_BASE}/readiness`) return DDC_FIXTURES.readiness;
  if (path === `${API_BASE}/limitations` || path === `${BFF_BASE}/limitations`) return DDC_FIXTURES.limitations;
  if (path === `${API_BASE}/safety-boundaries` || path === `${BFF_BASE}/safety-boundaries`) return DDC_FIXTURES.safetyBoundaries;
  if (path === `${API_BASE}/dashboard` || path === `${BFF_BASE}/dashboard`) return DDC_FIXTURES.dashboard;
  if (path === `${API_BASE}/documents` || path === `${BFF_BASE}/documents`) return DDC_FIXTURES.documents;
  if (path === `${API_BASE}/document-intake` || path === `${BFF_BASE}/document-intake`) return DDC_FIXTURES.documentIntake;
  if (path === `${API_BASE}/document-registration` || path === `${BFF_BASE}/document-registration`) return DDC_FIXTURES.documentRegistration;
  if (path === `${API_BASE}/document-routing` || path === `${BFF_BASE}/document-routing`) return DDC_FIXTURES.documentRouting;
  if (path === `${API_BASE}/rector-resolutions` || path === `${BFF_BASE}/rector-resolutions`) return DDC_FIXTURES.rectorResolutions;
  if (path === `${API_BASE}/decrees` || path === `${BFF_BASE}/decrees`) return DDC_FIXTURES.decrees;
  if (path === `${API_BASE}/decree-drafts` || path === `${BFF_BASE}/decree-drafts`) return DDC_FIXTURES.decreeDrafts;
  if (path === `${API_BASE}/incoming-correspondence` || path === `${BFF_BASE}/incoming-correspondence`) return DDC_FIXTURES.incomingCorrespondence;
  if (path === `${API_BASE}/outgoing-correspondence` || path === `${BFF_BASE}/outgoing-correspondence`) return DDC_FIXTURES.outgoingCorrespondence;
  if (path === `${API_BASE}/templates` || path === `${BFF_BASE}/templates`) return DDC_FIXTURES.templates;
  if (path === `${API_BASE}/committee-decisions` || path === `${BFF_BASE}/committee-decisions`) return DDC_FIXTURES.committeeDecisions;
  if (path === `${API_BASE}/committee-decisions/bridge` || path === `${BFF_BASE}/committee-decisions/bridge`) return DDC_FIXTURES.committeeDecisionsBridge;
  if (path === `${API_BASE}/assignments` || path === `${BFF_BASE}/assignments`) return DDC_FIXTURES.assignments;
  if (path === `${API_BASE}/assignments/bridge` || path === `${BFF_BASE}/assignments/bridge`) return DDC_FIXTURES.assignmentsBridge;
  if (path === `${API_BASE}/execution-control` || path === `${BFF_BASE}/execution-control`) return DDC_FIXTURES.executionControl;
  if (path === `${API_BASE}/sla-deadlines` || path === `${BFF_BASE}/sla-deadlines`) return DDC_FIXTURES.slaDeadlines;
  if (path === `${API_BASE}/evidence` || path === `${BFF_BASE}/evidence`) return DDC_FIXTURES.evidence;
  if (path === `${API_BASE}/attachments` || path === `${BFF_BASE}/attachments`) return DDC_FIXTURES.attachments;
  if (path === `${API_BASE}/audit-events` || path === `${BFF_BASE}/audit-events`) return DDC_FIXTURES.auditEvents;
  if (path === `${API_BASE}/archive` || path === `${BFF_BASE}/archive`) return DDC_FIXTURES.archive;
  if (path === `${API_BASE}/archive/readiness` || path === `${BFF_BASE}/archive/readiness`) return DDC_FIXTURES.archiveReadiness;
  if (path === `${API_BASE}/retention/metadata` || path === `${BFF_BASE}/retention/metadata`) return DDC_FIXTURES.retentionMetadata;
  if (path === `${API_BASE}/signature-readiness` || path === `${BFF_BASE}/signature-readiness`) return DDC_FIXTURES.signatureReadiness;
  if (path === `${API_BASE}/signature-readiness/evidence` || path === `${BFF_BASE}/signature-readiness/evidence`) return DDC_FIXTURES.signatureReadinessEvidence;
  if (path === `${API_BASE}/delivery-readiness` || path === `${BFF_BASE}/delivery-readiness`) return DDC_FIXTURES.deliveryReadiness;
  if (path === `${API_BASE}/delivery-readiness/evidence` || path === `${BFF_BASE}/delivery-readiness/evidence`) return DDC_FIXTURES.deliveryReadinessEvidence;
  if (path === `${API_BASE}/bridges/executive` || path === `${BFF_BASE}/bridges/executive`) return DDC_FIXTURES.bridgesExecutive;
  if (path === `${API_BASE}/bridges/assignments` || path === `${BFF_BASE}/bridges/assignments`) return DDC_FIXTURES.bridgesAssignments;
  if (path === `${API_BASE}/roles` || path === `${BFF_BASE}/roles`) return DDC_FIXTURES.roles;
  if (path === `${API_BASE}/permissions` || path === `${BFF_BASE}/permissions`) return DDC_FIXTURES.permissions;
  if (path === `${API_BASE}/metadata-contract` || path === `${BFF_BASE}/metadata-contract`) return DDC_FIXTURES.metadataContract;
  if (path === `${API_BASE}/rector-resolutions/metadata` || path === `${BFF_BASE}/rector-resolutions/metadata`) return { ok: true, accepted: true, mutation_applied: false, ...BASE_FLAGS };
  if (path === `${API_BASE}/decrees/metadata` || path === `${BFF_BASE}/decrees/metadata`) return { ok: true, accepted: true, mutation_applied: false, ...BASE_FLAGS };
  if (path === `${API_BASE}/templates/metadata` || path === `${BFF_BASE}/templates/metadata`) return { ok: true, accepted: true, mutation_applied: false, ...BASE_FLAGS };
  if (path === `${API_BASE}/execution-control/metadata` || path === `${BFF_BASE}/execution-control/metadata`) return { ok: true, accepted: true, mutation_applied: false, ...BASE_FLAGS };
  if (path === `${API_BASE}/attachments/metadata` || path === `${BFF_BASE}/attachments/metadata`) return { ok: true, accepted: true, mutation_applied: false, ...BASE_FLAGS };
  return null;
}

async function stubDdcApi(page: Page) {
  const fulfillDdcRoute = async (route: Route) => {
    const request = route.request();
    const url = new URL(request.url());
    const payload = matchDdcFixture(url.pathname);

    const ok = async (body: unknown, status = 200) => {
      await route.fulfill({
        status,
        contentType: 'application/json',
        body: JSON.stringify(body),
      });
    };

    if (payload) {
      await ok(payload);
      return;
    }

    if (request.method() === 'POST' || request.method() === 'PATCH') {
      await ok({
        ok: true,
        accepted: true,
        mutation_applied: false,
        mode: 'metadata_evidence_readiness_only',
        ...BASE_FLAGS,
      });
      return;
    }

    await ok({ detail: `Unhandled DDC stub path: ${url.pathname}` }, 404);
  };

  await page.route(`**${API_BASE}**`, fulfillDdcRoute);
  await page.route(`**${BFF_BASE}**`, fulfillDdcRoute);
}

async function setAuthenticatedDdcAdmin(page: Page) {
  await forceEnglishLocale(page);
  await stubSharedBootstrap(page);
  await stubAuth(page, fullAccessDdcAdminFixture);
  await stubDdcApi(page);
}

async function setRestrictedDdcUser(page: Page) {
  await forceEnglishLocale(page);
  await stubSharedBootstrap(page);
  await stubAuth(page, restrictedUserFixture);
  await stubDdcApi(page);
}

async function gotoDdcRoute(page: Page, path: string) {
  for (let attempt = 0; attempt < 3; attempt += 1) {
    try {
      await page.goto(pageUrl(path), { waitUntil: 'domcontentloaded' });
      return;
    } catch (error) {
      const message = error instanceof Error ? error.message : String(error);
      const isTransientNavigationFailure = /ERR_ABORTED|frame was detached/i.test(message);
      if (!isTransientNavigationFailure || attempt === 2) {
        throw error;
      }
    }
  }
}

async function expectRequiredBoundaryLabels(page: Page) {
  for (const label of REQUIRED_BOUNDARY_LABELS) {
    await expect(page.locator('body')).toContainText(label);
  }
}

async function expectForbiddenDomAbsent(page: Page) {
  for (const label of FORBIDDEN_DOM_LABELS) {
    const exactLabelPattern = new RegExp(`^${escapeRegExp(label)}$`, 'i');
    await expect(page.getByRole('button', { name: exactLabelPattern })).toHaveCount(0);
    await expect(page.getByRole('link', { name: exactLabelPattern })).toHaveCount(0);
    await expect(page.getByText(exactLabelPattern)).toHaveCount(0);
  }

  for (const pattern of FORBIDDEN_EXACT_TEXTS) {
    await expect(page.getByText(pattern)).toHaveCount(0);
  }
}

async function expectCommonRuntimeSafety(page: Page) {
  await expect(page.getByTestId('ddc-safety-checklist')).toContainText('fakeDocuments=false');
  await expect(page.getByTestId('ddc-safety-checklist')).toContainText('fakeDecrees=false');
  await expect(page.getByTestId('ddc-safety-checklist')).toContainText('fakeSignatures=false');
  await expect(page.getByTestId('ddc-safety-checklist')).toContainText('fakeDeliveryConfirmations=false');
  await expect(page.getByTestId('ddc-safety-checklist')).toContainText('fakeArchiveLegalRecord=false');
  await expect(page.getByTestId('ddc-safety-checklist')).toContainText('officialLegalEffect=false');
  await expect(page.getByTestId('ddc-safety-checklist')).toContainText('externalSubmissionEnabled=false');
  await expect(page.getByTestId('ddc-safety-checklist')).toContainText('automaticRectorDecisionEnabled=false');
  await expect(page.getByTestId('ddc-safety-checklist')).toContainText('automaticDecreeApprovalEnabled=false');
  await expect(page.getByTestId('ddc-safety-checklist')).toContainText('automaticDocumentSigningEnabled=false');
  await expect(page.getByTestId('ddc-safety-checklist')).toContainText('hiddenScorePresent=false');
  await expect(page.getByTestId('ddc-safety-checklist')).toContainText('humanReviewRequired=true');
  await expect(page.getByTestId('ddc-incomplete-data-notice')).toContainText('incompleteData=true');
  await expect(page.getByTestId('ddc-no-overclaim-footer')).toContainText('No sign document UI.');
  await expect(page.getByTestId('ddc-no-overclaim-footer')).toContainText('No issue official decree UI.');
  await expect(page.getByTestId('ddc-no-overclaim-footer')).toContainText('No automatic rector/decree approval UI.');
  await expect(page.getByTestId('ddc-no-overclaim-footer')).toContainText('No external submission or delivery execution UI.');
  await expect(page.getByTestId('ddc-no-overclaim-footer')).toContainText('No legal-effect archive confirmation UI.');
  await expect(page.getByTestId('ddc-no-overclaim-footer')).toContainText('No hidden staff/department score UI.');
  await expect(page.getByTestId('ddc-no-overclaim-footer')).toContainText('No production/sales/GCC/L5/L6 claim.');
}

async function expectRouteShell(page: Page, route: (typeof DDC_ROUTES)[number]) {
  const shell = page.getByTestId('ddc-page-shell');
  await expect(shell).toBeVisible({ timeout: 15_000 });
  await expect(page.getByRole('heading', { name: route.title, level: 1 })).toBeVisible({ timeout: 15_000 });
  await expect(shell).toContainText('Document / Decree / Correspondence Suite', { timeout: 15_000 });
  await expect(page.locator('nav[aria-label="Document decree correspondence navigation"] a')).toHaveCount(23, { timeout: 15_000 });
  await expect(page.getByRole('link', { name: 'Document / Decree / Correspondence Suite' })).toBeVisible({ timeout: 15_000 });
  await expect(page.getByRole('link', { name: 'Document Dashboard' })).toBeVisible({ timeout: 15_000 });
  await expect(page.getByRole('link', { name: 'Limitations / Safety Boundaries' })).toBeVisible({ timeout: 15_000 });
}

async function expectPermissionDeniedOrSafeFallback(page: Page) {
  const deniedPanel = page.getByTestId('ddc-permission-denied-panel');
  const outerAccessDenied = page.getByRole('heading', { name: /Access Denied/i });

  if (await deniedPanel.count()) {
    await expect(deniedPanel).toBeVisible();
    await expect(deniedPanel).toContainText('Permission required');
    await expect(deniedPanel).toContainText('fail-closed');
  } else if (await outerAccessDenied.count()) {
    await expect(outerAccessDenied).toBeVisible();
    await expect(page.locator('body')).toContainText(/fail-closed/i);
  } else {
    await expect(page.locator('body')).toContainText(/fail-closed/i);
  }

  await expect(page.getByTestId('ddc-dashboard-grid')).toHaveCount(0);
  await expect(page.getByTestId('ddc-signature-readiness-badge')).toHaveCount(0);
  await expect(page.getByTestId('ddc-delivery-readiness-badge')).toHaveCount(0);
  await expectForbiddenDomAbsent(page);
}

async function openAndAssertRoute(page: Page, route: (typeof DDC_ROUTES)[number]) {
  await gotoDdcRoute(page, route.path);
  await expectRouteShell(page, route);

  const routePage = page.getByTestId(`ddc-page-${route.routeKey}`);
  await expect(routePage).toBeVisible();
  await expect(page.locator('body')).toContainText(route.requiredPermission);

  for (const label of route.expectedBoundaryLabels) {
    await expect(page.locator('body')).toContainText(label);
  }

  for (const endpoint of route.endpoints) {
    await expect(page.getByTestId('ddc-evidence-table')).toContainText(endpoint);
  }

  await expectCommonRuntimeSafety(page);
  await expectForbiddenDomAbsent(page);
}

async function visitRouteWithFreshPage(browser: Browser, route: (typeof DDC_ROUTES)[number]) {
  const page = await browser.newPage({ ignoreHTTPSErrors: true });

  try {
    page.setDefaultTimeout(15_000);
    page.setDefaultNavigationTimeout(15_000);
    await setAuthenticatedDdcAdmin(page);
    await openAndAssertRoute(page, route);
  } finally {
    await page.close();
  }
}

test.describe('A-041.4 Document / Decree / Correspondence route coverage', () => {
  test.describe.configure({ timeout: 260_000 });

  test('DDC-E2E-GROUP-00 route inventory has exactly 23 routes', async () => {
    expect(DDC_ROUTES).toHaveLength(23);
  });

  test('DDC-E2E-GROUP-01 full-access document admin can visit all 23 routes', async ({ browser }) => {
    for (const route of DDC_ROUTES) {
      await test.step(`full-access ${route.routeKey} ${route.path} -> ${route.title}`, async () => {
        await visitRouteWithFreshPage(browser, route);
      });
    }
  });

  test('DDC-E2E-GROUP-02 route-title group A, routes 1-6', async ({ browser }) => {
    for (const route of ROUTE_TITLE_GROUPS[0].routes) {
      await test.step(`route-title ${route.routeKey} ${route.path} -> ${route.title}`, async () => {
        await visitRouteWithFreshPage(browser, route);
      });
    }
  });

  test('DDC-E2E-GROUP-03 route-title group B, routes 7-12', async ({ browser }) => {
    for (const route of ROUTE_TITLE_GROUPS[1].routes) {
      await test.step(`route-title ${route.routeKey} ${route.path} -> ${route.title}`, async () => {
        await visitRouteWithFreshPage(browser, route);
      });
    }
  });

  test('DDC-E2E-GROUP-04 route-title group C, routes 13-18', async ({ browser }) => {
    for (const route of ROUTE_TITLE_GROUPS[2].routes) {
      await test.step(`route-title ${route.routeKey} ${route.path} -> ${route.title}`, async () => {
        await visitRouteWithFreshPage(browser, route);
      });
    }
  });

  test('DDC-E2E-GROUP-05 route-title group D, routes 19-23', async ({ browser }) => {
    for (const route of ROUTE_TITLE_GROUPS[3].routes) {
      await test.step(`route-title ${route.routeKey} ${route.path} -> ${route.title}`, async () => {
        await visitRouteWithFreshPage(browser, route);
      });
    }
  });
});

test.describe('A-041.4 Document / Decree / Correspondence scenario groups', () => {
  test.describe.configure({ timeout: 200_000 });

  test('DDC-E2E-GROUP-06 overview/readiness/limitations boundaries', async ({ page }) => {
    await setAuthenticatedDdcAdmin(page);
    await openAndAssertRoute(page, DDC_ROUTES[0]);
    await gotoDdcRoute(page, DDC_ROUTES[22].path);
    await expectRequiredBoundaryLabels(page);
    await expect(page.getByTestId('ddc-readiness-runtime-baseline')).toContainText('Backend route count used: 53');
  });

  test('DDC-E2E-GROUP-07 dashboard incomplete-data and fake flags false boundary', async ({ page }) => {
    await setAuthenticatedDdcAdmin(page);
    await openAndAssertRoute(page, DDC_ROUTES[1]);
    await expect(page.getByTestId('ddc-safety-checklist')).toContainText('fakeDocuments=false');
    await expect(page.getByTestId('ddc-dashboard-grid')).toContainText('Document Intake');
  });

  test('DDC-E2E-GROUP-08 document registration and intake metadata', async ({ page }) => {
    await setAuthenticatedDdcAdmin(page);
    await openAndAssertRoute(page, DDC_ROUTES[2]);
    await gotoDdcRoute(page, DDC_ROUTES[3].path);
    await openAndAssertRoute(page, DDC_ROUTES[3]);
  });

  test('DDC-E2E-GROUP-09 routing and human-review-only boundary', async ({ page }) => {
    await setAuthenticatedDdcAdmin(page);
    await openAndAssertRoute(page, DDC_ROUTES[4]);
    await expect(page.getByTestId('ddc-human-review-badge')).toBeVisible();
  });

  test('DDC-E2E-GROUP-10 rector resolution non-automatic decision boundary', async ({ page }) => {
    await setAuthenticatedDdcAdmin(page);
    await openAndAssertRoute(page, DDC_ROUTES[5]);
    await expect(page.getByTestId('ddc-boundary-no-automatic-rector-decision')).toBeVisible();
  });

  test('DDC-E2E-GROUP-11 decree registry and decree draft non-legal-effect boundary', async ({ page }) => {
    await setAuthenticatedDdcAdmin(page);
    await openAndAssertRoute(page, DDC_ROUTES[6]);
    await gotoDdcRoute(page, DDC_ROUTES[7].path);
    await openAndAssertRoute(page, DDC_ROUTES[7]);
    await expect(page.getByTestId('ddc-safety-checklist')).toContainText('officialLegalEffect=false');
  });

  test('DDC-E2E-GROUP-12 incoming/outgoing correspondence non-delivery boundary', async ({ page }) => {
    await setAuthenticatedDdcAdmin(page);
    await openAndAssertRoute(page, DDC_ROUTES[8]);
    await gotoDdcRoute(page, DDC_ROUTES[9].path);
    await openAndAssertRoute(page, DDC_ROUTES[9]);
    await expect(page.getByTestId('ddc-boundary-no-external-ministry-egov-submission')).toBeVisible();
  });

  test('DDC-E2E-GROUP-13 template metadata and committee bridge', async ({ page }) => {
    await setAuthenticatedDdcAdmin(page);
    await openAndAssertRoute(page, DDC_ROUTES[10]);
    await gotoDdcRoute(page, DDC_ROUTES[11].path);
    await openAndAssertRoute(page, DDC_ROUTES[11]);
  });

  test('DDC-E2E-GROUP-14 assignment and execution-control bridge', async ({ page }) => {
    await setAuthenticatedDdcAdmin(page);
    await openAndAssertRoute(page, DDC_ROUTES[12]);
    await gotoDdcRoute(page, DDC_ROUTES[13].path);
    await openAndAssertRoute(page, DDC_ROUTES[13]);
  });

  test('DDC-E2E-GROUP-15 SLA/deadline visibility and incomplete data', async ({ page }) => {
    await setAuthenticatedDdcAdmin(page);
    await openAndAssertRoute(page, DDC_ROUTES[14]);
    await expect(page.getByTestId('ddc-boundary-incomplete-data-supported')).toBeVisible();
  });

  test('DDC-E2E-GROUP-16 evidence and attachment metadata', async ({ page }) => {
    await setAuthenticatedDdcAdmin(page);
    await openAndAssertRoute(page, DDC_ROUTES[15]);
    await gotoDdcRoute(page, DDC_ROUTES[16].path);
    await openAndAssertRoute(page, DDC_ROUTES[16]);
  });

  test('DDC-E2E-GROUP-17 audit trail metadata', async ({ page }) => {
    await setAuthenticatedDdcAdmin(page);
    await openAndAssertRoute(page, DDC_ROUTES[17]);
    await expect(page.getByTestId('ddc-audit-timeline')).toContainText('Audit / Review Timeline');
  });

  test('DDC-E2E-GROUP-18 archive readiness / non-legal-archive boundary', async ({ page }) => {
    await setAuthenticatedDdcAdmin(page);
    await openAndAssertRoute(page, DDC_ROUTES[18]);
    await expect(page.getByTestId('ddc-archive-readiness-badge')).toContainText('officialLegalEffect=false');
  });

  test('DDC-E2E-GROUP-19 signature readiness / non-signing boundary', async ({ page }) => {
    await setAuthenticatedDdcAdmin(page);
    await openAndAssertRoute(page, DDC_ROUTES[19]);
    await expect(page.getByTestId('ddc-signature-readiness-badge')).toContainText('automaticDocumentSigningEnabled=false');
  });

  test('DDC-E2E-GROUP-20 delivery readiness / non-external-dispatch boundary', async ({ page }) => {
    await setAuthenticatedDdcAdmin(page);
    await openAndAssertRoute(page, DDC_ROUTES[20]);
    await expect(page.getByTestId('ddc-delivery-readiness-badge')).toContainText('externalSubmissionEnabled=false');
  });

  test('DDC-E2E-GROUP-21 bridges executive/assignments read-only-first', async ({ page }) => {
    await setAuthenticatedDdcAdmin(page);
    await openAndAssertRoute(page, DDC_ROUTES[21]);
    await expect(page.getByTestId('ddc-bridge-executive')).toBeVisible();
    await expect(page.getByTestId('ddc-bridge-assignments')).toBeVisible();
  });

  test('DDC-E2E-GROUP-22 no-overclaim DOM scan across all routes', async ({ browser }) => {
    for (const route of DDC_ROUTES) {
      await test.step(`no-overclaim ${route.routeKey} ${route.path} -> ${route.title}`, async () => {
        await visitRouteWithFreshPage(browser, route);
      });
    }
  });

  test('DDC-E2E-GROUP-23 permission-denial smoke', async ({ page }) => {
    await setRestrictedDdcUser(page);

    for (const path of [
      '/console/document-decree-correspondence/dashboard',
      '/console/document-decree-correspondence/rector-resolutions',
      '/console/document-decree-correspondence/decrees',
      '/console/document-decree-correspondence/outgoing',
      '/console/document-decree-correspondence/signature-readiness',
      '/console/document-decree-correspondence/delivery-readiness',
      '/console/document-decree-correspondence/archive',
      '/console/document-decree-correspondence/limitations',
    ]) {
      await gotoDdcRoute(page, path);
      await expectPermissionDeniedOrSafeFallback(page);
    }
  });

  test('DDC-E2E-GROUP-24 suite closeout', async ({ page }) => {
    await setAuthenticatedDdcAdmin(page);
    await openAndAssertRoute(page, DDC_ROUTES[0]);
    expect(DDC_ROUTES).toHaveLength(23);
    await expect(page.locator('nav[aria-label="Document decree correspondence navigation"] a')).toHaveCount(23);
  });
});
