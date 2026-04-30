export type CounselingCaseStatus = "open" | "in_progress" | "closed";
export type WellbeingCheckinStatus = "stable" | "watch" | "at_risk";
export type AccessibilitySupportStatus = "requested" | "active" | "completed" | "denied";
export type DisciplinaryCaseStatus = "reported" | "under_review" | "resolved" | "appealed";

export interface CounselingCase {
  id: number;
  tenant_id?: string | null;
  case_code: string;
  student_id: string;
  concern_type: string;
  status: CounselingCaseStatus;
}

export interface WellbeingCheckin {
  id: number;
  tenant_id?: string | null;
  student_id: string;
  wellbeing_score: number;
  status: WellbeingCheckinStatus;
}

export interface AccessibilitySupport {
  id: number;
  tenant_id?: string | null;
  support_code: string;
  student_id: string;
  support_type: string;
  status: AccessibilitySupportStatus;
}

export interface DisciplinaryCase {
  id: number;
  tenant_id?: string | null;
  incident_code: string;
  student_id: string;
  incident_type: string;
  severity: string;
  status: DisciplinaryCaseStatus;
}

export interface StudentLifeHealth {
  counseling_cases_total: number;
  open_counseling_cases: number;
  wellbeing_checkins_total: number;
  at_risk_wellbeing_checkins: number;
  accessibility_supports_total: number;
  active_accessibility_supports: number;
  disciplinary_cases_total: number;
  unresolved_disciplinary_cases: number;
}

export interface StudentLifeHealthResponse {
  item: StudentLifeHealth;
}

export interface CounselingCaseListResponse {
  items: CounselingCase[];
}

export interface WellbeingCheckinListResponse {
  items: WellbeingCheckin[];
}

export interface AccessibilitySupportListResponse {
  items: AccessibilitySupport[];
}

export interface DisciplinaryCaseListResponse {
  items: DisciplinaryCase[];
}

export interface CounselingCaseCreatePayload {
  case_code: string;
  student_id: string;
  concern_type: string;
  status?: CounselingCaseStatus;
}

export interface WellbeingCheckinCreatePayload {
  student_id: string;
  wellbeing_score: number;
  status?: WellbeingCheckinStatus;
}

export interface AccessibilitySupportCreatePayload {
  support_code: string;
  student_id: string;
  support_type: string;
  status?: AccessibilitySupportStatus;
}

export interface DisciplinaryCaseCreatePayload {
  incident_code: string;
  student_id: string;
  incident_type: string;
  severity: string;
  status?: DisciplinaryCaseStatus;
}
