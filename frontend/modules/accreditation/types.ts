export type AccreditationStatus =
  | "draft"
  | "evidence_requested"
  | "evidence_collected"
  | "under_review"
  | "compliant"
  | "remediation_required";

export type AccreditationStandardType =
  | "institutional"
  | "programmatic"
  | "curriculum"
  | "faculty_qualifications"
  | "learning_outcomes";

export type AccreditationRiskLevel = "low" | "medium" | "high";

export interface AccreditationRecord {
  id: number;
  tenant_id?: string | null;
  standard_code: string;
  standard_type: AccreditationStandardType;
  title: string;
  owner_department: string;
  review_cycle_year: number;
  due_date?: string | null;
  evidence_summary?: string | null;
  risk_level: AccreditationRiskLevel;
  status: AccreditationStatus;
  reviewer_notes?: string | null;
  remediation_plan?: string | null;
}

export interface AccreditationCreatePayload {
  standard_code: string;
  standard_type: AccreditationStandardType;
  title: string;
  owner_department: string;
  review_cycle_year: number;
  due_date?: string | null;
  evidence_summary?: string | null;
  risk_level: AccreditationRiskLevel;
}

export interface AccreditationStatusUpdatePayload {
  status: AccreditationStatus;
  reviewer_notes?: string | null;
  remediation_plan?: string | null;
}

export interface AccreditationListResponse {
  items: AccreditationRecord[];
}

export interface AccreditationItemResponse {
  item: AccreditationRecord;
}
