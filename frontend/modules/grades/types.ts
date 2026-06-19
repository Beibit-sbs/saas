export interface Grade {
  id: string | number;
  enrollment_id: string | number;
  tenant_id: string | number;
  grade_code?: string | null;
  grade_points?: number | string | null;
  grading_scale_id?: string | number;
  submitted_by?: string;
  submitted_at?: string | null;
  version?: number;
  metadata_json?: Record<string, unknown>;

  // Legacy display fields are kept while the page moves to the canonical
  // enrollment-backed grade lifecycle contract.
  student_id?: string;
  student_name?: string;
  section_id?: string;
  section_code?: string;
  course_name?: string;
  grade_value?: string | null;
  numeric_value?: number | null;
  graded_at?: string | null;
}

export interface UpsertGradePayload {
  enrollment_id: string | number;
  grading_scale_id: string | number;
  grade_value?: string;
  grade_code?: string;
  numeric_value?: number;
  grade_points?: number;
  expected_version?: number;
  reason?: string;
}

export interface GradeMutationResponse {
  grade: Grade;
  idempotent_replay: boolean;
}

export interface GradingScaleItem {
  id: string | number;
  tenant_id: string | number;
  scale_id: string | number;
  grade_code: string;
  grade_points: number | string;
  min_percentage: number | string;
  max_percentage: number | string;
}

export interface GradingScale {
  id: string | number;
  tenant_id: string | number;
  name: string;
  description: string | null;
  is_active: boolean;
  items: GradingScaleItem[];
}

export interface CreateGradingScaleItemPayload {
  grade_code: string;
  grade_points: number;
  min_percentage: number;
  max_percentage: number;
}

export interface CreateGradingScalePayload {
  name: string;
  description?: string | null;
  is_active?: boolean;
  items: CreateGradingScaleItemPayload[];
}
