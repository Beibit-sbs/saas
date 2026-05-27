import { apiGet, apiPatch, apiPost } from '@/shared/api/client';
import { STUDENT_SERVICES_SUPPORT_API_PATHS } from './constants';
import type {
  AccommodationCreatePayload,
  ComplaintCreatePayload,
  ComplaintItemResponse,
  DashboardSummary,
  EscalationCreatePayload,
  EscalationItemResponse,
  HardshipCreatePayload,
  ReadinessItemResponse,
  ServiceRequestAssignPayload,
  ServiceRequestCreatePayload,
  ServiceRequestItemResponse,
  ServiceRequestListResponse,
  ServiceRequestStatusPayload,
  SupportCaseCreatePayload,
  SupportCaseItemResponse,
  SupportCaseListResponse,
  SupportCaseNoteCreatePayload,
  SupportCaseNoteItemResponse,
  SupportEvidenceCreatePayload,
  SupportEvidenceItemResponse,
} from './types';

export const studentServicesSupportApi = {
  listServiceRequests: () => apiGet<ServiceRequestListResponse>(STUDENT_SERVICES_SUPPORT_API_PATHS.requests),
  createServiceRequest: (payload: ServiceRequestCreatePayload) =>
    apiPost<ServiceRequestItemResponse>(STUDENT_SERVICES_SUPPORT_API_PATHS.requests, payload),
  getServiceRequest: (requestId: number) =>
    apiGet<ServiceRequestItemResponse>(STUDENT_SERVICES_SUPPORT_API_PATHS.requestById(requestId)),
  assignServiceRequest: (requestId: number, payload: ServiceRequestAssignPayload) =>
    apiPatch<ServiceRequestItemResponse>(STUDENT_SERVICES_SUPPORT_API_PATHS.requestAssign(requestId), payload),
  updateServiceRequestStatus: (requestId: number, payload: ServiceRequestStatusPayload) =>
    apiPatch<ServiceRequestItemResponse>(STUDENT_SERVICES_SUPPORT_API_PATHS.requestStatus(requestId), payload),

  listSupportCases: () => apiGet<SupportCaseListResponse>(STUDENT_SERVICES_SUPPORT_API_PATHS.cases),
  createSupportCase: (payload: SupportCaseCreatePayload) =>
    apiPost<SupportCaseItemResponse>(STUDENT_SERVICES_SUPPORT_API_PATHS.cases, payload),
  getSupportCase: (caseId: number) =>
    apiGet<SupportCaseItemResponse>(STUDENT_SERVICES_SUPPORT_API_PATHS.caseById(caseId)),
  addSupportCaseNote: (caseId: number, payload: SupportCaseNoteCreatePayload) =>
    apiPost<SupportCaseNoteItemResponse>(STUDENT_SERVICES_SUPPORT_API_PATHS.caseNotes(caseId), payload),
  attachSupportEvidenceMetadata: (caseId: number, payload: SupportEvidenceCreatePayload) =>
    apiPost<SupportEvidenceItemResponse>(STUDENT_SERVICES_SUPPORT_API_PATHS.caseEvidence(caseId), payload),

  createHardshipRequest: (payload: HardshipCreatePayload) =>
    apiPost<ReadinessItemResponse>(STUDENT_SERVICES_SUPPORT_API_PATHS.hardship, payload),
  createAccommodationRequest: (payload: AccommodationCreatePayload) =>
    apiPost<ReadinessItemResponse>(STUDENT_SERVICES_SUPPORT_API_PATHS.accommodations, payload),
  createComplaint: (payload: ComplaintCreatePayload) =>
    apiPost<ComplaintItemResponse>(STUDENT_SERVICES_SUPPORT_API_PATHS.complaints, payload),
  createEscalation: (payload: EscalationCreatePayload) =>
    apiPost<EscalationItemResponse>(STUDENT_SERVICES_SUPPORT_API_PATHS.escalations, payload),

  getDashboardSummary: () => apiGet<DashboardSummary>(STUDENT_SERVICES_SUPPORT_API_PATHS.dashboardSummary),
};
