export interface Grade {
  id: string;
  enrollment_id: string;
  student_id: string;
  student_name: string;
  section_id: string;
  section_code: string;
  course_name: string;
  grade_value: string | null;
  numeric_value: number | null;
  graded_at: string | null;
  tenant_id: string;
}

export interface UpsertGradePayload {
  enrollment_id: string;
  grade_value: string;
  numeric_value?: number;
}
