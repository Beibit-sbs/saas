export interface Enrollment {
  id: string | number;
  student_id?: string;
  student_name?: string;
  student_profile_id?: number;
  section_id?: string | number | null;
  section_code?: string;
  course_id?: number;
  course_name?: string;
  term_id?: number;
  status?: "enrolled" | "dropped" | "completed" | "waitlisted";
  enrollment_status?: "enrolled" | "dropped" | "completed" | "waitlisted";
  enrolled_at: string;
  version?: number;
  tenant_id: string | number;
}

export interface CreateEnrollmentPayload {
  student_profile_id: number;
  course_id: number;
  term_id: number;
  section_id: number;
}

export interface DropEnrollmentPayload {
  expected_version: number;
  reason?: string;
  dropped_at?: string;
  metadata_json?: Record<string, unknown>;
}
