import { EXPECTED_DATA_SOURCE } from './constants';

export const ApplicantStatus = {
  DRAFT: 'DRAFT',
  SUBMITTED: 'SUBMITTED',
  UNDER_REVIEW: 'UNDER_REVIEW',
  ADDITIONAL_INFO_REQUESTED: 'ADDITIONAL_INFO_REQUESTED',
  DECISION_METADATA_RECORDED: 'DECISION_METADATA_RECORDED',
  ACCEPTED: 'ACCEPTED',
  STUDENT_PROFILE_PENDING: 'STUDENT_PROFILE_PENDING',
  STUDENT_PROFILE_CREATED: 'STUDENT_PROFILE_CREATED',
  ARCHIVED: 'ARCHIVED',
} as const;

export type ApplicantStatus = (typeof ApplicantStatus)[keyof typeof ApplicantStatus];

export const StudentStatus = {
  PROFILE_CREATED: 'PROFILE_CREATED',
  ACTIVE: 'ACTIVE',
  ON_LEAVE: 'ON_LEAVE',
  SUSPENDED: 'SUSPENDED',
  WITHDRAWN: 'WITHDRAWN',
  GRADUATED_METADATA: 'GRADUATED_METADATA',
  ARCHIVED: 'ARCHIVED',
} as const;

export type StudentStatus = (typeof StudentStatus)[keyof typeof StudentStatus];

export const EnrollmentStatus = {
  DRAFT: 'DRAFT',
  COURSE_SELECTION_PENDING: 'COURSE_SELECTION_PENDING',
  SUBMITTED: 'SUBMITTED',
  REGISTRAR_REVIEW: 'REGISTRAR_REVIEW',
  ENROLLED: 'ENROLLED',
  CHANGED: 'CHANGED',
  WITHDRAWN: 'WITHDRAWN',
  SUSPENDED: 'SUSPENDED',
  CLOSED: 'CLOSED',
} as const;

export type EnrollmentStatus = (typeof EnrollmentStatus)[keyof typeof EnrollmentStatus];

export const AcademicRecordStatus = {
  OPENED: 'OPENED',
  RESULTS_METADATA_ENTERED: 'RESULTS_METADATA_ENTERED',
  REVIEW_REQUIRED: 'REVIEW_REQUIRED',
  REVIEWED: 'REVIEWED',
  LOCKED_METADATA: 'LOCKED_METADATA',
  ARCHIVED: 'ARCHIVED',
} as const;

export type AcademicRecordStatus = (typeof AcademicRecordStatus)[keyof typeof AcademicRecordStatus];

export const TranscriptPreviewStatus = {
  NOT_GENERATED: 'NOT_GENERATED',
  GENERATED_UNOFFICIAL_PREVIEW: 'GENERATED_UNOFFICIAL_PREVIEW',
  REVIEW_REQUIRED: 'REVIEW_REQUIRED',
  RELEASED_UNOFFICIAL: 'RELEASED_UNOFFICIAL',
  OFFICIAL_REQUEST_DEFERRED: 'OFFICIAL_REQUEST_DEFERRED',
} as const;

export type TranscriptPreviewStatus = (typeof TranscriptPreviewStatus)[keyof typeof TranscriptPreviewStatus];

export const DegreeProgressStatus = {
  REQUIREMENTS_LOADED: 'REQUIREMENTS_LOADED',
  COMPUTED_FROM_AVAILABLE_SOURCES: 'COMPUTED_FROM_AVAILABLE_SOURCES',
  INCOMPLETE_DATA: 'INCOMPLETE_DATA',
  ADVISOR_REVIEW_REQUIRED: 'ADVISOR_REVIEW_REQUIRED',
  HUMAN_REVIEW_REQUIRED: 'HUMAN_REVIEW_REQUIRED',
  GRADUATION_READY_METADATA: 'GRADUATION_READY_METADATA',
  NOT_READY_METADATA: 'NOT_READY_METADATA',
  PENDING: 'PENDING',
} as const;

export type DegreeProgressStatus = (typeof DegreeProgressStatus)[keyof typeof DegreeProgressStatus];

