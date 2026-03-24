export interface Student {
  id: string;
  student_number: string;
  first_name: string;
  last_name: string;
  email: string;
  status: "active" | "inactive" | "graduated" | "suspended";
  tenant_id: string;
  program: string | null;
  enrollment_year: number | null;
  created_at: string;
  updated_at: string;
}

export interface CreateStudentPayload {
  student_number: string;
  first_name: string;
  last_name: string;
  email: string;
  tenant_id: string;
  program?: string;
  enrollment_year?: number;
}

export interface UpdateStudentPayload {
  first_name?: string;
  last_name?: string;
  email?: string;
  status?: Student["status"];
  program?: string;
}
