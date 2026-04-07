export interface Enrollment {
  id: string;
  student_id: string;
  student_name: string;
  section_id: string;
  section_code: string;
  course_name: string;
  status: "enrolled" | "dropped" | "completed" | "waitlisted";
  enrolled_at: string;
  tenant_id: string;
}

export interface CreateEnrollmentPayload {
  student_id: string;
  section_id: string;
}
