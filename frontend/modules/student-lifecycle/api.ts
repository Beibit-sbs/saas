import { apiGet, apiPatch, apiPost } from '@/shared/api/client';
import { API_BASE_PATH } from './constants';
import type {
  AcademicRecordCreateRequest,
  AcademicRecordResponse,
  ApplicantCreateRequest,
  ApplicantResponse,
  ApplicantStatusHistoryResponse,
  ApplicantStatusUpdateRequest,
  ApplicantUpdateRequest,
  DegreeProgressSnapshotCreateRequest,
  DegreeProgressSnapshotResponse,
  EnrollmentReviewRequest,
  EnrollmentStatusHistoryResponse,
  GraduationReadinessReviewRequest,
  GraduationReadinessReviewResponse,
  InterventionFollowupRequest,
  InterventionPlanCreateRequest,
  InterventionPlanResponse,
  StudentAppealCreateRequest,
  StudentAppealResponse,
  StudentAppealReviewRequest,
  StudentEnrollmentCreateRequest,
  StudentEnrollmentResponse,
  StudentEnrollmentUpdateRequest,
  StudentLifecycleAuditEventResponse,
  StudentLifecycleDashboardResponse,
  StudentLifecycleEvidenceMetadataRequest,
  StudentLifecycleEvidenceMetadataResponse,
  StudentLifecycleHealthResponse,
  StudentProfileCreateRequest,
  StudentProfileResponse,
  StudentProfileUpdateRequest,
  StudentRequestCreateRequest,
  StudentRequestResponse,
  StudentRequestReviewRequest,
  StudentStatusHistoryResponse,
  StudentStatusUpdateRequest,
  TranscriptPreviewCreateRequest,
  TranscriptPreviewResponse,
} from './types';

