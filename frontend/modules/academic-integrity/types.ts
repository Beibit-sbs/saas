/**
 * TypeScript types for Academic Integrity module.
 */

export enum IntegrityCaseStatus {
  FLAGGED = "flagged",
  UNDER_REVIEW = "under_review",
  RESOLVED = "resolved",
  DISMISSED = "dismissed",
  ESCALATED = "escalated",
}

export enum IntegrityCaseType {
  PLAGIARISM = "plagiarism",
  UNAUTHORIZED_COLLABORATION = "unauthorized_collaboration",
  UNAUTHORIZED_AID = "unauthorized_aid",
  FABRICATION = "fabrication",
  CHEATING = "cheating",
}

export interface IntegrityCase {
  id: string;
  student_id: string;
  course_id: string;
  assignment_id?: string;
  case_type: IntegrityCaseType;
  description: string;
  evidence_url?: string;
  priority: "low" | "normal" | "high";
  status: IntegrityCaseStatus;
  resolution_notes?: string;
  recommended_action?: string;
  created_at: string;
  updated_at: string;
  created_by: string;
  tenant_id: string;
}

export interface IntegrityCaseCreateRequest {
  student_id: string;
  course_id: string;
  assignment_id?: string;
  case_type: IntegrityCaseType;
  description: string;
  evidence_url?: string;
  priority?: string;
}

export interface IntegrityCaseStatusUpdate {
  status: IntegrityCaseStatus;
  resolution_notes?: string;
  recommended_action?: string;
}

export interface IntegrityCaseListResponse {
  cases: IntegrityCase[];
  total: number;
  page: number;
  page_size: number;
}

export interface IntegrityCaseDetailResponse {
  case: IntegrityCase;
}