export const StudentRequestStatus = {
  DRAFT: 'DRAFT',
  SUBMITTED: 'SUBMITTED',
  ROUTED: 'ROUTED',
  UNDER_REVIEW: 'UNDER_REVIEW',
  DECISION_METADATA_RECORDED: 'DECISION_METADATA_RECORDED',
  RESPONSE_ISSUED: 'RESPONSE_ISSUED',
  CLOSED: 'CLOSED',
  ARCHIVED: 'ARCHIVED',
} as const;

export type StudentRequestStatus = (typeof StudentRequestStatus)[keyof typeof StudentRequestStatus];

export const StudentAppealStatus = {
  DRAFT: 'DRAFT',
  SUBMITTED: 'SUBMITTED',
  ELIGIBILITY_CHECK: 'ELIGIBILITY_CHECK',
  REVIEWER_REVIEW: 'REVIEWER_REVIEW',
  COMMITTEE_REVIEW: 'COMMITTEE_REVIEW',
  DECISION_METADATA_RECORDED: 'DECISION_METADATA_RECORDED',
  RESPONSE_ISSUED: 'RESPONSE_ISSUED',
  CLOSED: 'CLOSED',
  ARCHIVED: 'ARCHIVED',
} as const;

export type StudentAppealStatus = (typeof StudentAppealStatus)[keyof typeof StudentAppealStatus];

export const InterventionStatus = {
  SIGNAL_REGISTERED: 'SIGNAL_REGISTERED',
  ADVISOR_REVIEW_REQUIRED: 'ADVISOR_REVIEW_REQUIRED',
  INTERVENTION_DRAFT: 'INTERVENTION_DRAFT',
  CONTACT_PLANNED: 'CONTACT_PLANNED',
  FOLLOW_UP_SCHEDULED: 'FOLLOW_UP_SCHEDULED',
  PROGRESS_NOTE_RECORDED: 'PROGRESS_NOTE_RECORDED',
  OUTCOME_METADATA_RECORDED: 'OUTCOME_METADATA_RECORDED',
  CLOSED: 'CLOSED',
  CONTINUED: 'CONTINUED',
} as const;

export type InterventionStatus = (typeof InterventionStatus)[keyof typeof InterventionStatus];

export const StudentLifecycleAuditEventType = {
  APPLICANT_CREATED: 'APPLICANT_CREATED',
  APPLICANT_STATUS_CHANGED: 'APPLICANT_STATUS_CHANGED',
  STUDENT_PROFILE_CREATED: 'STUDENT_PROFILE_CREATED',
  STUDENT_STATUS_CHANGED: 'STUDENT_STATUS_CHANGED',
  ENROLLMENT_CREATED: 'ENROLLMENT_CREATED',
  ENROLLMENT_REVIEWED: 'ENROLLMENT_REVIEWED',
  ACADEMIC_RECORD_OPENED: 'ACADEMIC_RECORD_OPENED',
  TRANSCRIPT_PREVIEW_GENERATED: 'TRANSCRIPT_PREVIEW_GENERATED',
  DEGREE_PROGRESS_COMPUTED: 'DEGREE_PROGRESS_COMPUTED',
  GRADUATION_READINESS_REVIEWED: 'GRADUATION_READINESS_REVIEWED',
  STUDENT_REQUEST_SUBMITTED: 'STUDENT_REQUEST_SUBMITTED',
  STUDENT_REQUEST_REVIEWED: 'STUDENT_REQUEST_REVIEWED',
  STUDENT_APPEAL_SUBMITTED: 'STUDENT_APPEAL_SUBMITTED',
  STUDENT_APPEAL_REVIEWED: 'STUDENT_APPEAL_REVIEWED',
  INTERVENTION_PLAN_CREATED: 'INTERVENTION_PLAN_CREATED',
  INTERVENTION_FOLLOWUP_RECORDED: 'INTERVENTION_FOLLOWUP_RECORDED',
  EVIDENCE_METADATA_ATTACHED: 'EVIDENCE_METADATA_ATTACHED',
  DASHBOARD_VIEWED: 'DASHBOARD_VIEWED',
} as const;

export type StudentLifecycleAuditEventType = (typeof StudentLifecycleAuditEventType)[keyof typeof StudentLifecycleAuditEventType];

export interface StudentLifecycleLimitation {
  code?: string;
  message: string;
}

export interface StudentLifecycleTrustFields {
  limitations: string[];
}

