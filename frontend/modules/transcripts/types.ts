export interface TranscriptEntry {
  course_name: string;
  section_code: string;
  credits: number;
  grade_value: string | null;
  numeric_value: number | null;
  semester: string;
  completed: boolean;
}

export interface Transcript {
  student_id: string;
  student_name: string;
  student_number: string;
  program: string | null;
  gpa: number | null;
  total_credits: number;
  entries: TranscriptEntry[];
  generated_at: string;
}

export interface TranscriptSnapshot {
  id: number;
  tenant_id: number;
  student_profile_id: number;
  snapshot_json: Record<string, unknown>;
  generated_by: string;
  generated_at: string;
}
