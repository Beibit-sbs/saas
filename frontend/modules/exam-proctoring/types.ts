/**
 * Exam Proctoring Types
 * Defines interfaces for AI-camera proctoring sessions, violations, and oversight context.
 */

export type ProctoringSessionStatus = "active" | "paused" | "ended" | "aborted";

export type ProctoringViolationType =
  | "gaze_away"
  | "multiple_faces"
  | "phone_detected"
  | "absence_detected"
  | "audio_anomaly"
  | "tab_switch";

export interface ProctoringSessionRecord {
  id: number;
  tenant_id: number;
  exam_id: number;
  student_id: number;
  status: ProctoringSessionStatus | string;
  proctoring_mode?: string | null;
  scheduled_date?: string | null;
  violation_count?: number | null;
}

export interface ProctoringViolationRecord {
  violation_id: number;
  session_id: number;
  violation_type: ProctoringViolationType | string;
  confidence: number;
  reviewed: boolean;
}

export interface ExamProctoringDashboardContext {
  total_sessions: number;
  active_sessions: number;
  violations_detected: number;
  high_risk_count: number;
  requires_review_count: number;
}

/** Subset of exam-governance exam list item that is relevant for proctoring oversight. */
export interface ProctoredExamItem {
  id: number;
  course_code: string;
  course_title: string;
  status: string;
  proctoring_mode: string;
  is_proctored: boolean;
  scheduled_date?: string | null;
  scheduled_time?: string | null;
}

export interface ProctoredExamListResponse {
  items: ProctoredExamItem[];
}
