export interface TranscriptItem {
  enrollment_id: number;
  term_id: number;
  term_code: string | null;
  term_name: string | null;
  course_id: number;
  course_code: string | null;
  course_title: string | null;
  credits: number;
  grade_code: string | null;
  grade_points: number | string | null;
}

export interface Transcript {
  student_profile_id: number;
  total_credits: number;
  gpa: number | string | null;
  items: TranscriptItem[];
}

export interface TranscriptSnapshot {
  id: number;
  tenant_id: number;
  student_profile_id: number;
  snapshot_json: Record<string, unknown>;
  generated_by: string;
  generated_at: string;
}

export interface TranscriptSnapshotMutationResponse {
  snapshot: TranscriptSnapshot;
  idempotent_replay: boolean;
}