export const studentLifecycleApi = {
  getStudentLifecycleDashboard: () => apiGet<StudentLifecycleDashboardResponse>(`${API_BASE_PATH}/dashboard`),
  getStudentLifecycleHealth: () => apiGet<StudentLifecycleHealthResponse>(`${API_BASE_PATH}/health`),

  listApplicants: () => apiGet<ApplicantResponse[]>(`${API_BASE_PATH}/applicants`),
  createApplicant: (payload: ApplicantCreateRequest) => apiPost<ApplicantResponse>(`${API_BASE_PATH}/applicants`, payload),
  getApplicant: (applicantId: number | string) => apiGet<ApplicantResponse>(`${API_BASE_PATH}/applicants/${applicantId}`),
  updateApplicant: (applicantId: number | string, payload: ApplicantUpdateRequest) =>
    apiPatch<ApplicantResponse>(`${API_BASE_PATH}/applicants/${applicantId}`, payload),
  submitApplicant: (applicantId: number | string) => apiPost<ApplicantResponse>(`${API_BASE_PATH}/applicants/${applicantId}/submit`, {}),
  updateApplicantStatus: (applicantId: number | string, payload: ApplicantStatusUpdateRequest) =>
    apiPost<ApplicantResponse>(`${API_BASE_PATH}/applicants/${applicantId}/status`, payload),
  getApplicantStatusHistory: (applicantId: number | string) =>
    apiGet<ApplicantStatusHistoryResponse[]>(`${API_BASE_PATH}/applicants/${applicantId}/status-history`),

  listStudents: () => apiGet<StudentProfileResponse[]>(`${API_BASE_PATH}/students`),
  createStudentProfile: (payload: StudentProfileCreateRequest) => apiPost<StudentProfileResponse>(`${API_BASE_PATH}/students`, payload),
  getStudentProfile: (studentId: number | string) => apiGet<StudentProfileResponse>(`${API_BASE_PATH}/students/${studentId}`),
  updateStudentProfile: (studentId: number | string, payload: StudentProfileUpdateRequest) =>
    apiPatch<StudentProfileResponse>(`${API_BASE_PATH}/students/${studentId}`, payload),
  updateStudentStatus: (studentId: number | string, payload: StudentStatusUpdateRequest) =>
    apiPost<StudentProfileResponse>(`${API_BASE_PATH}/students/${studentId}/status`, payload),
  getStudentStatusHistory: (studentId: number | string) =>
    apiGet<StudentStatusHistoryResponse[]>(`${API_BASE_PATH}/students/${studentId}/status-history`),

  listEnrollments: () => apiGet<StudentEnrollmentResponse[]>(`${API_BASE_PATH}/enrollment`),
  createEnrollment: (payload: StudentEnrollmentCreateRequest) =>
    apiPost<StudentEnrollmentResponse>(`${API_BASE_PATH}/enrollment`, payload),
  getEnrollment: (enrollmentId: number | string) => apiGet<StudentEnrollmentResponse>(`${API_BASE_PATH}/enrollment/${enrollmentId}`),
  updateEnrollment: (enrollmentId: number | string, payload: StudentEnrollmentUpdateRequest) =>
    apiPatch<StudentEnrollmentResponse>(`${API_BASE_PATH}/enrollment/${enrollmentId}`, payload),
  reviewEnrollment: (enrollmentId: number | string, payload: EnrollmentReviewRequest) =>
    apiPost<StudentEnrollmentResponse>(`${API_BASE_PATH}/enrollment/${enrollmentId}/review`, payload),
  getEnrollmentStatusHistory: (enrollmentId: number | string) =>
    apiGet<EnrollmentStatusHistoryResponse[]>(`${API_BASE_PATH}/enrollment/${enrollmentId}/status-history`),

  listAcademicRecords: () => apiGet<AcademicRecordResponse[]>(`${API_BASE_PATH}/academic-records`),
  createAcademicRecord: (payload: AcademicRecordCreateRequest) =>
    apiPost<AcademicRecordResponse>(`${API_BASE_PATH}/academic-records`, payload),
  getAcademicRecord: (recordId: number | string) => apiGet<AcademicRecordResponse>(`${API_BASE_PATH}/academic-records/${recordId}`),

  listTranscriptPreviews: () => apiGet<TranscriptPreviewResponse[]>(`${API_BASE_PATH}/transcripts`),
  createTranscriptPreview: (payload: TranscriptPreviewCreateRequest) =>
    apiPost<TranscriptPreviewResponse>(`${API_BASE_PATH}/transcripts/preview`, payload),
  getTranscriptPreview: (previewId: number | string) =>
    apiGet<TranscriptPreviewResponse>(`${API_BASE_PATH}/transcripts/${previewId}`),

  getDegreeProgress: (studentId: number | string) =>
    apiGet<DegreeProgressSnapshotResponse>(`${API_BASE_PATH}/degree-progress/${studentId}`),
  createDegreeProgressSnapshot: (studentId: number | string, payload: DegreeProgressSnapshotCreateRequest) =>
    apiPost<DegreeProgressSnapshotResponse>(`${API_BASE_PATH}/degree-progress/${studentId}/snapshot`, payload),
  reviewGraduationReadiness: (studentId: number | string, payload: GraduationReadinessReviewRequest) =>
    apiPost<GraduationReadinessReviewResponse>(`${API_BASE_PATH}/degree-progress/${studentId}/graduation-review`, payload),

  listStudentRequests: () => apiGet<StudentRequestResponse[]>(`${API_BASE_PATH}/requests`),
  createStudentRequest: (payload: StudentRequestCreateRequest) =>
    apiPost<StudentRequestResponse>(`${API_BASE_PATH}/requests`, payload),
  getStudentRequest: (requestId: number | string) => apiGet<StudentRequestResponse>(`${API_BASE_PATH}/requests/${requestId}`),
  reviewStudentRequest: (requestId: number | string, payload: StudentRequestReviewRequest) =>
    apiPost<StudentRequestResponse>(`${API_BASE_PATH}/requests/${requestId}/review`, payload),

  listStudentAppeals: () => apiGet<StudentAppealResponse[]>(`${API_BASE_PATH}/appeals`),
  createStudentAppeal: (payload: StudentAppealCreateRequest) =>
    apiPost<StudentAppealResponse>(`${API_BASE_PATH}/appeals`, payload),
  getStudentAppeal: (appealId: number | string) => apiGet<StudentAppealResponse>(`${API_BASE_PATH}/appeals/${appealId}`),
  reviewStudentAppeal: (appealId: number | string, payload: StudentAppealReviewRequest) =>
    apiPost<StudentAppealResponse>(`${API_BASE_PATH}/appeals/${appealId}/review`, payload),

  listInterventionPlans: () => apiGet<InterventionPlanResponse[]>(`${API_BASE_PATH}/interventions/plans`),
  createInterventionPlan: (payload: InterventionPlanCreateRequest) =>
    apiPost<InterventionPlanResponse>(`${API_BASE_PATH}/interventions/plans`, payload),
  getInterventionPlan: (planId: number | string) => apiGet<InterventionPlanResponse>(`${API_BASE_PATH}/interventions/plans/${planId}`),
  recordInterventionFollowup: (planId: number | string, payload: InterventionFollowupRequest) =>
    apiPost<InterventionPlanResponse>(`${API_BASE_PATH}/interventions/plans/${planId}/followups`, payload),

  listStudentLifecycleAuditEvents: () => apiGet<StudentLifecycleAuditEventResponse[]>(`${API_BASE_PATH}/audit`),
  listStudentLifecycleEvidence: () => apiGet<StudentLifecycleEvidenceMetadataResponse[]>(`${API_BASE_PATH}/evidence`),
  attachStudentLifecycleEvidenceMetadata: (payload: StudentLifecycleEvidenceMetadataRequest) =>
    apiPost<StudentLifecycleEvidenceMetadataResponse>(`${API_BASE_PATH}/evidence`, payload),
};