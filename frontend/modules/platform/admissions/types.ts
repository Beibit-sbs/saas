export type ApplicantStatus = "active" | "inactive" | "archived";

export type ApplicationStage =
  | "new"
  | "received"
  | "under_review"
  | "decision_pending"
  | "concluded";

export type ApplicationConclusionType =
  | "accepted"
  | "rejected"
  | "waitlist"
  | "withdrawn";

export type DocumentStatus = "received" | "verified" | "rejected";

export type StageTransitionAction = "manual" | "automated" | "system_decision";

// ---------------------------------------------------------------------------
// Applicant
// ---------------------------------------------------------------------------

export interface Applicant {
  id: number;
  tenant_id: number;
  email: string;
  first_name: string;
  last_name: string;
  phone: string | null;
  program_id: number;
  application_year: number;
  status: ApplicantStatus;
  external_id: string | null;
  metadata_json: Record<string, unknown>;
  created_by: string;
  created_at: string;
  updated_at: string;
}

export interface ApplicantListResponse {
  total: number;
  page: number;
  page_size: number;
  items: Applicant[];
}

export interface CreateApplicantPayload {
  email: string;
  first_name: string;
  last_name: string;
  phone?: string;
  program_id: number;
  application_year: number;
  status?: ApplicantStatus;
  external_id?: string;
  metadata_json?: Record<string, unknown>;
}

// ---------------------------------------------------------------------------
// Application
// ---------------------------------------------------------------------------

export interface Application {
  id: number;
  tenant_id: number;
  applicant_id: number;
  program_id: number;
  stage: ApplicationStage;
  conclusion_type: ApplicationConclusionType | null;
  received_at: string | null;
  decision_at: string | null;
  version: number;
  metadata_json: Record<string, unknown>;
  created_by: string;
  created_at: string;
  updated_at: string;
}

export interface ApplicationListResponse {
  total: number;
  page: number;
  page_size: number;
  items: Application[];
}

export interface CreateApplicationPayload {
  applicant_id: number;
  program_id: number;
  metadata_json?: Record<string, unknown>;
}

export interface StageTransitionPayload {
  to_stage: ApplicationStage;
  reason?: string;
  action_type?: StageTransitionAction;
  metadata_json?: Record<string, unknown>;
}

export interface StageTransitionResponse {
  application_id: number;
  from_stage: ApplicationStage;
  to_stage: ApplicationStage;
  transition_at: string;
  history_id: number;
}

// ---------------------------------------------------------------------------
// Decision
// ---------------------------------------------------------------------------

export interface ApplicationDecision {
  id: number;
  tenant_id: number;
  application_id: number;
  decision_type: ApplicationConclusionType;
  decision_rationale: string | null;
  decided_by_id: string;
  decided_at: string;
  conditions_json: Record<string, unknown>;
  version: number;
  created_at: string;
  updated_at: string;
}

export interface MakeDecisionPayload {
  decision_type: ApplicationConclusionType;
  decision_rationale?: string;
  decided_by: string;
  conditions_json?: Record<string, unknown>;
  application_version: number;
}

// ---------------------------------------------------------------------------
// Document
// ---------------------------------------------------------------------------

export interface ApplicationDocument {
  id: number;
  tenant_id: number;
  application_id: number;
  document_type: string;
  document_key: string;
  file_name: string;
  file_size_bytes: number | null;
  mime_type: string | null;
  status: DocumentStatus;
  metadata_json: Record<string, unknown>;
  created_by: string;
  created_at: string;
  verified_at: string | null;
  verified_by: string | null;
}
