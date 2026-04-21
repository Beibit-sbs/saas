export interface CourseSection {
  id: string;
  code: string;
  course_name: string;
  instructor: string | null;
  capacity: number;
  enrolled_count: number;
  semester: string;
  schedule: string | null;
  room: string | null;
  status: "open" | "closed" | "cancelled";
  tenant_id: string;
}

export interface CreateSectionPayload {
  code: string;
  course_name: string;
  instructor?: string;
  capacity: number;
  semester: string;
  schedule?: string;
  room?: string;
  tenant_id: string;
}

export type AttendanceStatus = "present" | "absent" | "late" | "excused";

export interface LessonAttendanceItem {
  id: number;
  tenant_id: number;
  lesson_instance_id: number;
  student_profile_id: number;
  attendance_status: AttendanceStatus;
  marked_by: string;
  marked_at: string;
  created_at: string;
  updated_at: string;
  version: number;
}

export interface LessonAttendanceListResponse {
  total: number;
  items: LessonAttendanceItem[];
}

export interface LessonAttendanceUpsertPayload {
  student_profile_id: number;
  attendance_status: AttendanceStatus;
}

export type LessonStatus = "planned" | "completed" | "cancelled";

export interface LessonInstance {
  id: number;
  tenant_id: number;
  section_id: number;
  scheduled_date: string;
  actual_date: string | null;
  topic_title: string;
  status: LessonStatus;
  notes: string | null;
  metadata_json: Record<string, unknown>;
  created_by: string;
  created_at: string;
  updated_at: string;
  version: number;
}

export interface LessonInstanceListResponse {
  total: number;
  page: number;
  page_size: number;
  items: LessonInstance[];
}

export type RiskSeverity = "low" | "medium" | "high";

export interface StudentLatestRisk {
  student_profile_id: number;
  severity: RiskSeverity;
  signal_type: string;
  detected_at: string;
  current_value: number;
  threshold_value: number;
  associated_case_id: number | null;
  signal_data_json: Record<string, unknown>;
}

export interface InterventionRiskSummary {
  tenant_id: number;
  open_cases_total: number;
  signals_last_24h: number;
  auto_created_cases_last_24h: number;
  severity_breakdown: Record<string, number>;
}

export interface StudentRiskHistoryResponse {
  student_profile_id: number;
  total: number;
  page: number;
  page_size: number;
  items: StudentLatestRisk[];
}

export interface AttendanceTrendDataPoint {
  date: string;
  attendance_rate: number;
}

export interface AttendanceTrend {
  section_id: number;
  total_students: number;
  total_lessons: number;
  data_points: AttendanceTrendDataPoint[];
}
