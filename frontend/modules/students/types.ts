export interface Student {
  id: string;
  student_number: string;
  first_name: string;
  last_name: string;
  email: string;
  status: StudentStatus;
  current_status?: StudentStatus;
  tenant_id: string;
  program: string | null;
  enrollment_year: number | null;
  version?: number;
  created_at: string;
  updated_at: string;
}

export type StudentStatus =
  | "admitted"
  | "active"
  | "inactive"
  | "leave_of_absence"
  | "suspended"
  | "graduated"
  | "withdrawn";

export interface CreateStudentPayload {
  // Current backend schema requires profile fields.
  person_id?: number;
  student_number: string;
  cohort_year?: number;
  admission_source?: "admissions_workflow" | "migration" | "manual";
  metadata_json?: Record<string, unknown>;

  // Legacy fields are kept optional for compatibility with existing callers.
  first_name?: string;
  last_name?: string;
  email?: string;
  tenant_id?: string;
  program?: string;
  enrollment_year?: number;
}

export interface UpdateStudentPayload {
  first_name?: string;
  last_name?: string;
  email?: string;
  status?: StudentStatus;
  program?: string;
}

export interface ChangeStudentStatusPayload {
  expected_version: number;
  to_status: StudentStatus;
  reason?: string;
  metadata_json?: Record<string, unknown>;
}

export interface StudentProfileMutationResponse {
  student: Student;
  idempotent_replay: boolean;
}

export interface StudentProgramBinding {
  id: number;
  tenant_id: number;
  student_profile_id: number;
  program_id: number;
  is_primary: boolean;
  binding_state: "active" | "inactive";
  started_at: string;
  ended_at: string | null;
  metadata_json: Record<string, unknown>;
  version: number;
  created_by: string;
  updated_by: string;
  created_at: string;
  updated_at: string;
}

export interface BindStudentProgramPayload {
  program_id: number;
  is_primary?: boolean;
  binding_state?: "active" | "inactive";
  started_at?: string | null;
  metadata_json?: Record<string, unknown>;
}

export interface StudentProgramBindingMutationResponse {
  binding: StudentProgramBinding;
  idempotent_replay: boolean;
}