export interface StudentLifecycleHealthResponse extends StudentLifecycleTrustFields {
  tenant_id: number;
  generated_at: string;
  module_name: string;
  route_count: number;
  table_count: number;
  fake_metrics: boolean;
  data_source: typeof EXPECTED_DATA_SOURCE;
  incomplete_data: boolean;
  provider_integration_enabled: boolean;
  automated_decision_count: number;
  hidden_score_present: boolean;
}

export interface StudentLifecycleDashboardResponse extends StudentLifecycleTrustFields {
  tenant_id: number;
  generated_at: string;
  fake_metrics: boolean;
  data_source: typeof EXPECTED_DATA_SOURCE;
  incomplete_data: boolean;
  applicant_counts_by_status: Record<string, number>;
  student_counts_by_status: Record<string, number>;
  enrollment_counts_by_status: Record<string, number>;
  transcript_preview_counts: Record<string, number>;
  degree_progress_counts: Record<string, number>;
  request_counts_by_status: Record<string, number>;
  appeal_counts_by_status: Record<string, number>;
  intervention_counts_by_status: Record<string, number>;
  human_review_required_count: number;
  provider_integration_enabled: boolean;
  automated_decision_count: number;
  hidden_score_present: boolean;
}

interface BaseEntityResponse extends StudentLifecycleTrustFields {
  id: number;
  tenant_id: number;
  status: string;
  created_at: string;
  updated_at: string;
  human_review_required: boolean;
  automated_decision: boolean;
  provider_integration_enabled: boolean;
}

export interface ApplicantResponse extends BaseEntityResponse {
  status: ApplicantStatus;
  applicant_code: string;
  program_interest: string;
  entry_term: string;
  notes?: string | null;
  source_available: boolean;
  archived_at?: string | null;
}

export interface ApplicantStatusHistoryResponse {
  id: number;
  tenant_id: number;
  applicant_id: number;
  previous_status: ApplicantStatus | null;
  new_status: ApplicantStatus;
  reason?: string | null;
  actor_user_id?: string | null;
  request_id?: string | null;
  created_at: string;
}

export interface StudentProfileResponse extends BaseEntityResponse {
  status: StudentStatus;
  student_code: string;
  source_applicant_id?: number | null;
  program_code: string;
  notes?: string | null;
  archived_at?: string | null;
}

export interface StudentStatusHistoryResponse {
  id: number;
  tenant_id: number;
  student_id: number;
  previous_status: StudentStatus | null;
  new_status: StudentStatus;
  reason?: string | null;
  actor_user_id?: string | null;
  request_id?: string | null;
  created_at: string;
}

export interface StudentEnrollmentResponse extends BaseEntityResponse {
  status: EnrollmentStatus;
  student_id: number;
  term_code: string;
  notes?: string | null;
  archived_at?: string | null;
}

export interface EnrollmentStatusHistoryResponse {
  id: number;
  tenant_id: number;
  enrollment_id: number;
  previous_status: EnrollmentStatus | null;
  new_status: EnrollmentStatus;
  comment?: string | null;
  actor_user_id?: string | null;
  request_id?: string | null;
  created_at: string;
}

export interface AcademicRecordResponse extends BaseEntityResponse {
  status: AcademicRecordStatus;
  student_id: number;
  record_name: string;
  source_available: boolean;
  result_metadata: Record<string, unknown>;
}

export interface TranscriptPreviewResponse extends BaseEntityResponse {
  status: TranscriptPreviewStatus;
  student_id: number;
  academic_record_id: number;
  official_document: boolean;
  preview_payload: Record<string, unknown>;
}

export interface DegreeProgressSnapshotResponse extends BaseEntityResponse {
  status: DegreeProgressStatus;
  student_id: number;
  data_source: typeof EXPECTED_DATA_SOURCE;
  incomplete_data: boolean;
  hidden_score_present: boolean;
  completion_summary: Record<string, unknown>;
}

export interface GraduationReadinessReviewResponse {
  student_id: number;
  status: DegreeProgressStatus;
  note?: string | null;
  tenant_id: number;
  created_at: string;
  updated_at: string;
  human_review_required: boolean;
  automated_decision: boolean;
  provider_integration_enabled: boolean;
  limitations: string[];
}

export interface StudentRequestResponse extends BaseEntityResponse {
  status: StudentRequestStatus;
  student_id: number;
  request_type: string;
  description: string;
  decision_note?: string | null;
  archived_at?: string | null;
}

