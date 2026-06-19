export interface AcademicTerm {
  id: number;
  tenant_id: number;
  term_code: string;
  term_name: string;
  start_date: string | null;
  end_date: string | null;
  add_drop_deadline?: string | null;
  status: "active" | "inactive" | "archived";
  metadata_json: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export interface AcademicTermsResponse {
  total: number;
  page: number;
  page_size: number;
  items: AcademicTerm[];
}

export interface CreateAcademicTermPayload {
  term_code: string;
  term_name: string;
  start_date?: string | null;
  end_date?: string | null;
  add_drop_deadline?: string | null;
  status?: AcademicTerm["status"];
  metadata_json?: Record<string, unknown>;
}
