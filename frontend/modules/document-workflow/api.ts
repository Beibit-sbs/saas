import { apiGet, apiPatch, apiPost } from '@/shared/api/client';
import type {
  CorrespondenceArchivePayload,
  CorrespondenceItem,
  CorrespondenceListFilters,
  CorrespondenceListResponse,
  CorrespondenceOutgoingCreatePayload,
  CorrespondenceIncomingCreatePayload,
  CorrespondenceRegisterPayload,
  CorrespondenceRoutePayload,
  DashboardSummary,
  DecreeApprovePayload,
  DecreeArchivePayload,
  DecreeCreatePayload,
  DecreeLegalReviewPayload,
  DecreeListFilters,
  DecreeListResponse,
  DecreeRegisterPayload,
  DecreeSignedMetadataPayload,
  DecreeUpdatePayload,
  DocumentApprovePayload,
  DocumentArchivePayload,
  DocumentAssignmentLink,
  DocumentAuditEvent,
  DocumentCreatePayload,
  DocumentDetail,
  DocumentListFilters,
  DocumentListResponse,
  DocumentRegisterPayload,
  DocumentReviewPayload,
  DocumentReturnPayload,
  DocumentSignedMetadataPayload,
  DocumentStatusHistory,
  DocumentUpdatePayload,
  Document,
  LinkAssignmentPayload,
  OrderDecree,
  Resolution,
  ResolutionAssignmentLink,
  ResolutionCreatePayload,
} from './types';

const BASE = '/api/admin/documents';

export const documentWorkflowApi = {
  listDocuments: (params?: DocumentListFilters) =>
    apiGet<DocumentListResponse>(BASE, params),
  createDocument: (payload: DocumentCreatePayload) => apiPost<Document>(BASE, payload),
  getDocument: (documentId: number | string) => apiGet<DocumentDetail>(`${BASE}/${documentId}`),
  updateDocument: (documentId: number | string, payload: DocumentUpdatePayload) =>
    apiPatch<Document>(`${BASE}/${documentId}`, payload),
  registerDocument: (documentId: number | string, payload: DocumentRegisterPayload) =>
    apiPost<Document>(`${BASE}/${documentId}/register`, payload),
  submitDocumentReview: (documentId: number | string, payload: DocumentReviewPayload) =>
    apiPost<Document>(`${BASE}/${documentId}/submit-review`, payload),
  returnDocument: (documentId: number | string, payload: DocumentReturnPayload) =>
    apiPost<Document>(`${BASE}/${documentId}/return`, payload),
  approveDocument: (documentId: number | string, payload: DocumentApprovePayload) =>
    apiPost<Document>(`${BASE}/${documentId}/approve`, payload),
  recordDocumentSignedMetadata: (
    documentId: number | string,
    payload: DocumentSignedMetadataPayload,
  ) => apiPost<Document>(`${BASE}/${documentId}/signed-metadata`, payload),
  archiveDocument: (documentId: number | string, payload: DocumentArchivePayload) =>
    apiPost<Document>(`${BASE}/${documentId}/archive`, payload),
  getDocumentAudit: (documentId: number | string) =>
    apiGet<DocumentAuditEvent[]>(`${BASE}/${documentId}/audit`),
  getDocumentHistory: (documentId: number | string) =>
    apiGet<DocumentStatusHistory[]>(`${BASE}/${documentId}/history`),
  linkDocumentToAssignment: (
    documentId: number | string,
    assignmentId: number | string,
    payload: LinkAssignmentPayload,
  ) => apiPost<DocumentAssignmentLink>(`${BASE}/${documentId}/link-assignment/${assignmentId}`, payload),

  listDecrees: (params?: DecreeListFilters) =>
    apiGet<DecreeListResponse>(`${BASE}/decrees`, params),
  createDecree: (payload: DecreeCreatePayload) =>
    apiPost<OrderDecree>(`${BASE}/decrees`, payload),
  getDecree: (decreeId: number | string) => apiGet<OrderDecree>(`${BASE}/decrees/${decreeId}`),
  updateDecree: (decreeId: number | string, payload: DecreeUpdatePayload) =>
    apiPatch<OrderDecree>(`${BASE}/decrees/${decreeId}`, payload),
  submitDecreeLegalReview: (
    decreeId: number | string,
    payload: DecreeLegalReviewPayload,
  ) => apiPost<OrderDecree>(`${BASE}/decrees/${decreeId}/legal-review`, payload),
  approveDecreeSigning: (decreeId: number | string, payload: DecreeApprovePayload) =>
    apiPost<OrderDecree>(`${BASE}/decrees/${decreeId}/approve-signing`, payload),
  recordDecreeSignedMetadata: (
    decreeId: number | string,
    payload: DecreeSignedMetadataPayload,
  ) => apiPost<OrderDecree>(`${BASE}/decrees/${decreeId}/signed-metadata`, payload),
  registerDecree: (decreeId: number | string, payload: DecreeRegisterPayload) =>
    apiPost<OrderDecree>(`${BASE}/decrees/${decreeId}/register`, payload),
  archiveDecree: (decreeId: number | string, payload: DecreeArchivePayload) =>
    apiPost<OrderDecree>(`${BASE}/decrees/${decreeId}/archive`, payload),

  listCorrespondence: (params?: CorrespondenceListFilters) =>
    apiGet<CorrespondenceListResponse>(`${BASE}/correspondence`, params),
  createIncomingCorrespondence: (payload: CorrespondenceIncomingCreatePayload) =>
    apiPost<CorrespondenceItem>(`${BASE}/correspondence/incoming`, payload),
  createOutgoingCorrespondence: (payload: CorrespondenceOutgoingCreatePayload) =>
    apiPost<CorrespondenceItem>(`${BASE}/correspondence/outgoing`, payload),
  getCorrespondence: (correspondenceId: number | string) =>
    apiGet<CorrespondenceItem>(`${BASE}/correspondence/${correspondenceId}`),
  registerCorrespondence: (
    correspondenceId: number | string,
    payload: CorrespondenceRegisterPayload,
  ) => apiPost<CorrespondenceItem>(`${BASE}/correspondence/${correspondenceId}/register`, payload),
  routeCorrespondence: (
    correspondenceId: number | string,
    payload: CorrespondenceRoutePayload,
  ) => apiPost<CorrespondenceItem>(`${BASE}/correspondence/${correspondenceId}/route`, payload),
  recordOutgoingSentMetadata: (correspondenceId: number | string) =>
    apiPost<CorrespondenceItem>(`${BASE}/correspondence/${correspondenceId}/sent-metadata`, {}),
  archiveCorrespondence: (
    correspondenceId: number | string,
    payload: CorrespondenceArchivePayload,
  ) => apiPost<CorrespondenceItem>(`${BASE}/correspondence/${correspondenceId}/archive`, payload),

  createResolution: (payload: ResolutionCreatePayload) =>
    apiPost<Resolution>(`${BASE}/resolutions`, payload),
  linkResolutionToAssignment: (resolutionId: number | string, assignmentId: number | string) =>
    apiPost<ResolutionAssignmentLink>(
      `${BASE}/resolutions/${resolutionId}/link-assignment/${assignmentId}`,
      {},
    ),

  getDocumentWorkflowDashboardSummary: () =>
    apiGet<DashboardSummary>(`${BASE}/dashboard/summary`),
};