export interface StudentAppealResponse extends BaseEntityResponse {
  status: StudentAppealStatus;
  student_id: number;
  appeal_type: string;
  description: string;
  decision_note?: string | null;
  archived_at?: string | null;
}

export interface InterventionPlanResponse extends BaseEntityResponse {
  status: InterventionStatus;
  student_id: number;
  signal_type: string;
  plan_summary: string;
  hidden_score_present: boolean;
  followups: Array<Record<string, unknown>>;
  archived_at?: string | null;
}

export interface StudentLifecycleAuditEventResponse {
  id: number;
  tenant_id: number;
  entity_type: string;
  entity_id: number;
  event_type: StudentLifecycleAuditEventType;
  actor_user_id?: string | null;
  previous_status?: string | null;
  new_status?: string | null;
  human_review_required: boolean;
  automated_decision: boolean;
  provider_integration_enabled: boolean;
  action: string;
  request_id?: string | null;
  payload: Record<string, unknown>;
  created_at: string;
}

export interface StudentLifecycleEvidenceMetadataResponse {
  id: number;
  tenant_id: number;
  audit_event_id: number;
  entity_type: string;
  entity_id: number;
  evidence_type: string;
  evidence_ref: string;
  limitations: string[];
  created_by_user_id?: string | null;
  created_at: string;
}

export interface MutationRequest {
  limitations?: string[];
}

export interface ApplicantCreateRequest extends MutationRequest {
  applicant_code: string;
  program_interest: string;
  entry_term: string;
  notes?: string | null;
  source_available?: boolean;
}

export interface ApplicantUpdateRequest extends MutationRequest {
  program_interest?: string;
  entry_term?: string;
  notes?: string | null;
  human_review_required?: boolean;
}

export interface ApplicantStatusUpdateRequest {
  new_status: ApplicantStatus;
  reason?: string | null;
}

export interface StudentProfileCreateRequest extends MutationRequest {
  student_code: string;
  source_applicant_id?: number | null;
  program_code: string;
  notes?: string | null;
}

export interface StudentProfileUpdateRequest extends MutationRequest {
  program_code?: string;
  notes?: string | null;
  human_review_required?: boolean;
}

export interface StudentStatusUpdateRequest {
  new_status: StudentStatus;
  reason?: string | null;
}

export interface StudentEnrollmentCreateRequest extends MutationRequest {
  student_id: number;
  term_code: string;
  notes?: string | null;
}

export interface StudentEnrollmentUpdateRequest extends MutationRequest {
  notes?: string | null;
  human_review_required?: boolean;
}

export interface EnrollmentReviewRequest {
  new_status: EnrollmentStatus;
  comment?: string | null;
}

export interface AcademicRecordCreateRequest extends MutationRequest {
  student_id: number;
  record_name: string;
  source_available?: boolean;
}

export interface TranscriptPreviewCreateRequest extends MutationRequest {
  student_id: number;
  academic_record_id: number;
  preview_payload?: Record<string, unknown>;
}

export interface DegreeProgressSnapshotCreateRequest extends MutationRequest {
  student_id: number;
  incomplete_data?: boolean;
  completion_summary?: Record<string, unknown>;
}

export interface GraduationReadinessReviewRequest {
  new_status: DegreeProgressStatus;
  note?: string | null;
}

export interface StudentRequestCreateRequest extends MutationRequest {
  student_id: number;
  request_type: string;
  description: string;
}

export interface StudentRequestReviewRequest {
  new_status: StudentRequestStatus;
  decision_note?: string | null;
}

export interface StudentAppealCreateRequest extends MutationRequest {
  student_id: number;
  appeal_type: string;
  description: string;
}

export interface StudentAppealReviewRequest {
  new_status: StudentAppealStatus;
  decision_note?: string | null;
}

export interface InterventionPlanCreateRequest extends MutationRequest {
  student_id: number;
  signal_type: string;
  plan_summary: string;
}

export interface InterventionFollowupRequest {
  outcome_note: string;
  continued: boolean;
}

export interface StudentLifecycleEvidenceMetadataRequest extends MutationRequest {
  audit_event_id: number;
  entity_type: string;
  entity_id: number;
  evidence_type: string;
  evidence_ref: string;
}